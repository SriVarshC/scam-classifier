#!/usr/bin/env bash
# On-demand GPU copy of the service's LLM (same Ollama model) on the Unity cluster.
# Submitted by gateway.sh from the scam-llm folder (BASE = submit dir). It:
#   1. copies the model to the node's local disk (loading from /work directly takes ~150 s, local ~7 s)
#   2. starts Ollama on 127.0.0.1 (private to this job) and loads the model
#   3. opens a reverse SSH tunnel so the Azure VM sees it at 127.0.0.1:${REMOTE_PORT} (tunnel up == ready)
#   4. exits after IDLE_MIN minutes without LLM requests; near the time limit, if still busy, submits its successor
#SBATCH --job-name=scam-llm
#SBATCH --partition=gpu
#SBATCH --qos=short
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
set -uo pipefail
BASE="${SLURM_SUBMIT_DIR:?submit from the scam-llm folder}"
CONF="$HOME/.scam-llm"
source "$CONF/env"                       # AZURE_HOST (tunnel target), optional overrides
REMOTE_PORT="${REMOTE_PORT:-11435}"
IDLE_MIN="${IDLE_MIN:-30}"
RENEW_MIN="${RENEW_MIN:-15}"
MODEL="${MODEL:-qwen2.5:7b}"
PORT=$((20000 + SLURM_JOB_ID % 20000))
LOCAL="${TMPDIR:-/tmp}/scam-llm-$SLURM_JOB_ID"
log() { echo "$(date +%T) $*"; }

cleanup() {
  [[ -n "${TUN_PID:-}" ]] && { pkill -P "$TUN_PID" 2>/dev/null; kill "$TUN_PID" 2>/dev/null; }
  [[ -n "${OLL_PID:-}" ]] && kill "$OLL_PID" 2>/dev/null
  rm -rf "$LOCAL"
}
trap cleanup EXIT

log "node=$(hostname) gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1)"
mkdir -p "$LOCAL" && chmod 700 "$LOCAL"
cp -r "$BASE/models" "$LOCAL/models"
log "model copied to local disk"

export OLLAMA_MODELS="$LOCAL/models" OLLAMA_HOST="127.0.0.1:$PORT" OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=1
"$BASE/ollama/bin/ollama" serve > "$LOCAL/serve.log" 2>&1 &
OLL_PID=$!
for _ in $(seq 120); do curl -s "127.0.0.1:$PORT/api/version" >/dev/null && break; sleep 1; done
curl -s "127.0.0.1:$PORT/api/generate" \
  -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":-1,\"options\":{\"num_predict\":1}}" >/dev/null \
  || { log "model failed to load"; tail -20 "$LOCAL/serve.log"; exit 1; }
log "model loaded on GPU"

# Reverse tunnel, reconnecting if it drops. A successor job retries until the old job's port is free.
(
  while true; do
    ssh -N -i "$CONF/tunnel_key" -o BatchMode=yes -o IdentitiesOnly=yes \
        -o UserKnownHostsFile="$CONF/known_hosts" -o StrictHostKeyChecking=yes \
        -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
        -R "127.0.0.1:$REMOTE_PORT:127.0.0.1:$PORT" "gputunnel@$AZURE_HOST"
    sleep 10
  done
) &
TUN_PID=$!
log "tunnel loop started -> $AZURE_HOST:127.0.0.1:$REMOTE_PORT"

left_s() {  # seconds left before the Slurm time limit (squeue %L: [D-]HH:MM:SS, MM:SS)
  local t d=0 h=0 m=0 s=0
  t=$(squeue -h -j "$SLURM_JOB_ID" -o %L)
  [[ "$t" == *-* ]] && { d=${t%%-*}; t=${t#*-}; }
  IFS=: read -r a b c <<< "$t"
  if [[ -n "$c" ]]; then h=$a; m=$b; s=$c; elif [[ -n "$b" ]]; then m=$a; s=$b; else s=$a; fi
  echo $(( 10#$d*86400 + 10#$h*3600 + 10#$m*60 + 10#$s ))
}

count=-1; last=$(date +%s); renewed=0
while sleep 30; do
  n=$(grep -c -E 'POST +"/api/(generate|chat)"' "$LOCAL/serve.log")
  now=$(date +%s)
  [[ "$n" != "$count" ]] && { count=$n; last=$now; }
  idle=$(( (now - last) / 60 ))
  if (( idle >= IDLE_MIN )); then log "idle for ${idle} min - stopping"; break; fi
  if (( renewed == 0 )) && (( $(left_s) < RENEW_MIN * 60 )); then
    (cd "$BASE" && sbatch --parsable scam_llm.sbatch) && log "near time limit and busy - successor submitted"
    renewed=1
  fi
  kill -0 "$OLL_PID" 2>/dev/null || { log "ollama exited"; tail -20 "$LOCAL/serve.log"; break; }
done
log "requests served: $count"
