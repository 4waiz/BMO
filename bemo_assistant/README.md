# Bemo Assistant (Offline, Ollama, PySide6)

A fully local, Bemo-inspired voice assistant with a friendly UI, local STT, local TTS, and Ollama for responses. No cloud APIs.

Default model: `tinyllama:chat` (fast + responsive).

## One-Command Run

### Linux / Raspberry Pi / macOS

```bash
cd bemo_assistant
chmod +x scripts/bootstrap_and_run.sh
./scripts/bootstrap_and_run.sh
```

### Windows (PowerShell)

```powershell
cd bemo_assistant
scripts\bootstrap_and_run.ps1
```

If PowerShell blocks the script, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

The scripts will:
- Create `.venv` if missing
- Install pip deps
- Warn if `ffmpeg` is missing
- Start Ollama if possible
- Pull `tinyllama:chat` if missing
- Download a default faster-whisper model if missing
- Run the app

## Requirements

- Python 3.10+ (3.11 recommended)
- Ollama installed
- Microphone + speaker
- `ffmpeg` recommended
- Linux: `portaudio` dev packages (`portaudio19-dev`) may be required
- Piper TTS installed (use `scripts/install_piper.sh` on Pi/Linux, or install manually on desktop and set paths in Settings)

## Settings Panel

- **Verify Ollama**: health check + model list refresh
- **STT Test**: records 3 seconds and shows transcript
- **Wake word mode**: `simple` (default) or `openwakeword`
- **STT engine**: `faster-whisper` (default) or `whisper.cpp`
- **TTS**: set Piper executable path + voice `.onnx`
- **Kiosk mode**: fullscreen for Pi touchscreens

## Voice Commands

- Wake word: **"Hey Bemo"**
- Start a game: "start trivia", "start tic tac toe", "start rock paper scissors"
- Interrupt speaking: "stop"

## Optional Dependencies

- openWakeWord (advanced wake word):
  ```bash
  pip install openwakeword
  ```
- Camera vision via OpenCV:
  ```bash
  pip install opencv-python
  ```

## Troubleshooting

- **Ollama not reachable**: run `ollama serve`
- **No audio I/O**: check PortAudio and device selection in Settings
- **TTS missing**: install Piper and set path/voice in Settings
- **Piper error: ModuleNotFoundError: pathvalidate**: run `pip install pathvalidate` (or `pip install -r requirements.txt`)
- **Windows webrtcvad build error**: install Microsoft C++ Build Tools or rerun the bootstrap script (it will continue without webrtcvad and use an energy-based VAD fallback)
- **Windows Piper voice missing**: run `scripts\bootstrap_and_run.ps1` again or download `en_US-lessac-medium.onnx` into `models\piper` (use the Hugging Face URL in scripts) and set the path in Settings

---
Bemo-inspired only. Not an official or copyrighted character.
