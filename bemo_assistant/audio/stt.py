import os
import tempfile
import subprocess
import numpy as np


class STTManager:
    def __init__(
        self,
        engine="faster-whisper",
        model_name="small.en",
        compute_type="int8",
        device="cpu",
        whisper_cpp_path="",
        whisper_cpp_model="",
    ):
        self.engine = engine
        self.model_name = model_name
        self.compute_type = compute_type
        self.device = device
        self.whisper_cpp_path = whisper_cpp_path
        self.whisper_cpp_model = whisper_cpp_model
        self._fw_models = {}

    def update_engine(
        self,
        engine,
        model_name,
        compute_type,
        device,
        whisper_cpp_path,
        whisper_cpp_model,
    ):
        self.engine = engine
        self.model_name = model_name
        self.compute_type = compute_type
        self.device = device
        self.whisper_cpp_path = whisper_cpp_path
        self.whisper_cpp_model = whisper_cpp_model

    def _get_faster_whisper(self, model_name):
        if model_name in self._fw_models:
            return self._fw_models[model_name]
        from faster_whisper import WhisperModel

        model = WhisperModel(model_name, device=self.device, compute_type=self.compute_type)
        self._fw_models[model_name] = model
        return model

    def transcribe(self, audio: np.ndarray, sample_rate: int, model_override=None, language="en"):
        if audio is None or len(audio) == 0:
            return ""
        if self.engine == "whisper.cpp":
            return self._transcribe_whisper_cpp(audio, sample_rate, language)
        return self._transcribe_faster_whisper(audio, sample_rate, model_override, language)

    def _transcribe_faster_whisper(self, audio, sample_rate, model_override, language):
        audio = audio.astype(np.float32) / 32768.0
        model_name = model_override or self.model_name
        model = self._get_faster_whisper(model_name)
        segments, _info = model.transcribe(audio, language=language, beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments if seg.text)
        return text.strip()

    def _transcribe_whisper_cpp(self, audio, sample_rate, language):
        exe = self.whisper_cpp_path or os.environ.get("WHISPER_CPP_PATH", "")
        model_path = self.whisper_cpp_model
        if not exe or not model_path:
            raise RuntimeError("whisper.cpp path/model not configured")

        audio = audio.astype(np.int16)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        import wave

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

        cmd = [exe, "-m", model_path, "-f", wav_path, "-otxt", "-nt", "-l", language]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        txt_path = wav_path + ".txt"
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
        finally:
            for path in (wav_path, txt_path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        return text
