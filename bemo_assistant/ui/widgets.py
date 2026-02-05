import random
import time
import math
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget, QTextEdit, QFrame, QLabel, QLineEdit, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout


class FaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "idle"
        self.mouth_level = 0.2
        self.blink = False
        self._last_amp_time = 0.0
        self._talk_phase = 0.0
        self._talk_timer = QTimer(self)
        self._talk_timer.setInterval(80)
        self._talk_timer.timeout.connect(self._talk_tick)
        self.setMinimumHeight(220)
        self.setMinimumWidth(280)
        self._schedule_blink()

    def _schedule_blink(self):
        delay = random.randint(2000, 5000)
        QTimer.singleShot(delay, self._do_blink)

    def _do_blink(self):
        self.blink = True
        self.update()
        QTimer.singleShot(150, self._end_blink)

    def _end_blink(self):
        self.blink = False
        self.update()
        self._schedule_blink()

    def set_state(self, state: str):
        self.state = state
        if state == "idle":
            self.mouth_level = 0.15
            self._talk_timer.stop()
        elif state == "listening":
            self.mouth_level = 0.05
            self._talk_timer.stop()
        elif state == "thinking":
            self.mouth_level = 0.1
            self._talk_timer.stop()
        elif state == "speaking":
            if not self._talk_timer.isActive():
                self._talk_timer.start()
        self.update()

    def set_mouth_level(self, level: float):
        self.mouth_level = max(0.0, min(1.0, level))
        self._last_amp_time = time.time()
        self.update()

    def _talk_tick(self):
        if self.state != "speaking":
            self._talk_timer.stop()
            return
        if time.time() - self._last_amp_time < 0.25:
            return
        self._talk_phase += 0.4
        self.mouth_level = 0.15 + 0.2 * (1 + math.sin(self._talk_phase)) / 2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)

        painter.setBrush(QBrush(QColor("#BFF2E6")))
        painter.setPen(QPen(QColor("#3B7F7A"), 3))
        painter.drawRoundedRect(rect, 22, 22)

        eye_radius = 10
        eye_y = rect.top() + rect.height() * 0.35
        eye_x_offset = rect.width() * 0.22
        left_eye = (rect.left() + eye_x_offset, eye_y)
        right_eye = (rect.right() - eye_x_offset, eye_y)

        painter.setPen(QPen(QColor("#1E4D4A"), 3))
        painter.setBrush(QBrush(QColor("#1E4D4A")))
        if self.blink:
            painter.drawLine(left_eye[0] - 10, left_eye[1], left_eye[0] + 10, left_eye[1])
            painter.drawLine(right_eye[0] - 10, right_eye[1], right_eye[0] + 10, right_eye[1])
        else:
            painter.drawEllipse(int(left_eye[0]) - eye_radius, int(left_eye[1]) - eye_radius, eye_radius * 2, eye_radius * 2)
            painter.drawEllipse(int(right_eye[0]) - eye_radius, int(right_eye[1]) - eye_radius, eye_radius * 2, eye_radius * 2)

        mouth_width = rect.width() * 0.4
        mouth_height = 8 + (self.mouth_level * 24)
        mouth_x = rect.center().x() - mouth_width / 2
        mouth_y = rect.center().y() + rect.height() * 0.18

        painter.setPen(QPen(QColor("#1E4D4A"), 3))
        painter.setBrush(QBrush(QColor("#1E4D4A")))
        painter.drawRoundedRect(int(mouth_x), int(mouth_y), int(mouth_width), int(mouth_height), 8, 8)


class TranscriptPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("transcript")
        self._lines = []

    def add_line(self, role: str, text: str):
        self._lines.append(f"{role}: {text}")
        self._render()

    def update_last(self, role: str, text: str):
        if not self._lines or not self._lines[-1].startswith(f"{role}:"):
            self._lines.append(f"{role}: {text}")
        else:
            self._lines[-1] = f"{role}: {text}"
        self._render()

    def _render(self):
        self.setPlainText("\n".join(self._lines))
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class GamePanel(QFrame):
    inputSubmitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.status_label = QLabel("No game running")
        self.score_label = QLabel("")
        self.input_line = QLineEdit()
        self.send_button = QPushButton("Send")
        self.quick_layout = QGridLayout()

        self.send_button.clicked.connect(self._send_input)
        self.input_line.returnPressed.connect(self._send_input)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.score_label)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input_line)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)
        layout.addLayout(self.quick_layout)

        self._buttons = []

    def _send_input(self):
        text = self.input_line.text().strip()
        if not text:
            return
        self.inputSubmitted.emit(text)
        self.input_line.setText("")

    def set_status(self, text: str):
        self.status_label.setText(text)

    def set_score(self, text: str):
        self.score_label.setText(text)

    def set_quick_buttons(self, buttons):
        for btn in self._buttons:
            self.quick_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons = []

        count = len(buttons or [])
        cols = 3 if count == 9 else 4

        for idx, (label, value) in enumerate(buttons or []):
            btn = QPushButton(label)
            btn.setObjectName("gameBtn")
            btn.clicked.connect(lambda checked=False, v=value: self.inputSubmitted.emit(v))
            row = idx // cols
            col = idx % cols
            self.quick_layout.addWidget(btn, row, col)
            self._buttons.append(btn)
