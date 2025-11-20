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
from pages import (
    LoginPage, DashboardPage, TodoPage, NotesPage,
    FlashcardsPage, ResourcesPage, SchedulePage,
    ClipartPage, TimerPage, PageWindow
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Helper")
        self.resize(1000, 650)  # still resizable smaller

        self.current_user: str | None = None

        # load handwriting font if present
        self.font_name = self.load_handwriting_font()

        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "Pink")
        self.dark_mode = self.settings.get("dark", False)

        central = QWidget()
        root = QVBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        # top bar --------------------------------------------------------
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Student Helper")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Pink", "Purple", "Green", "Yellow", "Blue", "Mono"])
        self.theme_combo.setCurrentText(self.theme_name)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        self.dark_btn = QPushButton("Dark Mode" if not self.dark_mode else "Light Mode")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        root.addLayout(top_bar)

        # stacked pages --------------------------------------------------
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # create pages
        self.pages = {}

        self.pages["login"] = LoginPage(self)
        self.pages["dashboard"] = DashboardPage(self)
        self.pages["todo"] = TodoPage(self)
        self.pages["notes"] = NotesPage(self)
        self.pages["flashcards"] = FlashcardsPage(self)
        self.pages["resources"] = ResourcesPage(self)
        self.pages["schedule"] = SchedulePage(self)
        self.pages["clipart"] = ClipartPage(self)
        self.pages["timer"] = TimerPage(self)

        for key in ["login", "dashboard", "todo", "notes",
                    "flashcards", "resources", "schedule",
                    "clipart", "timer"]:
            self.stack.addWidget(self.pages[key])

        # decide start page
        if self.settings.get("last_user"):
            self.current_user = self.settings["last_user"]
            self.switch_to("dashboard")
        else:
            self.switch_to("login")

        self.apply_theme()

    # ------------ theming & fonts ------------

    def load_handwriting_font(self) -> str:
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ttf_path = os.path.join(assets_dir, "handwriting.ttf")
        if os.path.exists(ttf_path):
            font_id = QFontDatabase.addApplicationFont(ttf_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "Comic Sans MS"

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("Dark Mode" if not self.dark_mode else "Light Mode")

    def change_theme(self, name: str):
        self.theme_name = name
        self.apply_theme()
        self.save_current_settings()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_current_settings()

    def save_current_settings(self):
        self.settings["theme"] = self.theme_name
        self.settings["dark"] = self.dark_mode
        self.settings["last_user"] = self.current_user or ""
        save_settings(self.settings)

    # ------------ navigation ------------

    def switch_to(self, key: str):
        # stack index order matches keys insertion above
        index = ["login", "dashboard", "todo", "notes",
                 "flashcards", "resources", "schedule",
                 "clipart", "timer"].index(key)
        self.stack.setCurrentIndex(index)

    def set_current_user(self, username: str):
        self.current_user = username
        self.save_current_settings()
        self.title_label.setText(f"Student Helper — {username}")

    def logout(self):
        self.current_user = None
        self.save_current_settings()
        self.title_label.setText("Student Helper")
        self.switch_to("login")

    # ------------ multi-window support ------------

    def open_in_new_window(self, key: str):
        cls_map = {
            "dashboard": DashboardPage,
            "todo": TodoPage,
            "notes": NotesPage,
            "flashcards": FlashcardsPage,
            "resources": ResourcesPage,
            "schedule": SchedulePage,
            "clipart": ClipartPage,
            "timer": TimerPage,
        }
        cls = cls_map.get(key)
        if not cls:
            return
        win = PageWindow(self, cls, f"{key.title()} — window")
        win.show()

    # small helper for old name
    def switch_to_page(self, key: str):
        self.switch_to(key)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
