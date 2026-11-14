#!/usr/bin/env bash
# Native install on the Azure VM (Ubuntu 24.04, x64 or ARM64). Ollama must already be installed with
# qwen2.5:7b pulled. Run on the VM from the repository root:
#   bash deploy/azure/native/install_native.sh <token-file> <public-ip>
# - creates .venv, installs CPU-only torch, then requirements.txt (pinned to the tested versions)
# - installs scam-service.service (token from <token-file>, which is then deleted) after ollama.service
# - installs Caddy with automatic HTTPS for https://<ip-with-dashes>.sslip.io
set -euo pipefail
TOKEN_FILE="$1"; PUBLIC_IP="$2"
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
HOST="${PUBLIC_IP//./-}.sslip.io"
cd "$REPO"

echo "== venv + CPU-only torch + requirements.txt"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -q -r requirements.txt -c deploy/azure/requirements-service.txt
.venv/bin/python -c "import torch, sentence_transformers, fastapi; print('torch', torch.__version__, '| cuda', torch.cuda.is_available())"
.venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" >/dev/null
echo "embedding model cached"

echo "== systemd unit (token not printed)"
TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"
[[ ${#TOKEN} -ge 16 ]] || { echo "token too short" >&2; exit 1; }
sed "s|__TOKEN__|${TOKEN}|" deploy/azure/native/scam-service.service.template | sudo tee /etc/systemd/system/scam-service.service >/dev/null
sudo chmod 600 /etc/systemd/system/scam-service.service
shred -u "$TOKEN_FILE" 2>/dev/null || rm -f "$TOKEN_FILE"
sudo systemctl daemon-reload
sudo systemctl enable --now scam-service

echo "== Caddy (automatic HTTPS for ${HOST})"
if ! command -v caddy >/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq caddy >/dev/null
fi
sed "s|__HOST__|${HOST}|" deploy/azure/native/Caddyfile.template | sudo tee /etc/caddy/Caddyfile >/dev/null
sudo systemctl enable caddy
sudo systemctl restart caddy
echo "done: https://${HOST}"
