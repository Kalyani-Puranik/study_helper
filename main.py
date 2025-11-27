# main.py
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainter, QColor, QIcon

from data_manager import load_json, save_json
from themes import build_stylesheet, THEME_NAMES, LIGHT_THEMES
from pages import (
    LoginPage, DashboardPage, TodoPage, NotesPage,
    FlashcardsPage, ResourcesPage, SchedulePage,
    ClipartPage, TimerPage
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Helper")
        self.resize(1000, 650)

        self.current_user = None
        self.child_windows = []

        self.font_name = self.load_handwriting_font()

        self.settings = load_json("settings.json", {"theme": "Pink", "dark": False, "last_user": ""})
        self.theme_name = self.settings.get("theme", "Pink")
        if self.theme_name not in THEME_NAMES:
            self.theme_name = "Pink"
        self.dark_mode = bool(self.settings.get("dark", False))
        self.current_user = self.settings.get("last_user") or None

        central = QWidget()
        root = QVBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        # ---------- top bar ----------
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Student Helper")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(140)
        self.populate_theme_combo()
        self.theme_combo.setCurrentText(self.theme_name)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        self.dark_btn = QPushButton("☾" if not self.dark_mode else "☀")
        self.dark_btn.setFixedWidth(40)
        self.dark_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.dark_btn.setToolTip("Toggle dark / light")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        root.addLayout(top_bar)

        # ---------- stacked pages ----------
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.pages = {}
        self.pages["login"] = LoginPage(self.switch_to, self.set_current_user)
        self.pages["dashboard"] = DashboardPage(self.switch_to, self.open_in_new_window,
                                                self.get_current_user, self.logout)
        self.pages["todo"] = TodoPage(self.switch_to)
        self.pages["notes"] = NotesPage(self.switch_to)
        self.pages["flashcards"] = FlashcardsPage(self.switch_to)
        self.pages["resources"] = ResourcesPage(self.switch_to)
        self.pages["schedule"] = SchedulePage(self.switch_to)
        self.pages["clipart"] = ClipartPage(self.switch_to)
        self.pages["timer"] = TimerPage(self.switch_to)

        self.page_order = [
            "login", "dashboard", "todo", "notes",
            "flashcards", "resources", "schedule",
            "clipart", "timer"
        ]

        for key in self.page_order:
            self.stack.addWidget(self.pages[key])

        if self.current_user:
            self.title_label.setText("Student Helper — " + self.current_user)
            self.switch_to("dashboard")
        else:
            self.switch_to("login")

        self.apply_theme()

    # ---------- fonts & themes ----------

    def load_handwriting_font(self):
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ttf_path = os.path.join(assets_dir, "handwriting.ttf")
        if os.path.exists(ttf_path):
            font_id = QFontDatabase.addApplicationFont(ttf_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "Avenir"

    def populate_theme_combo(self):
        self.theme_combo.clear()
        for name in THEME_NAMES:
            colors = LIGHT_THEMES[name]
            pix = QPixmap(20, 20)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)

            # big circle = accent
            p.setBrush(QColor(colors["button_bg"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(1, 1, 18, 18)

            # little arc = card bg
            p.setBrush(QColor(colors["card_bg"]))
            p.drawPie(1, 1, 18, 18, 90 * 16, 180 * 16)

            p.end()
            icon = QIcon(pix)
            self.theme_combo.addItem(icon, name)

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("☾" if not self.dark_mode else "☀")

    def change_theme(self, name):
        self.theme_name = name
        self.apply_theme()
        self.save_settings()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()

    def save_settings(self):
        self.settings["theme"] = self.theme_name
        self.settings["dark"] = self.dark_mode
        self.settings["last_user"] = self.current_user or ""
        save_json("settings.json", self.settings)

    # ---------- user / navigation ----------

    def set_current_user(self, username):
        self.current_user = username
        self.title_label.setText("Student Helper — " + username)
        self.save_settings()

    def get_current_user(self):
        return self.current_user

    def logout(self):
        self.current_user = None
        self.title_label.setText("Student Helper")
        self.save_settings()
        self.switch_to("login")

    def switch_to(self, key):
        if key not in self.page_order:
            key = "login"
        index = self.page_order.index(key)
        self.stack.setCurrentIndex(index)
        if key == "dashboard":
            page = self.pages["dashboard"]
            if hasattr(page, "refresh"):
                page.refresh()

    # ---------- multi-window ----------

    def open_in_new_window(self, key):
        cls_map = {
            "todo": TodoPage,
            "notes": NotesPage,
            "flashcards": FlashcardsPage,
            "resources": ResourcesPage,
            "schedule": SchedulePage,
            "clipart": ClipartPage,
            "timer": TimerPage,
        }
        if key not in cls_map:
            return
        cls = cls_map[key]
        win = QMainWindow(self)
        win.setWindowTitle("Student Helper — " + key.title())
        page = cls(None, standalone=True)
        win.setCentralWidget(page)
        win.resize(800, 550)
        win.show()
        self.child_windows.append(win)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
