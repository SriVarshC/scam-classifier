#!/usr/bin/env bash
# One-time setup on the Azure VM (Ubuntu 24.04). Run from the repository root:
#   bash deploy/azure/setup.sh <your-dns-name>.<region>.cloudapp.azure.com
# Installs Docker, creates deploy/azure/.env (with a fresh service token), downloads qwen2.5:7b,
# builds and starts Ollama + the scam service + Caddy (HTTPS), then runs a smoke test.
set -euo pipefail

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
  echo "usage: bash deploy/azure/setup.sh <dns-label>.<region>.cloudapp.azure.com" >&2
  exit 1
fi
cd "$(dirname "$0")"   # deploy/azure

echo "== 1/5 Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
  sudo usermod -aG docker "$USER"
fi
sudo systemctl enable --now docker
DOCKER="sudo docker"

echo "== 2/5 .env"
if [[ ! -f .env ]]; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  sed -e "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" -e "s|^SCAM_SERVICE_TOKEN=.*|SCAM_SERVICE_TOKEN=${TOKEN}|" \
      -e "s|^CALL_LLM_NUM_THREAD=.*|CALL_LLM_NUM_THREAD=$(nproc)|" .env.example > .env
  chmod 600 .env
  echo "created deploy/azure/.env (token stored there; show it with: grep TOKEN deploy/azure/.env)"
else
  echo ".env already exists - keeping it"
fi

echo "== 3/5 Ollama + qwen2.5:7b (about 4.7 GB download)"
$DOCKER compose --env-file .env up -d ollama
MODEL="$(grep -E '^CALL_LLM_MODEL=' .env | cut -d= -f2)"
$DOCKER compose --env-file .env exec -T ollama ollama pull "${MODEL:-qwen2.5:7b}"

echo "== 4/5 Build and start the service + HTTPS (first build takes ~5-10 min)"
$DOCKER compose --env-file .env up -d --build

echo "== 5/5 Waiting for the service (loads the classifier and warms up the LLM)..."
for i in $(seq 1 120); do
  if curl -fsS "https://${DOMAIN}/healthz" >/dev/null 2>&1; then echo "service is up at https://${DOMAIN}"; break; fi
  sleep 10
done
python3 smoke_test.py "https://${DOMAIN}" "$(grep -E '^SCAM_SERVICE_TOKEN=' .env | cut -d= -f2)"
