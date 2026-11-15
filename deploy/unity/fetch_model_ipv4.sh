#!/usr/bin/env bash
# Fetch an Ollama model from registry.ollama.ai over IPv4 only (Unity nodes have no IPv6 route),
# verify every blob's sha256, and write the manifest where `ollama serve` (OLLAMA_MODELS) finds it.
set -euo pipefail
MODELS="$1"; NAME="${2:-qwen2.5}"; TAG="${3:-7b}"
REG=https://registry.ollama.ai/v2/library/$NAME
rm -f "$MODELS"/blobs/*-partial*
mkdir -p "$MODELS/blobs" "$MODELS/manifests/registry.ollama.ai/library/$NAME"
MAN="$(mktemp)"
curl -4 -fsSL -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "$REG/manifests/$TAG" -o "$MAN"
for d in $(python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); print(" ".join([m["config"]["digest"]]+[l["digest"] for l in m["layers"]]))' "$MAN"); do
  hex="${d#sha256:}"; out="$MODELS/blobs/sha256-$hex"
  if [[ -f "$out" ]] && echo "$hex  $out" | sha256sum -c --status; then echo "ok (cached) $hex"; continue; fi
  curl -4 -fsSL --retry 3 "$REG/blobs/$d" -o "$out.tmp"
  echo "$hex  $out.tmp" | sha256sum -c --status || { echo "CHECKSUM MISMATCH $hex" >&2; exit 1; }
  mv "$out.tmp" "$out"; echo "ok $hex ($(du -h "$out" | cut -f1))"
done
cp "$MAN" "$MODELS/manifests/registry.ollama.ai/library/$NAME/$TAG"; rm -f "$MAN"
echo "manifest written"
