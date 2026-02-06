import time
import wave
import numpy as np
import sounddevice as sd


class AudioPlayer:
    def __init__(self):
        self._stream = None

    def stop(self):
        if self._stream:
            try:
                self._stream.abort(ignore_errors=True)
            except Exception:
                pass

    def play_wav(self, path, device=None, on_amplitude=None, stop_event=None):
        with wave.open(path, "rb") as wf:
            channels = wf.getnchannels()
            samplerate = wf.getframerate()
            frames = wf.getnframes()
            audio = wf.readframes(frames)
        data = np.frombuffer(audio, dtype=np.int16)
        if channels > 1:
            data = data.reshape(-1, channels)
        else:
            data = data.reshape(-1, 1)
        # Convert to float32 for smoother playback and better device compatibility
        data = data.astype(np.float32) / 32768.0

        # Use a slightly larger blocksize and higher latency to reduce glitches
        blocksize = int(samplerate * 0.02)
        blocksize = max(256, min(4096, blocksize))

        idx = 0

        def callback(outdata, frame_count, time_info, status):
            nonlocal idx
            if stop_event and stop_event.is_set():
                raise sd.CallbackStop()
            chunk = data[idx : idx + frame_count]
            if len(chunk) < frame_count:
                outdata[: len(chunk)] = chunk
                outdata[len(chunk) :] = 0
                raise sd.CallbackStop()
            outdata[:] = chunk
            idx += frame_count
            if on_amplitude:
                rms = float(np.sqrt(np.mean(chunk * chunk)))
                on_amplitude(float(rms))

        self._stream = sd.OutputStream(
            samplerate=samplerate,
            channels=channels,
            dtype="float32",
            blocksize=blocksize,
            latency="high",
            callback=callback,
            device=device if device else None,
        )

        with self._stream:
            while self._stream.active:
                if stop_event and stop_event.is_set():
                    break
                time.sleep(0.01)
        self._stream = None
