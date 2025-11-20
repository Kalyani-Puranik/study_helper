# pages.py
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QFileDialog, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices
from data_manager import load_json, save_json

# simple shared styles
BUTTON_STYLE = "QPushButton { background-color: #f4d4ea; border-radius: 10px; padding: 8px; }"
TITLE_STYLE = "font-size: 20px; font-weight: 600; margin-bottom: 8px;"
TEXT_STYLE = "font-size: 14px;"


class BasePage(QWidget):
    def __init__(self, goto_page):
        super().__init__()
        self.goto_page = goto_page

    def add_back(self, layout):
        back = QPushButton("← Back to Dashboard")
        back.setStyleSheet(BUTTON_STYLE)
        back.clicked.connect(lambda: self.goto_page("dashboard"))
        layout.addWidget(back)


# ---------------- DASHBOARD ----------------
class DashboardPage(QWidget):
    def __init__(self, goto_page):
        super().__init__()
        self.goto_page = goto_page
        layout = QVBoxLayout()
        title = QLabel("Student Helper Dashboard")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Buttons to navigate
        btns = [
            ("To-Do List", "todo"),
            ("Notes", "notes"),
            ("Flashcards", "flashcards"),
            ("Resources", "resources"),
            ("Schedule", "schedule"),
            ("Clipart Generator", "clipart"),
            ("Focus Timer", "timer"),
        ]
        for text, page in btns:
            b = QPushButton(text)
            b.setStyleSheet(BUTTON_STYLE)
            b.clicked.connect(lambda _, p=page: goto_page(p))
            layout.addWidget(b)

        self.setLayout(layout)

    def refresh_stats(self):
        # placeholder if main wants to call it — no-op here
        pass


# ---------------- TODO ----------------
class TodoPage(BasePage):
    FNAME = "todos.json"

    def __init__(self, goto_page):
        super().__init__(goto_page)
        # list of {"text": str, "done": bool}
        self.data = load_json(self.FNAME, [])

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("To-Do List")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self.on_edit_item)
        layout.addWidget(self.listw)

        self.input = QLineEdit()
        self.input.setPlaceholderText("New task…")
        layout.addWidget(self.input)

        row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_task)
        row.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.setStyleSheet(BUTTON_STYLE)
        edit_btn.clicked.connect(self.edit_selected)
        row.addWidget(edit_btn)

        del_btn = QPushButton("Delete Selected")
        del_btn.setStyleSheet(BUTTON_STYLE)
        del_btn.clicked.connect(self.delete_selected)
        row.addWidget(del_btn)

        toggle_btn = QPushButton("Toggle Done")
        toggle_btn.setStyleSheet(BUTTON_STYLE)
        toggle_btn.clicked.connect(self.toggle_selected_done)
        row.addWidget(toggle_btn)

        layout.addLayout(row)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.data = load_json(self.FNAME, [])
        self.listw.clear()
        for item in self.data:
            text = item.get("text", "")
            done = item.get("done", False)
            lw = QListWidgetItem(text)
            if done:
                lw.setCheckState(Qt.Checked)
                lw.setForeground(Qt.gray)
            else:
                lw.setCheckState(Qt.Unchecked)
            self.listw.addItem(lw)

    def persist(self):
        # data sync from widget to storage (safest)
        # ensure length matches
        items = []
        for i in range(self.listw.count()):
            lw = self.listw.item(i)
            items.append(
                {"text": lw.text(), "done": lw.checkState() == Qt.Checked})
        save_json(self.FNAME, items)
        self.refresh()

    def add_task(self):
        txt = self.input.text().strip()
        if not txt:
            return
        self.data.append({"text": txt, "done": False})
        save_json(self.FNAME, self.data)
        self.input.clear()
        self.refresh()

    def get_selected_index(self):
        it = self.listw.currentItem()
        if not it:
            QMessageBox.information(
                self, "Select", "Please select an item first.")
            return None
        return self.listw.currentRow()

    def edit_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        cur = self.data[idx]["text"]
        new, ok = QInputDialog.getText(self, "Edit task", "Task:", text=cur)
        if ok and new.strip():
            self.data[idx]["text"] = new.strip()
            save_json(self.FNAME, self.data)
            self.refresh()

    def on_edit_item(self, item):
        idx = self.listw.row(item)
        cur = self.data[idx]["text"]
        new, ok = QInputDialog.getText(self, "Edit task", "Task:", text=cur)
        if ok and new.strip():
            self.data[idx]["text"] = new.strip()
            save_json(self.FNAME, self.data)
            self.refresh()

    def delete_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        confirm = QMessageBox.question(
            self, "Confirm", "Delete selected task?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.data.pop(idx)
            save_json(self.FNAME, self.data)
            self.refresh()

    def toggle_selected_done(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        self.data[idx]["done"] = not self.data[idx].get("done", False)
        save_json(self.FNAME, self.data)
        self.refresh()


# ---------------- NOTES ----------------
class NotesPage(BasePage):
    FNAME = "notes.json"

    def __init__(self, goto_page):
        super().__init__(goto_page)
        self.data = load_json(self.FNAME, {"content": ""})

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Notes")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.text = QTextEdit()
        self.text.setPlainText(self.data.get("content", ""))
        layout.addWidget(self.text)

        row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.clicked.connect(self.save_notes)
        row.addWidget(save_btn)

        export_btn = QPushButton("Export .txt")
        export_btn.setStyleSheet(BUTTON_STYLE)
        export_btn.clicked.connect(self.export_txt)
        row.addWidget(export_btn)

        layout.addLayout(row)
        self.setLayout(layout)

    def save_notes(self):
        self.data["content"] = self.text.toPlainText()
        save_json(self.FNAME, self.data)
        QMessageBox.information(self, "Saved", "Notes saved.")

    def export_txt(self):
        content = self.text.toPlainText()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export notes", "notes.txt", "Text files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                QMessageBox.information(
                    self, "Exported", f"Notes exported to:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export:\n{e}")


# ---------------- FLASHCARDS ----------------
class FlashcardsPage(BasePage):
    FNAME = "flashcards.json"

    def __init__(self, goto_page):
        super().__init__(goto_page)
        # list of {"front": str, "back": str}
        self.cards = load_json(self.FNAME, [])
        self.index = 0
        self.showing_front = True

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Flashcards")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.card_label = QLabel("")
        self.card_label.setWordWrap(True)
        self.card_label.setAlignment(Qt.AlignCenter)
        self.card_label.setMinimumHeight(120)
        layout.addWidget(self.card_label)

        btn_row = QHBoxLayout()
        flip_btn = QPushButton("Flip")
        flip_btn.setStyleSheet(BUTTON_STYLE)
        flip_btn.clicked.connect(self.flip)
        btn_row.addWidget(flip_btn)

        next_btn = QPushButton("Next →")
        next_btn.setStyleSheet(BUTTON_STYLE)
        next_btn.clicked.connect(self.next_card)
        btn_row.addWidget(next_btn)

        add_btn = QPushButton("Add Card")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_card)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit Card")
        edit_btn.setStyleSheet(BUTTON_STYLE)
        edit_btn.clicked.connect(self.edit_card)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("Delete Card")
        del_btn.setStyleSheet(BUTTON_STYLE)
        del_btn.clicked.connect(self.delete_card)
        btn_row.addWidget(del_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.cards = load_json(self.FNAME, [])
        if not self.cards:
            self.card_label.setText("No cards available.")
        else:
            self.index = self.index % len(self.cards)
            self.showing_front = True
            self.card_label.setText(self.cards[self.index].get("front", ""))

    def flip(self):
        if not self.cards:
            return
        self.showing_front = not self.showing_front
        side = "front" if self.showing_front else "back"
        self.card_label.setText(self.cards[self.index].get(side, ""))

    def next_card(self):
        if not self.cards:
            return
        self.index = (self.index + 1) % len(self.cards)
        self.showing_front = True
        self.card_label.setText(self.cards[self.index].get("front", ""))

    def add_card(self):
        front, ok1 = QInputDialog.getText(self, "Add Card", "Front:")
        if not ok1 or not front.strip():
            return
        back, ok2 = QInputDialog.getText(self, "Add Card", "Back:")
        if not ok2:
            return
        self.cards.append({"front": front.strip(), "back": back.strip()})
        save_json(self.FNAME, self.cards)
        self.refresh()

    def edit_card(self):
        if not self.cards:
            QMessageBox.information(
                self, "No cards", "There are no cards to edit.")
            return
        card = self.cards[self.index]
        front, ok1 = QInputDialog.getText(
            self, "Edit Card", "Front:", text=card.get("front", ""))
        if not ok1:
            return
        back, ok2 = QInputDialog.getText(
            self, "Edit Card", "Back:", text=card.get("back", ""))
        if not ok2:
            return
        self.cards[self.index] = {"front": front.strip(), "back": back.strip()}
        save_json(self.FNAME, self.cards)
        self.refresh()

    def delete_card(self):
        if not self.cards:
            return
        confirm = QMessageBox.question(
            self, "Delete", "Delete this card?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.cards.pop(self.index)
            save_json(self.FNAME, self.cards)
            self.refresh()


# ---------------- RESOURCES ----------------
class ResourcesPage(BasePage):
    FNAME = "resources.json"

    def __init__(self, goto_page):
        super().__init__(goto_page)
        self.data = load_json(self.FNAME, [])

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Study Resources")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self.open_selected)
        layout.addWidget(self.listw)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Paste resource link…")
        layout.addWidget(self.input)

        row = QHBoxLayout()
        add = QPushButton("Add")
        add.setStyleSheet(BUTTON_STYLE)
        add.clicked.connect(self.add_res)
        row.addWidget(add)

        del_btn = QPushButton("Delete Selected")
        del_btn.setStyleSheet(BUTTON_STYLE)
        del_btn.clicked.connect(self.delete_selected)
        row.addWidget(del_btn)

        layout.addLayout(row)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.data = load_json(self.FNAME, [])
        self.listw.clear()
        for link in self.data:
            self.listw.addItem(link)

    def add_res(self):
        link = self.input.text().strip()
        if not link:
            return
        self.data.append(link)
        save_json(self.FNAME, self.data)
        self.input.clear()
        self.refresh()

    def get_selected_index(self):
        it = self.listw.currentItem()
        if not it:
            QMessageBox.information(
                self, "Select", "Please select a resource.")
            return None
        return self.listw.currentRow()

    def open_selected(self, item=None):
        if item:
            url = item.text()
        else:
            idx = self.get_selected_index()
            if idx is None:
                return
            url = self.data[idx]
        QDesktopServices.openUrl(QUrl(url))

    def delete_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        confirm = QMessageBox.question(
            self, "Delete", "Delete selected resource?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.data.pop(idx)
            save_json(self.FNAME, self.data)
            self.refresh()


# ---------------- SCHEDULE ----------------
class SchedulePage(BasePage):
    FNAME = "schedule.json"

    def __init__(self, goto_page):
        super().__init__(goto_page)
        self.data = load_json(self.FNAME, [])

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Schedule")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self.edit_selected)
        layout.addWidget(self.listw)

        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "Add schedule entry… (e.g., Mon 5pm: Math)")
        layout.addWidget(self.input)

        row = QHBoxLayout()
        add = QPushButton("Add")
        add.setStyleSheet(BUTTON_STYLE)
        add.clicked.connect(self.add_entry)
        row.addWidget(add)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.setStyleSheet(BUTTON_STYLE)
        edit_btn.clicked.connect(self.edit_selected)
        row.addWidget(edit_btn)

        del_btn = QPushButton("Delete Selected")
        del_btn.setStyleSheet(BUTTON_STYLE)
        del_btn.clicked.connect(self.delete_selected)
        row.addWidget(del_btn)

        layout.addLayout(row)
        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.data = load_json(self.FNAME, [])
        self.listw.clear()
        for e in self.data:
            self.listw.addItem(e)

    def add_entry(self):
        e = self.input.text().strip()
        if not e:
            return
        self.data.append(e)
        save_json(self.FNAME, self.data)
        self.input.clear()
        self.refresh()

    def get_selected_index(self):
        it = self.listw.currentItem()
        if not it:
            QMessageBox.information(self, "Select", "Please select an entry.")
            return None
        return self.listw.currentRow()

    def edit_selected(self, item=None):
        if item is not None:
            idx = self.listw.row(item)
            cur = self.data[idx]
        else:
            idx = self.get_selected_index()
            if idx is None:
                return
            cur = self.data[idx]
        new, ok = QInputDialog.getText(self, "Edit entry", "Entry:", text=cur)
        if ok and new.strip():
            self.data[idx] = new.strip()
            save_json(self.FNAME, self.data)
            self.refresh()

    def delete_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        confirm = QMessageBox.question(
            self, "Delete", "Delete selected entry?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.data.pop(idx)
            save_json(self.FNAME, self.data)
            self.refresh()


# ---------------- CLIPART PAGE ----------------
class ClipartPage(BasePage):
    def __init__(self, goto_page):
        super().__init__(goto_page)
        layout = QVBoxLayout()
        self.add_back(layout)

        title = QLabel("Clipart Generator")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Upload an image and open a clipart/vectorizer website.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn = QPushButton("Upload & Open Vectorizer")
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(self.pick_file)
        layout.addWidget(btn)

        self.setLayout(layout)

    def pick_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
        if file:
            # here we open a web-based vectorizer; you could upload programmatically later
            QDesktopServices.openUrl(QUrl("https://vectorizer.ai/"))


# ---------------- TIMER PAGE ----------------
class TimerPage(BasePage):
    def __init__(self, goto_page):
        super().__init__(goto_page)
        layout = QVBoxLayout()
        self.add_back(layout)

        title = QLabel("Focus Timer")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px;")
        layout.addWidget(self.timer_label)

        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText(
            "Duration in minutes (default 25)")
        layout.addWidget(self.duration_input)

        row = QHBoxLayout()
        start = QPushButton("Start")
        start.setStyleSheet(BUTTON_STYLE)
        start.clicked.connect(self.start_timer)
        row.addWidget(start)

        reset = QPushButton("Reset")
        reset.setStyleSheet(BUTTON_STYLE)
        reset.clicked.connect(self.reset_timer)
        row.addWidget(reset)

        layout.addLayout(row)
        self.setLayout(layout)

        self.time_left = 25 * 60
        self.running = False
        self.qtimer = QTimer()
        self.qtimer.timeout.connect(self.tick)

    def start_timer(self):
        if not self.running:
            # read minutes
            text = self.duration_input.text().strip()
            if text:
                try:
                    m = int(text)
                    self.time_left = max(1, m) * 60
                except Exception:
                    QMessageBox.warning(
                        self, "Invalid", "Please enter a number of minutes.")
                    return
            else:
                self.time_left = 25 * 60
            self.running = True
            self.qtimer.start(1000)
            self.update_label()

    def reset_timer(self):
        self.running = False
        self.qtimer.stop()
        self.time_left = 25 * 60
        self.update_label()

    def tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.update_label()
        else:
            self.qtimer.stop()
            self.running = False
            self.timer_label.setText("Done!")

    def update_label(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
