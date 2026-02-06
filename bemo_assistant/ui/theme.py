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
QPushButton {{
    background: {PALETTE['dark']};
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-size: 15px;
}}
QPushButton#accent {{
    background: {PALETTE['accent_yellow']};
    color: #2C2C2C;
}}
QPushButton#danger {{
    background: {PALETTE['accent_red']};
    color: white;
}}
QPushButton#gameBtn {{
    background: {PALETTE['accent_blue']};
    color: white;
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
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
}}
"""


def apply_theme(app):
    app.setStyleSheet(STYLE_SHEET)
