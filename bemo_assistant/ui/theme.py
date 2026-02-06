PALETTE = {
    "primary": "#76C7BE",
    "dark": "#3B7F7A",
    "screen": "#BFF2E6",
    "accent_yellow": "#F2D45C",
    "accent_red": "#D94A4A",
    "accent_blue": "#5AA7FF",
    "text": "#123E3A",
    "panel": "#E6FBF4",
}

STYLE_SHEET = f"""
QWidget {{
    font-family: 'Fira Sans','Noto Sans','DejaVu Sans','Segoe UI';
    color: {PALETTE['text']};
    font-size: 14px;
}}
QMainWindow {{
    background: {PALETTE['primary']};
}}
QDialog#settingsDialog {{
    background: #1E1F21;
}}
QFrame#settingsPanel {{
    background: #1E1F21;
    border-radius: 12px;
}}
QDialog#settingsDialog QLabel {{
    color: #F2FFFA;
}}
QDialog#settingsDialog QCheckBox {{
    color: #F2FFFA;
}}
QDialog#settingsDialog QToolButton {{
    color: #F2FFFA;
}}
QFrame#card {{
    background: {PALETTE['panel']};
    border-radius: 18px;
}}
QFrame#faceFrame {{
    background: transparent;
    border: none;
}}
QFrame#statusBar {{
    background: {PALETTE['panel']};
    border-radius: 12px;
}}
QLabel#statusLabel {{
    font-size: 16px;
    font-weight: 600;
}}
QLabel#warningLabel {{
    background: {PALETTE['accent_yellow']};
    color: #2C2C2C;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 600;
}}
QTextEdit#transcript {{
    background: #F8FFFD;
    border: 2px solid {PALETTE['dark']};
    border-radius: 12px;
    padding: 8px;
}}
QTextEdit#transcript {{
    min-height: 140px;
}}
QPushButton {{
    background: {PALETTE['dark']};
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-size: 15px;
}}
QPushButton:hover {{
    background: #4C9A94;
}}
QPushButton:pressed {{
    background: #2E6F6A;
}}
QPushButton#accent {{
    background: {PALETTE['accent_yellow']};
    color: #2C2C2C;
}}
QPushButton#accent:hover {{
    background: #F6DF77;
}}
QPushButton#accent:pressed {{
    background: #E3C24C;
}}
QPushButton#danger {{
    background: {PALETTE['accent_red']};
    color: white;
}}
QPushButton#danger:hover {{
    background: #E25B5B;
}}
QPushButton#danger:pressed {{
    background: #C33C3C;
}}
QPushButton#gameBtn {{
    background: {PALETTE['accent_blue']};
    color: white;
}}
QPushButton#gameBtn:hover {{
    background: #6AB2FF;
}}
QPushButton#gameBtn:pressed {{
    background: #4B90E6;
}}
QLineEdit {{
    background: white;
    border: 2px solid {PALETTE['dark']};
    border-radius: 10px;
    padding: 6px 10px;
}}
QComboBox {{
    background: white;
    border: 2px solid {PALETTE['dark']};
    border-radius: 10px;
    padding: 6px 10px;
}}
QDialog#settingsDialog QTextEdit {{
    background: #F7FFFC;
    color: #123E3A;
    border: 2px solid {PALETTE['dark']};
    border-radius: 10px;
    padding: 6px 10px;
}}
QDialog#settingsDialog QLineEdit {{
    background: #F7FFFC;
}}
QDialog#settingsDialog QComboBox {{
    background: #F7FFFC;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}
"""


def apply_theme(app):
    app.setStyleSheet(STYLE_SHEET)
