# themes.py
# Pastel + dark themes, with button colors included.

BASE_WIDGETS = """
QMainWindow {{
    background-color: {bg};
}}

QWidget {{
    background-color: {bg};
    color: {fg};
    font-family: "{font}";
    font-size: 14px;
}}

QPushButton {{
    background-color: {button_bg};
    color: {button_fg};
    border-radius: 14px;
    padding: 7px 16px;
    border: none;
}}
QPushButton:hover {{
    background-color: {button_bg_hover};
}}

QLineEdit, QTextEdit, QComboBox {{
    background-color: {card_bg};
    color: {fg};
    border-radius: 10px;
    border: 1px solid {border};
    padding: 6px 10px;
}}

QListWidget {{
    background-color: {card_bg};
    color: {fg};
    border-radius: 10px;
    border: 1px solid {border};
}}

QLabel {{
    color: {fg};
}}
"""

LIGHT_THEMES = {
    "Pink": dict(
        bg="#fff8fb",
        card_bg="#ffffff",
        border="#f0d1e3",
        fg="#2f2233",
        accent="#f7b7d7",
        accent_hover="#f29ac5",
        button_bg="#f7b7d7",
        button_bg_hover="#f29ac5",
        button_fg="#2f2233",
    ),
    "Purple": dict(
        bg="#f6f2ff",
        card_bg="#ffffff",
        border="#d7c9ff",
        fg="#241c3a",
        accent="#c3b0ff",
        accent_hover="#af98ff",
        button_bg="#c3b0ff",
        button_bg_hover="#af98ff",
        button_fg="#241c3a",
    ),
    "Green": dict(
        bg="#f3fff7",
        card_bg="#ffffff",
        border="#bfe6c9",
        fg="#1f3a29",
        accent="#8ed9a5",
        accent_hover="#71c38e",
        button_bg="#8ed9a5",
        button_bg_hover="#71c38e",
        button_fg="#1f3a29",
    ),
    "Yellow": dict(
        bg="#fffdf1",
        card_bg="#ffffff",
        border="#f6e0a8",
        fg="#4a3c16",
        accent="#ffd978",
        accent_hover="#ffc74a",
        button_bg="#ffd978",
        button_bg_hover="#ffc74a",
        button_fg="#4a3c16",
    ),
    "Blue": dict(
        bg="#f4f7ff",
        card_bg="#ffffff",
        border="#c7d6ff",
        fg="#1f2739",
        accent="#a2bfff",
        accent_hover="#86a9ff",
        button_bg="#a2bfff",
        button_bg_hover="#86a9ff",
        button_fg="#1f2739",
    ),
    "Mono": dict(
        bg="#f7f7f7",
        card_bg="#ffffff",
        border="#d5d5d5",
        fg="#222222",
        accent="#c4c4c4",
        accent_hover="#aaaaaa",
        button_bg="#c4c4c4",
        button_bg_hover="#aaaaaa",
        button_fg="#222222",
    ),
}

DARK_THEMES = {
    "Pink": dict(
        bg="#251623",
        card_bg="#321f30",
        border="#6f4661",
        fg="#f7e9f3",
        accent="#f29ac5",
        accent_hover="#ff7eb6",
        button_bg="#f29ac5",
        button_bg_hover="#ff7eb6",
        button_fg="#241222",
    ),
    "Purple": dict(
        bg="#1f182e",
        card_bg="#2a2142",
        border="#5c4d83",
        fg="#ebe4ff",
        accent="#b8a5ff",
        accent_hover="#a38fff",
        button_bg="#b8a5ff",
        button_bg_hover="#a38fff",
        button_fg="#1b1526",
    ),
    "Green": dict(
        bg="#102019",
        card_bg="#172f23",
        border="#3c6e50",
        fg="#e6f7ec",
        accent="#73c995",
        accent_hover="#5cb984",
        button_bg="#73c995",
        button_bg_hover="#5cb984",
        button_fg="#0e1914",
    ),
    "Yellow": dict(
        bg="#272015",
        card_bg="#342a18",
        border="#7c6231",
        fg="#fff3cf",
        accent="#ffcd6f",
        accent_hover="#ffb63a",
        button_bg="#ffcd6f",
        button_bg_hover="#ffb63a",
        button_fg="#231c11",
    ),
    "Blue": dict(
        bg="#101623",
        card_bg="#182134",
        border="#3a4b74",
        fg="#e2ebff",
        accent="#92adff",
        accent_hover="#7393ff",
        button_bg="#92adff",
        button_bg_hover="#7393ff",
        button_fg="#0e1520",
    ),
    "Mono": dict(
        bg="#171717",
        card_bg="#232323",
        border="#3f3f3f",
        fg="#f1f1f1",
        accent="#7f7f7f",
        accent_hover="#999999",
        button_bg="#7f7f7f",
        button_bg_hover="#999999",
        button_fg="#151515",
    ),
}

THEME_NAMES = list(LIGHT_THEMES.keys())
DEFAULT_FONT = "Avenir"


def build_stylesheet(theme_name, dark, font=None):
    base = DARK_THEMES if dark else LIGHT_THEMES
    if theme_name not in base:
        theme_name = "Pink"
    t = base[theme_name].copy()
    t["font"] = font or DEFAULT_FONT
    return BASE_WIDGETS.format(**t)
