# main.py
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from themes import LIGHT_STYLESHEET, DARK_STYLESHEET
from pages import (
    DashboardPage, TodoPage, NotesPage, FlashcardsPage,
    FlashcardsPage as FlashcardsPageDuplicate,  # safe alias if needed
    FlashcardsPage as FlashcardPage,
)
# NOTE: above aliases won't break; we'll import the pages again directly below to be explicit
from pages import (
    DashboardPage, TodoPage, NotesPage, FlashcardsPage,
    ResourcesPage, SchedulePage, TimerPage, ClipartPage
)
from data_manager import load_json  # to ensure data dir exists & defaults created

# Ensure default files exist
load_json("todos.json", [])
load_json("resources.json", [])
load_json("flashcards.json", [])
load_json("notes.json", {"content": ""})
load_json("schedule.json", [])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Helper Dashboard")
        self.setMinimumSize(900, 600)

        self.theme_mode = "light"

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout()
        central.setLayout(root_layout)

        # top bar
        top_bar = QHBoxLayout()
        title_label = QLabel("Student Helper Dashboard")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.theme_button = QPushButton("🌙 Dark Mode")
        self.theme_button.setMaximumWidth(140)
        self.theme_button.clicked.connect(self.toggle_theme)

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.theme_button)
        root_layout.addLayout(top_bar)

        # stack
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack)

        # instantiate pages with goto_page callable
        self.dashboard_page = DashboardPage(self.switch_to_page)
        self.todo_page = TodoPage(self.switch_to_page)
        self.notes_page = NotesPage(self.switch_to_page)
        self.flashcards_page = FlashcardsPage(self.switch_to_page)
        self.resources_page = ResourcesPage(self.switch_to_page)
        self.schedule_page = SchedulePage(self.switch_to_page)
        self.timer_page = TimerPage(self.switch_to_page)
        self.clipart_page = ClipartPage(self.switch_to_page)

        # map and add
        self.page_map = {
            "dashboard": 0,
            "todo": 1,
            "notes": 2,
            "flashcards": 3,
            "resources": 4,
            "schedule": 5,
            "timer": 6,
            "clipart": 7,
        }

        self.stack.addWidget(self.dashboard_page)   # 0
        self.stack.addWidget(self.todo_page)        # 1
        self.stack.addWidget(self.notes_page)       # 2
        self.stack.addWidget(self.flashcards_page)  # 3
        self.stack.addWidget(self.resources_page)   # 4
        self.stack.addWidget(self.schedule_page)    # 5
        self.stack.addWidget(self.timer_page)       # 6
        self.stack.addWidget(self.clipart_page)     # 7

        self.stack.setCurrentIndex(self.page_map["dashboard"])
        self.apply_theme()

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        self.apply_theme()

    def apply_theme(self):
        if self.theme_mode == "light":
            self.setStyleSheet(LIGHT_STYLESHEET)
            self.theme_button.setText("🌙 Dark Mode")
        else:
            self.setStyleSheet(DARK_STYLESHEET)
            self.theme_button.setText("☀ Light Mode")
        # refresh dashboard/page states if they have refresh methods
        for page in (self.dashboard_page, self.todo_page, self.notes_page,
                     self.flashcards_page, self.resources_page, self.schedule_page):
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception:
                    pass

    def switch_to_page(self, page_name: str):
        idx = self.page_map.get(page_name, 0)
        self.stack.setCurrentIndex(idx)
        # refresh the page we switched to if possible
        widget = self.stack.currentWidget()
        if hasattr(widget, "refresh"):
            try:
                widget.refresh()
            except Exception:
                pass


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
