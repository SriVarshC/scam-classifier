#!/usr/bin/env bash
# Controller for the on-demand GPU job: a tiny CPU job that lets the Azure VM start/stop the GPU job
# without Azure ever holding a key to this Unity account.
# Loop: send the current GPU-job status to the VM and wait (ssh ... wait, forced command scam-gpu-ctl on
# the VM, up to 5 min) for "start" / "stop" / "noop"; run it with gateway.sh. Renews itself before
# its time limit. Submit once from the scam-llm folder:  sbatch scam_ctl.sbatch
#SBATCH --job-name=scam-ctl
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=5-00:00:00
#SBATCH --output=logs/%x-%j.out
set -uo pipefail
BASE="${SLURM_SUBMIT_DIR:?submit from the scam-llm folder}"
CONF="$HOME/.scam-llm"
source "$CONF/env"                       # AZURE_HOST
RENEW_S="${CTL_RENEW_S:-3600}"
log() { echo "$(date +%T) $*"; }

left_s() {  # seconds left before the Slurm time limit (squeue %L: [D-]HH:MM:SS, MM:SS)
  local t d=0 h=0 m=0 s=0
  t=$(squeue -h -j "$SLURM_JOB_ID" -o %L)
  [[ "$t" == *-* ]] && { d=${t%%-*}; t=${t#*-}; }
  IFS=: read -r a b c <<< "$t"
  if [[ -n "$c" ]]; then h=$a; m=$b; s=$c; elif [[ -n "$b" ]]; then m=$a; s=$b; else s=$a; fi
  echo $(( 10#$d*86400 + 10#$h*3600 + 10#$m*60 + 10#$s ))
}

log "controller started on $(hostname)"
renewed=0; fails=0
while true; do
  report="controller=$SLURM_JOB_ID at $(date -u +%FT%TZ) | $(bash "$BASE/gateway.sh" status)"
  action=$(echo "$report" | ssh -i "$CONF/ctl_key" -o BatchMode=yes -o IdentitiesOnly=yes \
             -o UserKnownHostsFile="$CONF/known_hosts" -o StrictHostKeyChecking=yes \
             -o ConnectTimeout=15 -o ServerAliveInterval=30 "gputunnel@$AZURE_HOST" wait 2>>"$BASE/logs/ctl-ssh.err")
  if [[ $? -ne 0 ]]; then
    fails=$((fails + 1)); (( fails % 20 == 1 )) && log "cannot reach $AZURE_HOST (fail $fails)"; sleep 15
  else
    fails=0
    action="$(tail -n 1 <<< "$action")"   # earlier lines are "." heartbeats
    case "$action" in
      start|stop) log "$action -> $(bash "$BASE/gateway.sh" "$action")" ;;
    esac
  fi
  if (( renewed == 0 )) && (( $(left_s) < RENEW_S )); then
    (cd "$BASE" && sbatch --parsable scam_ctl.sbatch) && log "successor controller submitted"
    renewed=1
  fi
done
