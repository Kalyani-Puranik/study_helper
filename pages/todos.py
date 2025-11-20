# pages/todos.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from data_manager import load_json, save_json


class TodoPage(QWidget):
    FNAME = "todos.json"

    def __init__(self, app, standalone: bool = False):
        super().__init__()
        self.app = app
        self.standalone = standalone

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        top = QHBoxLayout()
        back = QPushButton("← Dashboard")
        back.clicked.connect(lambda: self.app.switch_to("dashboard"))
        top.addWidget(back)
        top.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All priorities", "High", "Medium", "Low"])
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.filter_combo)

        layout.addLayout(top)

        title = QLabel("To-Do List")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        lists_row = QHBoxLayout()

        self.pending_list = QListWidget()
        self.done_list = QListWidget()

        lists_row.addWidget(self.pending_list)
        lists_row.addWidget(self.done_list)

        layout.addLayout(lists_row)

        entry_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New task…")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["High", "Medium", "Low"])
        add_btn = QPushButton("Add")

        add_btn.clicked.connect(self.add_task)

        entry_row.addWidget(self.task_input)
        entry_row.addWidget(self.priority_combo)
        entry_row.addWidget(add_btn)
        layout.addLayout(entry_row)

        actions_row = QHBoxLayout()
        mark_done = QPushButton("Mark Pending → Done")
        mark_todo = QPushButton("Move Done → Pending")
        delete_btn = QPushButton("Delete Selected")

        mark_done.clicked.connect(self.move_pending_to_done)
        mark_todo.clicked.connect(self.move_done_to_pending)
        delete_btn.clicked.connect(self.delete_selected)

        actions_row.addWidget(mark_done)
        actions_row.addWidget(mark_todo)
        actions_row.addWidget(delete_btn)

        layout.addLayout(actions_row)

        self.setLayout(layout)
        self.refresh()

    # ------- persistence & refresh -------

    def load_data(self):
        return load_json(self.FNAME, [])

    def save_data(self, data):
        save_json(self.FNAME, data)

    def refresh(self):
        data = self.load_data()
        filt = self.filter_combo.currentText()
        self.pending_list.clear()
        self.done_list.clear()

        for item in data:
            if filt != "All priorities" and item["priority"] != filt:
                continue
            lw = QListWidgetItem(f"[{item['priority']}] {item['text']}")
            if item["done"]:
                self.done_list.addItem(lw)
            else:
                self.pending_list.addItem(lw)

    def _get_all_data(self):
        return self.load_data()

    # ------- actions -------

    def add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        priority = self.priority_combo.currentText()
        data = self._get_all_data()
        data.append({"text": text, "priority": priority, "done": False})
        self.save_data(data)
        self.task_input.clear()
        self.refresh()

    def _find_item_index(self, full_text, done):
        data = self._get_all_data()
        for i, item in enumerate(data):
            if item["done"] == done and f"[{item['priority']}] {item['text']}" == full_text:
                return i
        return None

    def move_pending_to_done(self):
        item = self.pending_list.currentItem()
        if not item:
            return
        idx = self._find_item_index(item.text(), False)
        if idx is None:
            return
        data = self._get_all_data()
        data[idx]["done"] = True
        self.save_data(data)
        self.refresh()

    def move_done_to_pending(self):
        item = self.done_list.currentItem()
        if not item:
            return
        idx = self._find_item_index(item.text(), True)
        if idx is None:
            return
        data = self._get_all_data()
        data[idx]["done"] = False
        self.save_data(data)
        self.refresh()

    def delete_selected(self):
        item = self.pending_list.currentItem() or self.done_list.currentItem()
        if not item:
            return
        data = self._get_all_data()
        idx_pending = self._find_item_index(item.text(), False)
        idx_done = self._find_item_index(item.text(), True)
        idx = idx_pending if idx_pending is not None else idx_done
        if idx is None:
            return
        del data[idx]
        self.save_data(data)
        self.refresh()
