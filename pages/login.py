# pages/login.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from data_manager import load_users, save_users, load_settings, save_settings


class LoginPage(QWidget):
    def __init__(self, app, standalone: bool = False):
        super().__init__()
        self.app = app
        self.standalone = standalone

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Welcome to Study Helper")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600;")
        layout.addWidget(title)

        subtitle = QLabel("Log in or create an account to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        row = QHBoxLayout()
        login_btn = QPushButton("Log In")
        signup_btn = QPushButton("Sign Up")

        login_btn.clicked.connect(self.handle_login)
        signup_btn.clicked.connect(self.handle_signup)

        row.addWidget(login_btn)
        row.addWidget(signup_btn)
        layout.addLayout(row)

        self.setLayout(layout)

        # Pre-fill last user if any
        settings = load_settings()
        if settings.get("last_user"):
            self.username_input.setText(settings["last_user"])

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Missing", "Please enter username and password.")
            return

        users = load_users()
        if username not in users or users[username] != password:
            QMessageBox.warning(self, "Error", "Invalid username or password.")
            return

        self.finish_login(username)

    def handle_signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Missing", "Please enter username and password.")
            return

        users = load_users()
        if username in users:
            QMessageBox.warning(self, "Exists", "User already exists.")
            return

        users[username] = password
        save_users(users)
        self.finish_login(username)

    def finish_login(self, username: str):
        # Remember settings
        settings = load_settings()
        settings["last_user"] = username
        save_settings(settings)

        self.app.set_current_user(username)
        self.app.switch_to("dashboard")
