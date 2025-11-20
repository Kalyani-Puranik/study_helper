# pages/dashboard.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout,
    QPushButton, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt
from . import PageWindow


class DashboardPage(QWidget):
    def __init__(self, app, standalone: bool = False):
        super().__init__()
        self.app = app
        self.standalone = standalone

        main = QVBoxLayout()
        main.setAlignment(Qt.AlignTop)

        title = QLabel("Study Helper Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600;")
        main.addWidget(title)

        subtitle = QLabel(f"Logged in as: {self.app.current_user or '—'}")
        subtitle.setAlignment(Qt.AlignCenter)
        main.addWidget(subtitle)

        # theme selector row comes from main, but add quick shortcuts
        info_row = QHBoxLayout()
        info_row.addStretch()
        logout_btn = QPushButton("Log Out")
        logout_btn.clicked.connect(lambda: self.app.logout())
        info_row.addWidget(logout_btn)
        main.addLayout(info_row)

        grid = QGridLayout()
        grid.setSpacing(20)

        tiles = [
            ("To-Do List", "todo"),
            ("Notes", "notes"),
            ("Flashcards", "flashcards"),
            ("Resources", "resources"),
            ("Schedule", "schedule"),
            ("Focus Timer", "timer"),
            ("Clipart Generator", "clipart"),
        ]

        for i, (label, key) in enumerate(tiles):
            row = i // 3
            col = i % 3
            wrapper = QWidget()
            v = QVBoxLayout()
            v.setContentsMargins(12, 12, 12, 12)
            wrapper.setLayout(v)
            wrapper.setStyleSheet(
                "background-color: rgba(255,255,255,0.7); border-radius: 18px;"
            )

            btn_main = QPushButton(label)
            btn_main.setStyleSheet("font-size: 18px; padding: 10px 16px;")
            btn_main.clicked.connect(lambda _, p=key: self.app.switch_to(p))
            v.addWidget(btn_main)

            open_win = QPushButton("Open in new window")
            open_win.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            open_win.clicked.connect(
                lambda _, cls_key=key: self.app.open_in_new_window(cls_key)
            )
            v.addWidget(open_win)

            grid.addWidget(wrapper, row, col)

        main.addLayout(grid)
        self.setLayout(main)

    def refresh(self):
        # update subtitle username if changed
        # called by main when needed
        pass
