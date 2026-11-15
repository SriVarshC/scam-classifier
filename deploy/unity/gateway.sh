#!/usr/bin/env bash
# Start / check / stop the GPU job (scam_llm.sbatch). Called by the controller job (scam_ctl.sbatch)
# or by hand on a Unity login node:  bash gateway.sh start|status|stop
set -uo pipefail
BASE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
NAME=scam-llm
jobs_now() { squeue -h -u "$USER" -n "$NAME" -o "%i %T %M %L %N %r"; }
case "${1:-}" in
  start)
    running="$(jobs_now)"
    if [[ -n "$running" ]]; then echo "already queued/running: $running"; exit 0; fi
    cd "$BASE" && sbatch --parsable scam_llm.sbatch | sed 's/^/submitted job /' ;;
  status)
    running="$(jobs_now)"; echo "gpu job: ${running:-none}" ;;
  stop)
    scancel -u "$USER" -n "$NAME" && echo "cancelled" ;;
  *)
    echo "usage: gateway.sh start|status|stop" >&2; exit 2 ;;
esac
