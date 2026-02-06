#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/tools/piper"
MODELS_DIR="$ROOT_DIR/models/piper"
PIPER_VERSION="1.2.0"

mkdir -p "$TOOLS_DIR" "$MODELS_DIR"

ARCH="$(uname -m)"
if [ "$ARCH" = "aarch64" ]; then
  FILE="piper_linux_aarch64.tar.gz"
elif [ "$ARCH" = "x86_64" ]; then
  FILE="piper_linux_x86_64.tar.gz"
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi

URL="https://github.com/rhasspy/piper/releases/download/v${PIPER_VERSION}/${FILE}"
VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
VOICE_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"

cd "$TOOLS_DIR"
if [ ! -f "piper" ]; then
  curl -L "$URL" -o piper.tgz
  tar -xzf piper.tgz
fi

cd "$MODELS_DIR"
if [ ! -f "en_US-lessac-medium.onnx" ]; then
  curl -L "$VOICE_URL" -o en_US-lessac-medium.onnx
fi
if [ ! -f "en_US-lessac-medium.onnx.json" ]; then
  curl -L "$VOICE_JSON_URL" -o en_US-lessac-medium.onnx.json
fi

echo "Piper installed. Set PIPER path in Settings if needed: $TOOLS_DIR/piper"
