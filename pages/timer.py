# pages/timer.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer


class TimerPage(QWidget):
    def __init__(self, app, standalone: bool = False):
        super().__init__()
        self.app = app
        self.standalone = standalone

        self.time_left = 25 * 60
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        back = QPushButton("← Dashboard")
        back.clicked.connect(lambda: self.app.switch_to("dashboard"))
        top.addWidget(back)
        top.addStretch()
        layout.addLayout(top)

        title = QLabel("Focus Timer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        self.flip_label = QLabel("25:00")
        self.flip_label.setAlignment(Qt.AlignCenter)
        self.flip_label.setStyleSheet("""
            font-size: 60px;
            font-weight: 600;
            padding: 20px 30px;
            border-radius: 18px;
            background-color: rgba(0,0,0,0.08);
            letter-spacing: 4px;
        """)
        layout.addWidget(self.flip_label)

        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText("Minutes (default 25)")
        layout.addWidget(self.minutes_input)

        controls = QHBoxLayout()
        start_btn = QPushButton("Start")
        stop_btn = QPushButton("Stop")
        reset_btn = QPushButton("Reset")

        start_btn.clicked.connect(self.start_timer)
        stop_btn.clicked.connect(self.stop_timer)
        reset_btn.clicked.connect(self.reset_timer)

        controls.addWidget(start_btn)
        controls.addWidget(stop_btn)
        controls.addWidget(reset_btn)
        layout.addLayout(controls)

        self.setLayout(layout)
        self.update_label()

    def start_timer(self):
        if self.running:
            return
        text = self.minutes_input.text().strip()
        if text:
            try:
                minutes = max(1, int(text))
                self.time_left = minutes * 60
            except ValueError:
                pass
        self.running = True
        self.timer.start(1000)
        self.update_label()

    def stop_timer(self):
        self.running = False
        self.timer.stop()

    def reset_timer(self):
        self.running = False
        self.timer.stop()
        self.time_left = 25 * 60
        self.update_label()

    def tick(self):
        if self.time_left <= 0:
            self.stop_timer()
            self.flip_label.setText("00:00")
            return
        self.time_left -= 1
        self.update_label()

    def update_label(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        self.flip_label.setText(f"{mins:02d}:{secs:02d}")
