import os
import sys
import time
import threading
import logging
import re
from pathlib import Path

import sounddevice as sd

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_theme
from storage.settings import SettingsManager, AppSettings
from storage.scoreboard import Scoreboard
from audio.vad import VADRecorder
from audio.stt import STTManager
from audio.wakeword import WakeWordService
from audio.tts import PiperTTS
from audio.playback import AudioPlayer
from llm.ollama_client import OllamaClient
from llm.prompts import DEFAULT_SYSTEM_PROMPT
from games.guess_number import GuessNumberGame
from games.rps import RPSGame
from games.trivia import TriviaGame
from games.tictactoe import TicTacToeGame

LOG = logging.getLogger("bemo")

STATE_IDLE = "Idle"
STATE_LISTENING = "Listening"
STATE_THINKING = "Thinking"
STATE_SPEAKING = "Speaking"


class ListenWorker(QThread):
    transcript = Signal(str)
    error = Signal(str)

    def __init__(self, settings: AppSettings, stt: STTManager):
        super().__init__()
        self.settings = settings
        self.stt = stt
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            recorder = VADRecorder(
                sample_rate=self.settings.sample_rate,
                aggressiveness=self.settings.vad_aggressiveness,
                device=self.settings.mic_device,
            )
            audio = recorder.record(
                stop_event=self._stop_event,
                max_record_ms=self.settings.max_record_ms,
                min_record_ms=self.settings.min_record_ms,
                silence_ms=self.settings.silence_ms,
            )
            if self._stop_event.is_set():
                return
            if audio is None or len(audio) == 0:
                self.transcript.emit("")
                return
            text = self.stt.transcribe(
                audio,
                self.settings.sample_rate,
                model_override=None,
                language=self.settings.language,
            )
            self.transcript.emit(text.strip())
        except Exception as exc:
            LOG.exception("ListenWorker error")
            self.error.emit(str(exc))


class LLMWorker(QThread):
    partial = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, client: OllamaClient, messages, model: str, temperature: float):
        super().__init__()
        self.client = client
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            buffer_text = ""
            for chunk in self.client.chat_stream(
                self.messages, model=self.model, temperature=self.temperature
            ):
                if self._stop_event.is_set():
                    return
                if not chunk:
                    continue
                buffer_text += chunk
                self.partial.emit(buffer_text)
            self.done.emit(buffer_text.strip())
        except Exception as exc:
            LOG.exception("LLMWorker error")
            self.error.emit(str(exc))


class SpeechWorker(QThread):
    amplitude = Signal(float)
    done = Signal()
    error = Signal(str)

    def __init__(self, text: str, settings: AppSettings, tts: PiperTTS, player: AudioPlayer):
        super().__init__()
        self.text = text
        self.settings = settings
        self.tts = tts
        self.player = player
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            wav_path = self.tts.synthesize(self.text)
            try:
                def on_amp(level: float):
                    self.amplitude.emit(level)

                self.player.play_wav(
                    wav_path,
                    device=self.settings.speaker_device,
                    on_amplitude=on_amp,
                    stop_event=self._stop_event,
                )
            finally:
                try:
                    os.remove(wav_path)
                except OSError:
                    pass
            self.done.emit()
        except Exception as exc:
            LOG.exception("SpeechWorker error")
            self.error.emit(str(exc))


class StopListener(threading.Thread):
    def __init__(self, settings: AppSettings, stt: STTManager, on_stop):
        super().__init__(daemon=True)
        self.settings = settings
        self.stt = stt
        self.on_stop = on_stop
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        recorder = VADRecorder(
            sample_rate=self.settings.sample_rate,
            aggressiveness=self.settings.vad_aggressiveness,
            device=self.settings.mic_device,
        )
        while not self._stop_event.is_set():
            audio = recorder.record(
                stop_event=self._stop_event,
                max_record_ms=1200,
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
            if "stop" in text.lower():
                self.on_stop()
                return


class GameManager:
    def __init__(self, scoreboard: Scoreboard):
        self.scoreboard = scoreboard
        self.games = {
            "guess": GuessNumberGame(),
            "rps": RPSGame(),
            "trivia": TriviaGame(),
            "tictactoe": TicTacToeGame(),
        }
        self.active_key = None

    def active(self):
        return self.active_key is not None

    def current(self):
        if self.active_key is None:
            return None
        return self.games[self.active_key]

    def start(self, key: str):
        if key not in self.games:
            return None
        self.active_key = key
        game = self.games[key]
        update = game.start()
        return update

    def stop(self):
        self.active_key = None

    def maybe_start_from_text(self, text: str):
        t = text.lower()
        if "guess" in t and "number" in t:
            return "guess"
        if "rock" in t and "paper" in t:
            return "rps"
        if "trivia" in t or "quiz" in t:
            return "trivia"
        if "tic tac toe" in t or "tictactoe" in t or "nought" in t:
            return "tictactoe"
        return None

    def handle_input(self, text: str):
        if not self.active_key:
            return None
        game = self.games[self.active_key]
        update = game.handle_input(text)
        if update.score_event:
            self.scoreboard.record(game.name, update.score_event)
        if update.done:
            self.active_key = None
        return update


class AssistantController(QObject):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()
        if not self.settings.system_prompt:
            self.settings.system_prompt = DEFAULT_SYSTEM_PROMPT

        self.scoreboard = Scoreboard(self.settings_manager.data_dir)
        self.stt = STTManager(
            engine=self.settings.stt_engine,
            model_name=self.settings.whisper_model,
            compute_type=self.settings.whisper_compute_type,
            device=self.settings.whisper_device,
            whisper_cpp_path=self.settings.whisper_cpp_path,
            whisper_cpp_model=self.settings.whisper_cpp_model,
        )
        self.tts = PiperTTS(
            voice=self.settings.tts_voice,
            speaker_id=self.settings.tts_speaker,
            piper_path=self.settings.piper_path,
        )
        self.player = AudioPlayer()
        self.ollama = OllamaClient(self.settings.ollama_base_url)

        self.ui = MainWindow()
        self.ui.talkClicked.connect(self.manual_listen)
        self.ui.stopClicked.connect(self.stop_all)
        self.ui.settingsClicked.connect(self.open_settings)
        self.ui.gamesClicked.connect(self.open_games_hub)
        self.ui.gameStartClicked.connect(self.start_game_from_ui)
        self.ui.gameInputSubmitted.connect(self.handle_game_input)
        self.ui.cameraClicked.connect(self.handle_camera_button)

        self.game_manager = GameManager(self.scoreboard)
        self.wakeword = WakeWordService(
            mode=self.settings.wakeword_mode,
            stt=self.stt,
            settings=self.settings,
            on_wake=self.on_wake_word,
        )

        self.listen_worker = None
        self.llm_worker = None
        self.speech_worker = None
        self.stop_listener = None
        self.state = STATE_IDLE
        self.history = []
        self.memory = []

        self.update_ui_state(STATE_IDLE)
        self.apply_startup_checks()

    def apply_startup_checks(self):
        if not self.ollama.health():
            self.ui.set_warning("Ollama is not reachable. Start 'ollama serve'.")
        if not self.tts.is_available:
            self.ui.set_warning("Piper TTS not found. Install Piper or set TTS voice path in Settings.")
        if self.settings.wakeword_mode == "openwakeword":
            try:
                import openwakeword  # noqa: F401
            except Exception:
                self.ui.set_warning("openWakeWord not installed. Run: pip install openwakeword")

    def start(self):
        self.ui.set_kiosk_mode(self.settings.kiosk_mode)
        self.ui.show()
        self.wakeword.start()

    def stop_all(self):
        if self.listen_worker:
            self.listen_worker.stop()
        if self.llm_worker:
            self.llm_worker.stop()
        if self.speech_worker:
            self.speech_worker.stop()
        if self.stop_listener:
            self.stop_listener.stop()
        self.update_ui_state(STATE_IDLE)

    def update_ui_state(self, state: str):
        self.state = state
        self.ui.set_status(state)
        if state == STATE_IDLE:
            self.ui.set_face_state("idle")
        elif state == STATE_LISTENING:
            self.ui.set_face_state("listening")
        elif state == STATE_THINKING:
            self.ui.set_face_state("thinking")
        elif state == STATE_SPEAKING:
            self.ui.set_face_state("speaking")

    def on_wake_word(self):
        if self.state != STATE_IDLE:
            return
        self.manual_listen()

    def manual_listen(self):
        if self.state != STATE_IDLE:
            return
        self.wakeword.pause()
        self.update_ui_state(STATE_LISTENING)
        self.listen_worker = ListenWorker(self.settings, self.stt)
        self.listen_worker.transcript.connect(self.on_transcript)
        self.listen_worker.error.connect(self.on_listen_error)
        self.listen_worker.start()

    def on_listen_error(self, message: str):
        self.ui.set_warning(f"Listen error: {message}")
        self.update_ui_state(STATE_IDLE)
        self.wakeword.resume()

    def on_transcript(self, text: str):
        self.wakeword.resume()
        if not text:
            self.update_ui_state(STATE_IDLE)
            return
        self.ui.append_transcript("You", text)
        self.handle_user_text(text)

    def handle_user_text(self, text: str):
        lower = text.lower()
        if "remember" in lower:
            self.capture_memory(text)

        if self.game_manager.active():
            update = self.game_manager.handle_input(text)
            if update:
                self.ui.set_game_status(update.status)
                self.ui.set_game_quick_buttons(update.quick_buttons)
                if update.score_event:
                    self.ui.set_game_scoreboard(self.scoreboard.summary(update.game_name))
                self.ui.append_transcript("Bemo", update.text)
                self.reply_with_text(update.text)
                if update.done:
                    self.ui.set_game_inactive()
            return

        start_key = self.game_manager.maybe_start_from_text(text)
        if start_key:
            self.start_game(start_key)
            return

        if self.settings.camera_enabled and ("camera" in lower or "see" in lower):
            handled = self.handle_camera_query(text)
            if handled:
                return

        if "stop" in lower and self.state == STATE_SPEAKING:
            self.stop_all()
            return

        self.ask_llm(text)

    def capture_memory(self, text: str):
        match = re.search(r"remember (that )?(.*)", text, re.IGNORECASE)
        if match:
            memory = match.group(2).strip()
            if memory:
                self.memory.append(memory)

    def memory_blurb(self):
        if not self.memory:
            return ""
        lines = "\n".join(f"- {m}" for m in self.memory[-5:])
        return f"\nMemory:\n{lines}\n"

    def ask_llm(self, text: str):
        self.update_ui_state(STATE_THINKING)
        self.ui.update_streaming_assistant("")

        system_prompt = self.settings.system_prompt or DEFAULT_SYSTEM_PROMPT
        system_prompt += self.memory_blurb()

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history[-self.settings.history_max_messages :])
        messages.append({"role": "user", "content": text})

        self.llm_worker = LLMWorker(
            self.ollama, messages, self.settings.ollama_model, self.settings.ollama_temperature
        )
        self.llm_worker.partial.connect(self.ui.update_streaming_assistant)
        self.llm_worker.done.connect(self.on_llm_done)
        self.llm_worker.error.connect(self.on_llm_error)
        self.llm_worker.start()

    def on_llm_error(self, message: str):
        self.ui.set_warning(f"LLM error: {message}")
        self.update_ui_state(STATE_IDLE)

    def on_llm_done(self, response: str):
        self.history.append({"role": "user", "content": self.ui.last_user_text()})
        self.history.append({"role": "assistant", "content": response})
        self.ui.update_streaming_assistant(response)
        self.reply_with_text(response)

    def reply_with_text(self, response: str):
        if not response:
            self.update_ui_state(STATE_IDLE)
            return
        if not self.tts.is_available:
            self.ui.set_warning("TTS unavailable. Set a valid Piper executable and voice in Settings.")
            self.update_ui_state(STATE_IDLE)
            return
        self.update_ui_state(STATE_SPEAKING)
        self.speech_worker = SpeechWorker(response, self.settings, self.tts, self.player)
        self.speech_worker.amplitude.connect(self.ui.set_mouth_level)
        self.speech_worker.done.connect(self.on_speech_done)
        self.speech_worker.error.connect(self.on_speech_error)
        self.speech_worker.start()
        self.stop_listener = StopListener(self.settings, self.stt, self.stop_all)
        self.stop_listener.start()

    def on_speech_error(self, message: str):
        self.ui.set_warning(f"TTS error: {message}")
        self.update_ui_state(STATE_IDLE)

    def on_speech_done(self):
        if self.stop_listener:
            self.stop_listener.stop()
        self.update_ui_state(STATE_IDLE)

    def start_game_from_ui(self, key: str):
        self.start_game(key)

    def start_game(self, key: str):
        update = self.game_manager.start(key)
        if not update:
            return
        self.ui.set_game_active(update.game_name)
        self.ui.set_game_status(update.status)
        self.ui.set_game_quick_buttons(update.quick_buttons)
        self.ui.set_game_scoreboard(self.scoreboard.summary(update.game_name))
        self.ui.append_transcript("Bemo", update.text)
        self.reply_with_text(update.text)

    def handle_game_input(self, text: str):
        if not self.game_manager.active():
            return
        update = self.game_manager.handle_input(text)
        if update:
            self.ui.set_game_status(update.status)
            self.ui.set_game_quick_buttons(update.quick_buttons)
            self.ui.set_game_scoreboard(self.scoreboard.summary(update.game_name))
            self.ui.append_transcript("Bemo", update.text)
            self.reply_with_text(update.text)
            if update.done:
                self.ui.set_game_inactive()

    def handle_camera_button(self):
        if not self.settings.camera_enabled:
            self.reply_with_text("Camera is disabled in Settings.")
            return
        self.handle_camera_query("camera")

    def handle_camera_query(self, text: str):
        try:
            import cv2
        except Exception:
            self.reply_with_text("Camera module not installed. Install opencv-python to enable vision.")
            return True

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.reply_with_text("I can't access the camera right now.")
            return True
        ret, frame = cap.read()
        cap.release()
        if not ret:
            self.reply_with_text("Camera capture failed.")
            return True
        temp_path = self.settings_manager.data_dir / "camera.png"
        cv2.imwrite(str(temp_path), frame)
        try:
            self.update_ui_state(STATE_THINKING)
            messages = [{"role": "system", "content": self.settings.system_prompt}]
            messages.append({"role": "user", "content": text, "images": [str(temp_path)]})
            response = self.ollama.chat_with_image(
                messages,
                model=self.settings.ollama_model,
                temperature=self.settings.ollama_temperature,
            )
            self.ui.append_transcript("Bemo", response)
            self.reply_with_text(response)
        except Exception as exc:
            self.reply_with_text(f"Vision error: {exc}")
        return True

    def open_settings(self):
        models = self.ollama.list_models()
        self.ui.open_settings(self.settings, models, self.verify_ollama, self.run_stt_test)
        if self.ui.settings_result is None:
            return
        previous_mode = self.settings.wakeword_mode
        self.settings = self.ui.settings_result
        self.settings_manager.save(self.settings)
        self.stt.update_engine(
            engine=self.settings.stt_engine,
            model_name=self.settings.whisper_model,
            compute_type=self.settings.whisper_compute_type,
            device=self.settings.whisper_device,
            whisper_cpp_path=self.settings.whisper_cpp_path,
            whisper_cpp_model=self.settings.whisper_cpp_model,
        )
        self.tts.update_voice(self.settings.tts_voice, self.settings.tts_speaker, self.settings.piper_path)
        self.wakeword.update_settings(self.settings)
        if previous_mode != self.settings.wakeword_mode:
            self.wakeword.stop()
            self.wakeword.start()
        self.ui.set_kiosk_mode(self.settings.kiosk_mode)

    def verify_ollama(self):
        ok = self.ollama.health()
        models = self.ollama.list_models()
        if ok:
            if models:
                preview = ", ".join(models[:5])
                message = f"Ollama OK. {len(models)} models. {preview}"
            else:
                message = "Ollama OK. No models listed yet."
        else:
            message = "Ollama not reachable. Start 'ollama serve'."
        return ok, models, message

    def run_stt_test(self, settings: AppSettings):
        try:
            audio = self._record_seconds(settings, seconds=3)
            stt = STTManager(
                engine=settings.stt_engine,
                model_name=settings.whisper_model,
                compute_type=settings.whisper_compute_type,
                device=settings.whisper_device,
                whisper_cpp_path=settings.whisper_cpp_path,
                whisper_cpp_model=settings.whisper_cpp_model,
            )
            text = stt.transcribe(audio, settings.sample_rate, language=settings.language)
            text = text.strip() if text else "(no speech detected)"
            return True, text
        except Exception as exc:
            return False, str(exc)

    def _record_seconds(self, settings: AppSettings, seconds=3):
        frames = int(settings.sample_rate * seconds)
        data = sd.rec(
            frames,
            samplerate=settings.sample_rate,
            channels=1,
            dtype="int16",
            device=settings.mic_device if settings.mic_device else None,
        )
        sd.wait()
        return data.reshape(-1)

    def open_games_hub(self):
        games = [
            {"key": "guess", "label": "Guess Number", "score": self.scoreboard.summary("guess_number")},
            {"key": "rps", "label": "Rock Paper Scissors", "score": self.scoreboard.summary("rock_paper_scissors")},
            {"key": "trivia", "label": "Trivia", "score": self.scoreboard.summary("trivia")},
            {"key": "tictactoe", "label": "Tic Tac Toe", "score": self.scoreboard.summary("tictactoe")},
        ]
        selected = self.ui.open_games_hub(games)
        if selected:
            self.start_game(selected)

    def shutdown(self):
        self.wakeword.stop()
        if self.listen_worker:
            self.listen_worker.stop()
            self.listen_worker.wait(2000)
        if self.llm_worker:
            self.llm_worker.stop()
            self.llm_worker.wait(2000)
        if self.speech_worker:
            self.speech_worker.stop()
            self.speech_worker.wait(2000)
        if self.stop_listener:
            self.stop_listener.stop()
            self.stop_listener.join(timeout=2)


def setup_logging(data_dir: Path):
    log_path = data_dir / "bemo.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )


def main():
    app = QApplication(sys.argv)
    apply_theme(app)

    controller = AssistantController()
    setup_logging(controller.settings_manager.data_dir)
    controller.start()

    app.aboutToQuit.connect(controller.shutdown)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

