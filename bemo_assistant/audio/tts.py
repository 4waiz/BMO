import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class PiperTTS:
    def __init__(self, voice: str, speaker_id: str = "", piper_path: str = ""):
        self.voice = voice
        self.speaker_id = speaker_id
        self.piper_path = piper_path

    @property
    def is_available(self) -> bool:
        return bool(self._resolve_piper()) and bool(self.voice)

    def update_voice(self, voice: str, speaker_id: str = "", piper_path: str = ""):
        self.voice = voice
        self.speaker_id = speaker_id
        self.piper_path = piper_path

    def _resolve_piper(self):
        if self.piper_path and Path(self.piper_path).exists():
            return self.piper_path
        return shutil.which("piper")

    def synthesize(self, text: str) -> str:
        exe = self._resolve_piper()
        if not exe:
            raise RuntimeError("Piper not found in PATH or configured path")
        if not self.voice:
            raise RuntimeError("Piper voice model is not configured")

        out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out_path = out_file.name
        out_file.close()

        cmd = [exe, "--model", self.voice, "--output_file", out_path]
        if self.speaker_id:
            cmd += ["--speaker", str(self.speaker_id)]

        subprocess.run(cmd, input=text.encode("utf-8"), check=True)
        return out_path
