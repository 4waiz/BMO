import threading
import time
import sounddevice as sd

from audio.vad import VADRecorder

try:
    from openwakeword.model import Model
    _HAS_OWW = True
except Exception:
    Model = None
    _HAS_OWW = False

WAKE_PHRASE = "hey bemo"


class WakeWordService:
    def __init__(self, mode, stt, settings, on_wake):
        self.mode = mode
        self.stt = stt
        self.settings = settings
        self.on_wake = on_wake
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None

    def update_settings(self, settings):
        self.settings = settings
        self.mode = settings.wakeword_mode

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def pause(self):
        self._pause_event.set()

    def resume(self):
        self._pause_event.clear()

    def _run(self):
        if self.mode == "openwakeword" and _HAS_OWW:
            self._run_openwakeword()
        else:
            self._run_simple()

    def _run_simple(self):
        recorder = VADRecorder(
            sample_rate=self.settings.sample_rate,
            aggressiveness=self.settings.vad_aggressiveness,
            device=self.settings.mic_device,
        )
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.1)
                continue
            audio = recorder.record(
                stop_event=self._stop_event,
                max_record_ms=2000,
                min_record_ms=200,
                silence_ms=300,
            )
            if self._stop_event.is_set():
                return
            if audio is None or len(audio) == 0:
                continue
            try:
                text = self.stt.transcribe(
                    audio,
                    self.settings.sample_rate,
                    model_override=self.settings.wakeword_model,
                    language=self.settings.language,
                )
            except Exception:
                continue
            if WAKE_PHRASE in text.lower():
                self.on_wake()
                time.sleep(1.0)

    def _run_openwakeword(self):
        model_path = self.settings.openwakeword_model_path
        if model_path:
            model = Model(wakeword_models=[model_path])
        else:
            model = Model()

        cooldown = 0

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.1)
                continue

            q = []

            def callback(indata, frames, time_info, status):
                q.append(indata.copy())

            stream = sd.InputStream(
                samplerate=self.settings.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=1600,
                callback=callback,
                device=self.settings.mic_device if self.settings.mic_device else None,
            )

            with stream:
                while not self._stop_event.is_set() and not self._pause_event.is_set():
                    if not q:
                        time.sleep(0.01)
                        continue
                    frame = q.pop(0).reshape(-1)
                    if len(frame) == 0:
                        continue
                    prediction = model.predict(frame)
                    score = 0
                    if isinstance(prediction, dict):
                        score = max(prediction.values())
                    if score > self.settings.wakeword_threshold and cooldown <= 0:
                        self.on_wake()
                        cooldown = 20
                    cooldown -= 1
                    time.sleep(0.01)


