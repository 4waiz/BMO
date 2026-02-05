#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Warning: ffmpeg not found. Audio utilities may fail."
  echo "Install hints:"
  echo "  Debian/Ubuntu: sudo apt install -y ffmpeg"
  echo "  Raspberry Pi OS: sudo apt install -y ffmpeg"
  echo "  macOS (Homebrew): brew install ffmpeg"
fi

OLLAMA_URL="http://localhost:11434/api/tags"
if ! curl -s --max-time 2 "$OLLAMA_URL" >/dev/null; then
  if command -v ollama >/dev/null 2>&1; then
    echo "Starting ollama serve..."
    nohup ollama serve >"$ROOT_DIR/.ollama.log" 2>&1 &
    sleep 2
  else
    echo "Warning: Ollama not found. Install from https://ollama.com"
  fi
fi

if curl -s --max-time 3 "$OLLAMA_URL" >/dev/null; then
  if ! curl -s "$OLLAMA_URL" | grep -q 'tinyllama:chat'; then
    echo "Pulling tinyllama:chat model..."
    ollama pull tinyllama:chat || true
  fi
else
  echo "Warning: Ollama server not reachable. Start with: ollama serve"
fi

if [ ! -d "models/whisper" ] || [ -z "$(ls -A models/whisper 2>/dev/null)" ]; then
  echo "Downloading faster-whisper model (small.en)..."
  python scripts/download_whisper_model.py --model small.en --output models/whisper || true
fi

python app.py
