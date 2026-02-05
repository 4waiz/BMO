import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AppSettings:
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "tinyllama:chat"
    ollama_temperature: float = 0.6

    system_prompt: str = ""

    wakeword_mode: str = "simple"  # simple | openwakeword
    wakeword_model: str = "tiny.en"
    wakeword_threshold: float = 0.6
    openwakeword_model_path: str = ""

    stt_engine: str = "faster-whisper"  # faster-whisper | whisper.cpp
    whisper_model: str = "small.en"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_cpp_path: str = ""
    whisper_cpp_model: str = ""

    tts_voice: str = "models/piper/en_US-lessac-medium.onnx"
    tts_speaker: str = ""
    piper_path: str = ""

    mic_device: str = ""
    speaker_device: str = ""
    sample_rate: int = 16000
    vad_aggressiveness: int = 2
    min_record_ms: int = 300
    max_record_ms: int = 12000
    silence_ms: int = 800

    history_max_messages: int = 12

    camera_enabled: bool = False
    kiosk_mode: bool = False
    language: str = "en"


class SettingsManager:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or self._default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "settings.json"

    def _default_data_dir(self) -> Path:
        return Path.home() / ".bemo_assistant"

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return self._from_dict(data)

    def save(self, settings: AppSettings):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2)

    def _from_dict(self, data: dict) -> AppSettings:
        settings = AppSettings()
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings
