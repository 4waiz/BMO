import threading
from dataclasses import replace
import sounddevice as sd

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QFrame,
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QCheckBox,
)

from ui.widgets import FaceWidget, TranscriptPanel, GamePanel
from audio.tts import PiperTTS
from audio.playback import AudioPlayer
from storage.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, models, verify_fn=None, stt_test_fn=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bemo Settings")
        self._settings = replace(settings)
        self._models = models or []
        self._verify_fn = verify_fn
        self._stt_test_fn = stt_test_fn

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        for m in self._models:
            self.model_combo.addItem(m)
        self.model_combo.setCurrentText(settings.ollama_model)

        self.verify_btn = QPushButton("Verify Ollama")
        self.verify_status = QLabel("")
        self.verify_status.setWordWrap(True)
        self.verify_btn.clicked.connect(self._verify_ollama)

        self.wake_combo = QComboBox()
        self.wake_combo.addItems(["simple", "openwakeword"])
        self.wake_combo.setCurrentText(settings.wakeword_mode)
        self.wakeword_model_edit = QLineEdit(settings.wakeword_model)
        self.openwakeword_model_edit = QLineEdit(settings.openwakeword_model_path)
        self.openwakeword_hint = QLabel("openWakeWord requires: pip install openwakeword")
        self.openwakeword_hint.setWordWrap(True)

        self.stt_combo = QComboBox()
        self.stt_combo.addItems(["faster-whisper", "whisper.cpp"])
        self.stt_combo.setCurrentText(settings.stt_engine)

        self.whisper_model_edit = QLineEdit(settings.whisper_model)
        self.whisper_cpp_path = QLineEdit(settings.whisper_cpp_path)
        self.whisper_cpp_model = QLineEdit(settings.whisper_cpp_model)
        self.stt_test_btn = QPushButton("STT Test (3s)")
        self.stt_result = QLabel("")
        self.stt_result.setWordWrap(True)
        self.stt_test_btn.clicked.connect(self._run_stt_test)

        self.mic_combo = QComboBox()
        self.speaker_combo = QComboBox()
        self._load_devices(settings)

        self.tts_voice = QLineEdit(settings.tts_voice)
        self.tts_speaker = QLineEdit(settings.tts_speaker)
        self.piper_path = QLineEdit(settings.piper_path)
        self.tts_test = QPushButton("TTS Test")
        self.tts_test.clicked.connect(self._test_tts)

        self.system_prompt = QTextEdit(settings.system_prompt)
        self.system_prompt.setMinimumHeight(120)

        self.camera_check = QCheckBox("Enable Camera Vision")
        self.camera_check.setChecked(settings.camera_enabled)
        self.kiosk_check = QCheckBox("Kiosk Mode (Fullscreen)")
        self.kiosk_check.setChecked(settings.kiosk_mode)

        form.addRow("Ollama Model", self.model_combo)
        form.addRow("Ollama", self.verify_btn)
        form.addRow("", self.verify_status)
        form.addRow("Wake Word Mode", self.wake_combo)
        form.addRow("Wake Word Model", self.wakeword_model_edit)
        form.addRow("openWakeWord Model Path", self.openwakeword_model_edit)
        form.addRow("", self.openwakeword_hint)
        form.addRow("STT Engine", self.stt_combo)
        form.addRow("Whisper Model", self.whisper_model_edit)
        form.addRow("whisper.cpp Path", self.whisper_cpp_path)
        form.addRow("whisper.cpp Model", self.whisper_cpp_model)
        form.addRow("STT Test", self.stt_test_btn)
        form.addRow("", self.stt_result)
        form.addRow("Mic Device", self.mic_combo)
        form.addRow("Speaker Device", self.speaker_combo)
        form.addRow("Piper Voice Path", self.tts_voice)
        form.addRow("Piper Speaker ID", self.tts_speaker)
        form.addRow("Piper Executable Path", self.piper_path)
        form.addRow("TTS", self.tts_test)
        form.addRow("System Prompt", self.system_prompt)
        form.addRow("", self.camera_check)
        form.addRow("", self.kiosk_check)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _load_devices(self, settings):
        self.mic_combo.addItem("Default")
        self.speaker_combo.addItem("Default")
        try:
            devices = sd.query_devices()
        except Exception:
            devices = []
        for dev in devices:
            name = dev.get("name")
            if name:
                self.mic_combo.addItem(name)
                self.speaker_combo.addItem(name)
        if settings.mic_device:
            self.mic_combo.setCurrentText(settings.mic_device)
        if settings.speaker_device:
            self.speaker_combo.setCurrentText(settings.speaker_device)

    def _set_models(self, models):
        current = self.model_combo.currentText()
        if not models:
            return
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        self.model_combo.setCurrentText(current)
        self.model_combo.blockSignals(False)

    def _verify_ollama(self):
        if not self._verify_fn:
            self.verify_status.setText("Verify function not available.")
            return
        self.verify_status.setText("Checking Ollama...")
        self.verify_btn.setEnabled(False)

        def worker():
            ok, models, message = self._verify_fn()

            def apply():
                self.verify_status.setText(message)
                self._set_models(models)
                self.verify_btn.setEnabled(True)

            QTimer.singleShot(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _run_stt_test(self):
        if not self._stt_test_fn:
            self.stt_result.setText("STT test not available.")
            return
        self.stt_result.setText("Recording 3 seconds...")
        self.stt_test_btn.setEnabled(False)
        settings = self._collect_settings()

        def worker():
            ok, text = self._stt_test_fn(settings)

            def apply():
                prefix = "STT OK:" if ok else "STT Error:"
                self.stt_result.setText(f"{prefix} {text}")
                self.stt_test_btn.setEnabled(True)

            QTimer.singleShot(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _test_tts(self):
        voice = self.tts_voice.text().strip()
        if not voice:
            return
        try:
            tts = PiperTTS(
                voice,
                speaker_id=self.tts_speaker.text().strip(),
                piper_path=self.piper_path.text().strip(),
            )
            player = AudioPlayer()
            wav = tts.synthesize("Hello. This is a Bemo voice test.")
            player.play_wav(wav)
            try:
                import os
                os.remove(wav)
            except OSError:
                pass
        except Exception:
            pass

    def _collect_settings(self) -> AppSettings:
        settings = replace(self._settings)
        settings.ollama_model = self.model_combo.currentText().strip()
        settings.wakeword_mode = self.wake_combo.currentText().strip()
        settings.wakeword_model = self.wakeword_model_edit.text().strip()
        settings.openwakeword_model_path = self.openwakeword_model_edit.text().strip()
        settings.stt_engine = self.stt_combo.currentText().strip()
        settings.whisper_model = self.whisper_model_edit.text().strip()
        settings.whisper_cpp_path = self.whisper_cpp_path.text().strip()
        settings.whisper_cpp_model = self.whisper_cpp_model.text().strip()
        settings.mic_device = "" if self.mic_combo.currentText() == "Default" else self.mic_combo.currentText()
        settings.speaker_device = "" if self.speaker_combo.currentText() == "Default" else self.speaker_combo.currentText()
        settings.tts_voice = self.tts_voice.text().strip()
        settings.tts_speaker = self.tts_speaker.text().strip()
        settings.piper_path = self.piper_path.text().strip()
        settings.system_prompt = self.system_prompt.toPlainText().strip()
        settings.camera_enabled = self.camera_check.isChecked()
        settings.kiosk_mode = self.kiosk_check.isChecked()
        return settings

    def result_settings(self) -> AppSettings:
        self._settings = self._collect_settings()
        return self._settings


class GameHubDialog(QDialog):
    def __init__(self, games, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bemo Games Hub")
        self.selected = None

        layout = QVBoxLayout(self)
        title = QLabel("Choose a Game")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        grid = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        grid.addLayout(left_col)
        grid.addLayout(right_col)
        layout.addLayout(grid)

        for idx, game in enumerate(games):
            frame = QFrame()
            frame.setObjectName("card")
            frame_layout = QVBoxLayout(frame)
            btn = QPushButton(game["label"])
            btn.setObjectName("gameBtn")
            btn.clicked.connect(lambda checked=False, key=game["key"]: self._select(key))
            score = QLabel(game.get("score", ""))
            score.setWordWrap(True)
            frame_layout.addWidget(btn)
            frame_layout.addWidget(score)

            if idx % 2 == 0:
                left_col.addWidget(frame)
            else:
                right_col.addWidget(frame)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

    def _select(self, key: str):
        self.selected = key
        self.accept()


class MainWindow(QMainWindow):
    talkClicked = Signal()
    stopClicked = Signal()
    settingsClicked = Signal()
    gamesClicked = Signal()
    gameStartClicked = Signal(str)
    gameInputSubmitted = Signal(str)
    cameraClicked = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bemo Assistant")
        self.resize(1024, 720)
        self.settings_result = None
        self._last_user_text = ""

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        header = QHBoxLayout()
        title = QLabel("Bemo Assistant")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusLabel")
        header.addWidget(self.status_label)
        layout.addLayout(header)

        face_frame = QFrame()
        face_frame.setObjectName("faceFrame")
        face_layout = QVBoxLayout(face_frame)
        face_layout.setContentsMargins(6, 6, 6, 6)
        self.face = FaceWidget()
        face_layout.addWidget(self.face)
        layout.addWidget(face_frame)

        self.transcript_toggle = QToolButton()
        self.transcript_toggle.setText("Transcript")
        self.transcript_toggle.setCheckable(True)
        self.transcript_toggle.setChecked(True)
        self.transcript_toggle.toggled.connect(self._toggle_transcript)
        layout.addWidget(self.transcript_toggle)

        self.transcript = TranscriptPanel()
        self.transcript.setMinimumHeight(140)
        layout.addWidget(self.transcript)

        self.game_panel = GamePanel()
        self.game_panel.inputSubmitted.connect(self.gameInputSubmitted.emit)
        self.game_panel.setVisible(False)
        layout.addWidget(self.game_panel)

        layout.setStretchFactor(face_frame, 5)
        layout.setStretchFactor(self.transcript, 2)

        controls = QHBoxLayout()
        self.talk_btn = QPushButton("Talk")
        self.talk_btn.setObjectName("accent")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.settings_btn = QPushButton("Settings")
        self.games_btn = QPushButton("Games")
        self.camera_btn = QPushButton("Camera")

        self.talk_btn.clicked.connect(self.talkClicked.emit)
        self.stop_btn.clicked.connect(self.stopClicked.emit)
        self.settings_btn.clicked.connect(self.settingsClicked.emit)
        self.games_btn.clicked.connect(self.gamesClicked.emit)
        self.camera_btn.clicked.connect(self.cameraClicked.emit)

        controls.addWidget(self.talk_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.settings_btn)
        controls.addWidget(self.games_btn)
        controls.addWidget(self.camera_btn)
        layout.addLayout(controls)

        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 6, 10, 6)
        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        status_layout.addWidget(self.warning_label)
        status_layout.addStretch()
        layout.addWidget(self.status_bar)

    def _toggle_transcript(self, checked):
        self.transcript.setVisible(checked)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_face_state(self, state: str):
        self.face.set_state(state)

    def set_mouth_level(self, level: float):
        self.face.set_mouth_level(level)

    def append_transcript(self, role: str, text: str):
        if role.lower() == "you":
            self._last_user_text = text
        self.transcript.add_line(role, text)

    def update_streaming_assistant(self, text: str):
        self.transcript.update_last("Bemo", text)

    def last_user_text(self):
        return self._last_user_text

    def set_warning(self, text: str):
        self.warning_label.setText(text)
        self.warning_label.setVisible(bool(text.strip()))

    def set_game_active(self, name: str):
        self.game_panel.setVisible(True)

    def set_game_inactive(self):
        self.game_panel.setVisible(False)

    def set_game_status(self, text: str):
        self.game_panel.set_status(text)

    def set_game_scoreboard(self, text: str):
        self.game_panel.set_score(text)

    def set_game_quick_buttons(self, buttons):
        self.game_panel.set_quick_buttons(buttons)

    def set_kiosk_mode(self, enabled: bool):
        if enabled:
            self.showFullScreen()
        else:
            self.showNormal()

    def open_settings(self, settings: AppSettings, models, verify_fn=None, stt_test_fn=None):
        dialog = SettingsDialog(settings, models, verify_fn, stt_test_fn, self)
        if dialog.exec() == QDialog.Accepted:
            self.settings_result = dialog.result_settings()
        else:
            self.settings_result = None

    def open_games_hub(self, games):
        dialog = GameHubDialog(games, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected:
            return dialog.selected
        return None
