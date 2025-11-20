# pages/notes.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QTextEdit, QPushButton, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from data_manager import load_json, save_json


class NotesPage(QWidget):
    FOLDERS_FILE = "notes_folders.json"

    def __init__(self, app, standalone: bool = False):
        super().__init__()
        self.app = app
        self.standalone = standalone

        self.folders = load_json(self.FOLDERS_FILE, {"folders": {}})
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        back = QPushButton("← Dashboard")
        back.clicked.connect(lambda: self.app.switch_to("dashboard"))
        top.addWidget(back)
        top.addStretch()
        layout.addLayout(top)

        title = QLabel("Notes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        main_row = QHBoxLayout()

        # Folder list
        left = QVBoxLayout()
        folder_label = QLabel("Folders / Subjects")
        left.addWidget(folder_label)

        self.folder_list = QListWidget()
        self.folder_list.currentTextChanged.connect(self.change_folder)
        left.addWidget(self.folder_list)

        folder_row = QHBoxLayout()
        self.new_folder_input = QLineEdit()
        self.new_folder_input.setPlaceholderText("New folder/subject")
        add_folder_btn = QPushButton("Add")
        add_folder_btn.clicked.connect(self.add_folder)
        folder_row.addWidget(self.new_folder_input)
        folder_row.addWidget(add_folder_btn)
        left.addLayout(folder_row)

        left_widget = QWidget()
        left_widget.setLayout(left)
        main_row.addWidget(left_widget, 1)

        # Notes area
        right = QVBoxLayout()
        self.notes_title_label = QLabel("No folder selected")
        right.addWidget(self.notes_title_label)

        self.text_edit = QTextEdit()
        right.addWidget(self.text_edit, 1)

        save_btn = QPushButton("Save Notes")
        save_btn.clicked.connect(self.save_notes)
        right.addWidget(save_btn)

        right_widget = QWidget()
        right_widget.setLayout(right)
        main_row.addWidget(right_widget, 2)

        layout.addLayout(main_row)
        self.setLayout(layout)

        self.refresh_folders()

    def refresh_folders(self):
        self.folder_list.clear()
        for folder in sorted(self.folders["folders"].keys()):
            self.folder_list.addItem(folder)

    def add_folder(self):
        name = self.new_folder_input.text().strip()
        if not name:
            return
        if name in self.folders["folders"]:
            QMessageBox.information(self, "Exists", "Folder already exists.")
            return
        self.folders["folders"][name] = {"content": ""}
        save_json(self.FOLDERS_FILE, self.folders)
        self.new_folder_input.clear()
        self.refresh_folders()

    def change_folder(self, name: str):
        if not name:
            return
        self.current_folder = name
        self.notes_title_label.setText(f"Notes — {name}")
        content = self.folders["folders"].get(name, {}).get("content", "")
        self.text_edit.setPlainText(content)

    def save_notes(self):
        if not self.current_folder:
            QMessageBox.information(self, "No folder", "Select a folder first.")
            return
        self.folders["folders"][self.current_folder]["content"] = self.text_edit.toPlainText()
        save_json(self.FOLDERS_FILE, self.folders)
        QMessageBox.information(self, "Saved", "Notes saved.")
