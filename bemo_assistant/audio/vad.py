import time
import collections
import numpy as np
import sounddevice as sd

try:
    import webrtcvad
    _HAS_WEBRTCVAD = True
except Exception:
    webrtcvad = None
    _HAS_WEBRTCVAD = False


class VADRecorder:
    def __init__(self, sample_rate=16000, aggressiveness=2, device=""):
        self.sample_rate = sample_rate
        self.frame_ms = 30
        self.frame_samples = int(self.sample_rate * self.frame_ms / 1000)
        self.device = device if device else None
        self.vad = webrtcvad.Vad(aggressiveness) if _HAS_WEBRTCVAD else None
        self.energy_threshold = 500

    def is_speech(self, frame: np.ndarray) -> bool:
        if self.vad:
            return self.vad.is_speech(frame.tobytes(), self.sample_rate)
        rms = np.sqrt(np.mean(frame.astype(np.float32) ** 2))
        return rms > self.energy_threshold

    def record(
        self,
        stop_event=None,
        max_record_ms=12000,
        min_record_ms=300,
        silence_ms=800,
    ):
        ring_buffer = collections.deque(maxlen=int(300 / self.frame_ms))
        voiced_frames = []
        triggered = False
        silence_duration = 0

        q = collections.deque()

        def callback(indata, frames, time_info, status):
            q.append(indata.copy())

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.frame_samples,
            callback=callback,
            device=self.device,
        )

        start_time = time.time()
        with stream:
            while True:
                if stop_event and stop_event.is_set():
                    return np.array([], dtype=np.int16)
                if q:
                    frame = q.popleft().reshape(-1)
                else:
                    time.sleep(0.01)
                    continue

                speech = self.is_speech(frame)
                if not triggered:
                    ring_buffer.append(frame)
                    if speech:
                        triggered = True
                        voiced_frames.extend(ring_buffer)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    if not speech:
                        silence_duration += self.frame_ms
                    else:
                        silence_duration = 0

                    total_ms = len(voiced_frames) * self.frame_ms
                    if total_ms >= min_record_ms and silence_duration >= silence_ms:
                        break

                if (time.time() - start_time) * 1000 > max_record_ms:
                    break

        if not voiced_frames:
            return np.array([], dtype=np.int16)
        return np.concatenate(voiced_frames)
