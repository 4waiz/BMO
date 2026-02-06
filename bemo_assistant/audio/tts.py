import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import sys


class PiperTTS:
    def __init__(self, voice: str, speaker_id: str = "", piper_path: str = ""):
        self.voice = voice
        self.speaker_id = speaker_id
        self.piper_path = piper_path

    @property
    def is_available(self) -> bool:
        return bool(self._resolve_piper()) and bool(self._resolve_voice_path())

    def status(self):
        exe = self._resolve_piper()
        voice = self._resolve_voice_path()
        if not exe:
            return False, "Piper executable not found."
        if not voice:
            return False, "Piper voice model not found."
        return True, "Piper ready."

    def update_voice(self, voice: str, speaker_id: str = "", piper_path: str = ""):
        self.voice = voice
        self.speaker_id = speaker_id
        self.piper_path = piper_path

    def _resolve_piper(self):
        if self.piper_path and Path(self.piper_path).exists():
            return self.piper_path

        # Look for piper.exe next to the current Python executable (venv Scripts)
        try:
            py_dir = Path(sys.executable).parent
            candidate = py_dir / "piper.exe"
            if candidate.exists():
                return str(candidate)
        except Exception:
            pass

        return shutil.which("piper")

    def _resolve_voice_path(self):
        if not self.voice:
            return ""
        voice_path = Path(self.voice)
        if voice_path.exists():
            return str(voice_path)
        return ""

    def synthesize(self, text: str) -> str:
        exe = self._resolve_piper()
        if not exe:
            raise RuntimeError("Piper not found in PATH or configured path")
        voice_path = self._resolve_voice_path()
        if not voice_path:
            raise RuntimeError("Piper voice model not found. Set a valid .onnx path in Settings.")

        out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out_path = out_file.name
        out_file.close()

        cmd = [exe, "--model", voice_path, "--output_file", out_path]
        if self.speaker_id:
            cmd += ["--speaker", str(self.speaker_id)]

        subprocess.run(cmd, input=text.encode("utf-8"), check=True)
        return out_path
