# themes.py

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
    background-color: {accent};
    color: {button_fg};
    border-radius: 12px;
    padding: 6px 14px;
    border: none;
}}
QPushButton:hover {{
    background-color: {accent_hover};
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
        bg="#fff5fb",
        card_bg="#ffffff",
        border="#f2cde2",
        fg="#333333",
        accent="#ff9acb",
        accent_hover="#ff7eb6",
        button_fg="#ffffff",
    ),
    "Purple": dict(
        bg="#f7f1ff",
        card_bg="#ffffff",
        border="#d9c9ff",
        fg="#2e2640",
        accent="#b39dff",
        accent_hover="#9c84ff",
        button_fg="#ffffff",
    ),
    "Green": dict(
        bg="#f3fff6",
        card_bg="#ffffff",
        border="#bae5c7",
        fg="#204028",
        accent="#7adf9b",
        accent_hover="#63ce85",
        button_fg="#ffffff",
    ),
    "Yellow": dict(
        bg="#fffceb",
        card_bg="#ffffff",
        border="#ffe18a",
        fg="#4b3d00",
        accent="#ffd666",
        accent_hover="#ffc233",
        button_fg="#4b3d00",
    ),
    "Blue": dict(
        bg="#f3f7ff",
        card_bg="#ffffff",
        border="#c2d5ff",
        fg="#1e2a3a",
        accent="#7eaaff",
        accent_hover="#5e91ff",
        button_fg="#ffffff",
    ),
    "Mono": dict(
        bg="#f6f6f6",
        card_bg="#ffffff",
        border="#d0d0d0",
        fg="#222222",
        accent="#444444",
        accent_hover="#222222",
        button_fg="#f6f6f6",
    ),
}

DARK_THEMES = {
    # darker, but not pure black — comfy dark mode
    "Pink": dict(
        bg="#241823",
        card_bg="#2f222e",
        border="#70445e",
        fg="#f5e8f2",
        accent="#ff7eb6",
        accent_hover="#ff5fa7",
        button_fg="#ffffff",
    ),
    "Purple": dict(
        bg="#201a2f",
        card_bg="#2c2342",
        border="#59427a",
        fg="#eee5ff",
        accent="#b39dff",
        accent_hover="#9c84ff",
        button_fg="#ffffff",
    ),
    "Green": dict(
        bg="#0f2016",
        card_bg="#16301f",
        border="#356646",
        fg="#e8f7ec",
        accent="#63ce85",
        accent_hover="#4fb972",
        button_fg="#0f2016",
    ),
    "Yellow": dict(
        bg="#261f0b",
        card_bg="#322814",
        border="#7b5e26",
        fg="#fff4cf",
        accent="#ffc233",
        accent_hover="#ffae00",
        button_fg="#261f0b",
    ),
    "Blue": dict(
        bg="#101624",
        card_bg="#171f30",
        border="#34446a",
        fg="#e1ebff",
        accent="#5e91ff",
        accent_hover="#446fe0",
        button_fg="#ffffff",
    ),
    "Mono": dict(
        bg="#171717",
        card_bg="#222222",
        border="#444444",
        fg="#f2f2f2",
        accent="#888888",
        accent_hover="#aaaaaa",
        button_fg="#111111",
    ),
}

DEFAULT_FONT = "Comic Sans MS"  # will be overridden if handwriting.ttf is loaded


def build_stylesheet(theme_name: str, dark: bool, font: str | None = None) -> str:
    base = DARK_THEMES if dark else LIGHT_THEMES
    theme = base.get(theme_name, base["Pink"]).copy()
    theme["font"] = font or DEFAULT_FONT
    return BASE_WIDGETS.format(**theme)
