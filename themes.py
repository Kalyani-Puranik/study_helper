# themes.py
from PyQt5.QtGui import QColor

# -----------------------------------------------------
# Available theme names (shown in dropdown)
# -----------------------------------------------------
THEME_NAMES = [
    "Pink",
    "Purple",
    "Green",
    "Blue",
    "Yellow",
    "Mono"
]

# -----------------------------------------------------
# Light theme definitions
# -----------------------------------------------------
LIGHT_THEMES = {
    "Pink": {
        "bg": "#fff7fb",
        "card_bg": "#ffe2f1",
        "button_bg": "#ff9dcf",
        "button_hover": "#ff82c3",
        "text": "#333333",
        "sidebar": "#ffd3ea",
        "accent": "#ff91cb"
    },
    "Purple": {
        "bg": "#f8f4ff",
        "card_bg": "#eaddff",
        "button_bg": "#c6a4ff",
        "button_hover": "#b58cff",
        "text": "#2e2e2e",
        "sidebar": "#e8d6ff",
        "accent": "#bb96ff"
    },
    "Green": {
        "bg": "#f2fff8",
        "card_bg": "#d7ffe6",
        "button_bg": "#89e6b8",
        "button_hover": "#6edba8",
        "text": "#2a2a2a",
        "sidebar": "#caffe0",
        "accent": "#7de1b0"
    },
    "Blue": {
        "bg": "#f4faff",
        "card_bg": "#d6ecff",
        "button_bg": "#8dc6ff",
        "button_hover": "#75b8ff",
        "text": "#2c2c2c",
        "sidebar": "#cbe5ff",
        "accent": "#7abaff"
    },
    "Yellow": {
        "bg": "#fffdf3",
        "card_bg": "#fff1c1",
        "button_bg": "#ffd86d",
        "button_hover": "#ffcb44",
        "text": "#3a3a3a",
        "sidebar": "#ffe8a1",
        "accent": "#ffcd55"
    },
    "Mono": {
        "bg": "#f4f4f4",
        "card_bg": "#e8e8e8",
        "button_bg": "#bcbcbc",
        "button_hover": "#a0a0a0",
        "text": "#000000",
        "sidebar": "#dcdcdc",
        "accent": "#b8b8b8"
    }
}

# -----------------------------------------------------
# DARK THEMES — deeper, moodier tones
# -----------------------------------------------------
DARK_THEMES = {
    name: {
        "bg": QColor(theme["bg"]).darker(240).name(),
        "card_bg": QColor(theme["card_bg"]).darker(260).name(),
        "button_bg": QColor(theme["button_bg"]).darker(200).name(),
        "button_hover": QColor(theme["button_hover"]).darker(180).name(),
        "text": "#f7f7f7",
        "sidebar": QColor(theme["sidebar"]).darker(270).name(),
        "accent": QColor(theme["accent"]).darker(200).name()
    }
    for name, theme in LIGHT_THEMES.items()
}


# -----------------------------------------------------
# Helper to build full stylesheet
# -----------------------------------------------------
def build_stylesheet(theme_name: str, dark: bool, font=None) -> str:
    theme_source = DARK_THEMES if dark else LIGHT_THEMES
    t = theme_source.get(theme_name, LIGHT_THEMES["Pink"])

    font_family = font or "Avenir"

    return f"""
    QWidget {{
        background-color: {t['bg']};
        color: {t['text']};
        font-family: '{font_family}';
        font-size: 15px;
    }}

    /* Cards */
    QFrame#card, QWidget#card {{
        background-color: {t['card_bg']};
        border-radius: 18px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {t['button_bg']};
        color: {t['text']};
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 14px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {t['button_hover']};
    }}

    /* Inputs */
    QLineEdit, QTextEdit {{
        background-color: {t['card_bg']};
        border-radius: 10px;
        border: 1px solid {t['accent']};
        padding: 6px 10px;
        font-size: 14px;
    }}

    /* Lists */
    QListWidget {{
        background-color: {t['card_bg']};
        border-radius: 10px;
        border: 1px solid {t['accent']};
        padding: 6px;
    }}

    /* Sidebar */
    #sidebar {{
        background-color: {t['sidebar']};
        border-right: 2px solid {t['accent']};
    }}
    #sidebar QPushButton {{
        background-color: transparent;
        border-radius: 0;
        padding: 12px;
        text-align: left;
        font-size: 15px;
    }}
    #sidebar QPushButton:hover {{
        background-color: {t['button_bg']};
    }}

    /* Top bar */
    #topbar QLabel {{
        font-size: 18px;
        font-weight: 600;
    }}

    QComboBox {{
        background-color: {t['button_bg']};
        padding: 4px 8px;
        border-radius: 8px;
    }}

    QComboBox:hover {{
        background-color: {t['button_hover']};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['accent']};
        border-radius: 5px;
    }}

    /* Special labels (timer, flashcards) */
    QLabel#BigNumber {{
        font-size: 42px;
        font-weight: 600;
    }}
    QLabel#Flashcard {{
        background-color: {t['card_bg']};
        border-radius: 20px;
        padding: 20px;
        font-size: 22px;
    }}
    """


# -----------------------------------------------------
# All exported
# -----------------------------------------------------
__all__ = [
    "build_stylesheet",
    "THEME_NAMES",
    "LIGHT_THEMES",
    "DARK_THEMES"
]
