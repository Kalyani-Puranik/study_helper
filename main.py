# main.py
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase

from data_manager import load_settings, save_settings
from themes import build_stylesheet
from page import (
    LoginPage, DashboardPage, TodoPage, NotesPage,
    FlashcardsPage, ResourcesPage, SchedulePage,
    ClipartPage, TimerPage
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Helper")
        self.resize(1000, 650)  # resizable

        self.current_user = None
        self.child_windows = []

        # load font
        self.font_name = self.load_handwriting_font()

        # settings
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "Pink")
        self.dark_mode = self.settings.get("dark", False)
        self.current_user = self.settings.get("last_user", None) or None

        central = QWidget()
        root = QVBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        # top bar -------------------------------------------------
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Student Helper")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Pink", "Purple", "Green", "Yellow", "Blue", "Mono"])
        if self.theme_name in ["Pink", "Purple", "Green", "Yellow", "Blue", "Mono"]:
            self.theme_combo.setCurrentText(self.theme_name)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        self.dark_btn = QPushButton("Dark Mode" if not self.dark_mode else "Light Mode")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        root.addLayout(top_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # create pages
        self.pages = {}

        self.pages["login"] = LoginPage(self.switch_to, self.set_current_user)
        self.pages["dashboard"] = DashboardPage(self.switch_to, self.open_in_new_window, self.get_current_user)
        self.pages["todo"] = TodoPage(self.switch_to)
        self.pages["notes"] = NotesPage(self.switch_to)
        self.pages["flashcards"] = FlashcardsPage(self.switch_to)
        self.pages["resources"] = ResourcesPage(self.switch_to)
        self.pages["schedule"] = SchedulePage(self.switch_to)
        self.pages["clipart"] = ClipartPage(self.switch_to)
        self.pages["timer"] = TimerPage(self.switch_to)

        self.page_order = ["login", "dashboard", "todo", "notes",
                           "flashcards", "resources", "schedule",
                           "clipart", "timer"]

        for key in self.page_order:
            self.stack.addWidget(self.pages[key])

        # start on login or dashboard
        if self.current_user:
            self.title_label.setText("Student Helper — " + self.current_user)
            self.switch_to("dashboard")
        else:
            self.switch_to("login")

        self.apply_theme()

    # ---------- font / theme ----------

    def load_handwriting_font(self):
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ttf = os.path.join(assets_dir, "handwriting.ttf")
        if os.path.exists(ttf):
            font_id = QFontDatabase.addApplicationFont(ttf)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "Comic Sans MS"

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("Dark Mode" if not self.dark_mode else "Light Mode")

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
        save_settings(self.settings)

    # ---------- user / navigation ----------

    def set_current_user(self, username):
        self.current_user = username
        self.title_label.setText("Student Helper — " + username)
        self.save_settings()

    def get_current_user(self):
        return self.current_user

    def switch_to(self, key):
        if key not in self.page_order:
            key = "login"
        index = self.page_order.index(key)
        self.stack.setCurrentIndex(index)

        # refresh dashboard when switching there
        if key == "dashboard":
            pages = self.pages["dashboard"]
            if hasattr(pages, "refresh"):
                pages.refresh()

    # ---------- multi-window ----------

    def open_in_new_window(self, key):
        # Only feature pages (not login)
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
        self.child_windows.append(win)  # keep reference so it doesn't get GC'd


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
