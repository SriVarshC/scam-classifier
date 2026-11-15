# On-demand GPU for the scam service (Unity cluster)

The Azure VM keeps the public HTTPS service and its CPU model. A GPU copy of the **same model**
(qwen2.5:7b, same prompts and scoring) runs on the Unity cluster only while it is being used.

```
transcription API ──HTTPS──> Azure VM: Caddy -> scam-service (rules, classifier, scoring)
                                │  GPU tunnel up?  yes -> 127.0.0.1:11435 (Unity GPU, ~5 s per call)
                                │                  no  -> local CPU Ollama (~40 s) + request "start"
                                │
   /var/lib/scam-gpu/request <──┘        (start|stop, written by the service)
            ▲  ssh "wait" (forced command scam-gpu-ctl, user gputunnel)
   Unity controller job (scam_ctl.sbatch, 1 CPU, 5 days, renews itself)
            │ sbatch
   Unity GPU job (scam_llm.sbatch): copy model to local disk -> Ollama on 127.0.0.1
            -> reverse tunnel to the VM (gputunnel, may only listen on 127.0.0.1:11435)
            -> stops itself after 30 min without requests; submits a successor near its 4 h limit if busy
```

Azure never holds a key to the Unity account (Unity only accepts keys added in its portal, and those
cannot be restricted). Both Unity keys are locked down on the VM:
`tunnel_key` = remote-forward 127.0.0.1:11435 only, no commands; `ctl_key` = forced command `scam-gpu-ctl wait` only.

## Measured (2026-11-14)
| Step | Time |
|---|---|
| Start request -> controller picks it up | < 1 s |
| Slurm queue (`gpu`, `--qos=short`, any GPU) | 2–4 s |
| Copy model /work -> node disk | ~60 s |
| Start Ollama + load model on GPU (Tesla M40) | ~35 s |
| **Cold start total** (`POST /v1/gpu/start` -> ready) | **~101 s** |
| `/v1/classify` on GPU | 4.5–12 s (CPU: ~40 s) |

## Use
- Warm up before a demo: `POST /v1/gpu/start` (Bearer token), then `GET /v1/gpu/status` until `"ready": true`.
- Any `/v1/classify` while the GPU is down also requests a start (at most once per 120 s) and is answered on CPU.
- Stop now: `POST /v1/gpu/stop` (otherwise it stops itself after 30 idle minutes).
- Responses include `"llm_backend": "gpu" | "cpu"`.

## Files
| Where | File |
|---|---|
| Unity `/work/<pi-group>/<user>/scam-llm/` | `scam_llm.sbatch`, `scam_ctl.sbatch`, `gateway.sh`, `ollama/` (0.40.16), `models/` (qwen2.5:7b, fetched over IPv4 with `fetch_model_ipv4.sh`), `logs/` |
| Unity `~/.scam-llm/` (700) | `env` (`AZURE_HOST=...`), `tunnel_key`, `ctl_key`, `known_hosts` (VM host key, fingerprint checked) |
| VM | user `gputunnel` (`~/.ssh/authorized_keys` with the two restricted keys), `/usr/local/bin/scam-gpu-ctl`, `/var/lib/scam-gpu/` (root:scamgpu 2770), NSG rule `allow-ssh-unity` (22 from Unity's egress IP), unit env `SCAM_GPU_OLLAMA_URL`, `SCAM_GPU_TIMEOUT_SECONDS` |

## Operate (from a Unity login node, in the scam-llm folder)
- Controller running? `squeue -u $USER -n scam-ctl` — if not: `sbatch scam_ctl.sbatch`
  (after cluster maintenance or if it was cancelled; without it the service just stays on CPU).
- By hand: `bash gateway.sh start|status|stop`. Logs: `logs/scam-ctl-<id>.out`, `logs/scam-llm-<id>.out`.
- Turn the GPU path off completely: remove the two `SCAM_GPU_*` lines from the unit, `systemctl daemon-reload`,
  restart `scam-service`, `scancel -n scam-ctl`.

Notes: Unity nodes have no IPv6 route (Ollama's own `pull` fails; use `fetch_model_ipv4.sh`).
Loading the model straight from /work takes ~150 s, hence the copy to node-local disk.
