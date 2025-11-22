# pages.py
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QCalendarWidget,
    QGraphicsOpacityEffect, QGridLayout
)
from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QPropertyAnimation,
    pyqtProperty, QRectF
)
from PyQt5.QtGui import (
    QDesktopServices, QIcon, QPixmap, QPainter,
    QColor, QPen, QFont
)

from data_manager import (
    load_json, save_json,
    load_users, save_users,
    load_settings, save_settings
)

# ---------- SHARED STYLES (NO COLORS HERE; THEMES HANDLE COLORS) ----------

CARD_STYLE = """
    border-radius: 18px;
    padding: 18px;
"""

BUTTON_STYLE = """
    border-radius: 14px;
    padding: 7px 16px;
"""

TITLE_STYLE = "font-size: 22px; font-weight: 600; margin-bottom: 8px;"
TEXT_STYLE = "font-size: 14px;"


def make_open_window_icon(size=20):
    """Tiny drawn icon for 'open in new window'."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # square outline
    p.setPen(QColor(80, 80, 80))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(3, 3, size - 6, size - 6, 3, 3)

    # plus sign
    p.setPen(QColor(80, 80, 80))
    mid = size // 2
    p.drawLine(mid, 5, mid, size - 5)
    p.drawLine(5, mid, size - 5, mid)

    p.end()
    return QIcon(pix)


# ---------------------------- CIRCULAR PROGRESS WIDGET ----------------------------

class CircularProgress(QWidget):
    """
    Cute pastel circular progress (0–100%) with smooth animation.
    """
    def __init__(self, size=110, thickness=10, color="#f29ac5", bg="#e8d8e2"):
        super().__init__()
        self._value = 0
        self.size = size
        self.thickness = thickness
        self.progress_color = QColor(color)
        self.bg_color = QColor(bg)

        self.setMinimumSize(size, size)

        self.anim = QPropertyAnimation(self, b"value")
        self.anim.setDuration(400)

    def getValue(self):
        return self._value

    def setValue(self, v):
        v = max(0, min(100, int(v)))
        self._value = v
        self.update()

    value = pyqtProperty(int, fget=getValue, fset=setValue)

    def setValueAnimated(self, v):
        v = max(0, min(100, int(v)))
        self.anim.stop()
        self.anim.setStartValue(self._value)
        self.anim.setEndValue(v)
        self.anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(
            self.thickness / 2,
            self.thickness / 2,
            self.size - self.thickness,
            self.size - self.thickness,
        )

        # background circle
        pen = QPen(self.bg_color, self.thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

        # progress arc
        pen.setColor(self.progress_color)
        painter.setPen(pen)
        angle = int(360 * (self._value / 100))
        painter.drawArc(rect, -90 * 16, -angle * 16)

        # text inside (%)
        painter.setPen(self.progress_color.darker(130))
        painter.setFont(QFont("Avenir", 14, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self._value}%")


# ================= BASE PAGE =================

class BasePage(QWidget):
    def __init__(self, goto_page, standalone=False):
        super().__init__()
        self.goto_page = goto_page
        self.standalone = standalone

    def add_back(self, layout: QVBoxLayout):
        if self.goto_page is not None and not self.standalone:
            back = QPushButton("← Back to Dashboard")
            back.setStyleSheet(BUTTON_STYLE)
            back.clicked.connect(lambda: self.goto_page("dashboard"))
            layout.addWidget(back)


# ================= LOGIN PAGE =================

class LoginPage(QWidget):
    def __init__(self, goto_page, on_login):
        super().__init__()
        self.goto_page = goto_page
        self.on_login = on_login

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Study Helper")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600; margin-bottom: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("Log in or sign up to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        layout.addWidget(subtitle)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        row = QHBoxLayout()
        login_btn = QPushButton("Log in")
        signup_btn = QPushButton("Sign up")
        login_btn.setStyleSheet(BUTTON_STYLE)
        signup_btn.setStyleSheet(BUTTON_STYLE)
        login_btn.clicked.connect(self.handle_login)
        signup_btn.clicked.connect(self.handle_signup)
        row.addWidget(login_btn)
        row.addWidget(signup_btn)
        layout.addLayout(row)

        self.setLayout(layout)

        settings = load_settings()
        last = settings.get("last_user")
        if last:
            self.username_input.setText(last)

    def _get_credentials(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Missing info", "Please enter both username and password.")
            return None, None
        return username, password

    def handle_login(self):
        username, password = self._get_credentials()
        if not username:
            return

        users = load_users()
        if username not in users:
            QMessageBox.warning(self, "User not found", "This username does not exist. Try signing up.")
            return
        if users[username] != password:
            QMessageBox.warning(self, "Wrong password", "The password you entered is incorrect.")
            return

        self.finish_login(username)

    def handle_signup(self):
        username, password = self._get_credentials()
        if not username:
            return

        users = load_users()
        if username in users:
            QMessageBox.warning(self, "User exists", "This username is already taken. Try logging in.")
            return

        users[username] = password
        save_users(users)
        QMessageBox.information(self, "Account created", "Your account has been created.")
        self.finish_login(username)

    def finish_login(self, username):
        settings = load_settings()
        settings["last_user"] = username
        save_settings(settings)

        self.on_login(username)
        self.goto_page("dashboard")


# ================= DASHBOARD =================

class DashboardPage(QWidget):
    def __init__(self, goto_page, open_window, get_user, logout):
        super().__init__()
        self.goto_page = goto_page
        self.open_window = open_window
        self.get_user = get_user
        self.logout = logout

        main = QVBoxLayout()
        main.setAlignment(Qt.AlignTop)

        # top row: title + logout
        top_row = QHBoxLayout()
        title = QLabel("Study Helper Dashboard")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        top_row.addWidget(title)

        top_row.addStretch()

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(BUTTON_STYLE + "font-size: 12px; padding: 4px 10px;")
        logout_btn.clicked.connect(self.logout)
        top_row.addWidget(logout_btn)

        main.addLayout(top_row)

        # user label
        self.user_label = QLabel("")
        self.user_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.user_label.setStyleSheet("margin-bottom: 10px; color: #666666;")
        main.addWidget(self.user_label)

        # ----- Overview (donut progress) -----
        overview_title = QLabel("Overview")
        overview_title.setStyleSheet("font-size: 18px; font-weight: 600; margin-top: 8px;")
        main.addWidget(overview_title)

        stats_row = QHBoxLayout()

        # Tasks card
        self.todo_circle = CircularProgress(size=110, color="#f29ac5", bg="#f0d1e3")
        todo_card = QWidget()
        todo_card.setObjectName("card")
        todo_card.setStyleSheet(CARD_STYLE)
        todo_layout = QVBoxLayout()
        todo_layout.setContentsMargins(10, 10, 10, 10)
        todo_layout.setAlignment(Qt.AlignCenter)
        todo_card.setLayout(todo_layout)
        todo_layout.addWidget(self.todo_circle, alignment=Qt.AlignCenter)

        todo_title = QLabel("Tasks Done")
        todo_title.setAlignment(Qt.AlignCenter)
        todo_title.setStyleSheet("font-weight: 600;")
        todo_layout.addWidget(todo_title)

        self.todo_label = QLabel("0 / 0")
        self.todo_label.setAlignment(Qt.AlignCenter)
        todo_layout.addWidget(self.todo_label)

        # Flashcards card
        self.flash_circle = CircularProgress(size=110, color="#86a9ff", bg="#c7d6ff")
        flash_card = QWidget()
        flash_card.setObjectName("card")
        flash_card.setStyleSheet(CARD_STYLE)
        flash_layout = QVBoxLayout()
        flash_layout.setContentsMargins(10, 10, 10, 10)
        flash_layout.setAlignment(Qt.AlignCenter)
        flash_card.setLayout(flash_layout)
        flash_layout.addWidget(self.flash_circle, alignment=Qt.AlignCenter)

        flash_title = QLabel("Flashcards Known")
        flash_title.setAlignment(Qt.AlignCenter)
        flash_title.setStyleSheet("font-weight: 600;")
        flash_layout.addWidget(flash_title)

        self.flash_label = QLabel("0 / 0")
        self.flash_label.setAlignment(Qt.AlignCenter)
        flash_layout.addWidget(self.flash_label)

        # Notes card
        self.notes_circle = CircularProgress(size=110, color="#8ed9a5", bg="#bfe6c9")
        notes_card = QWidget()
        notes_card.setObjectName("card")
        notes_card.setStyleSheet(CARD_STYLE)
        notes_layout = QVBoxLayout()
        notes_layout.setContentsMargins(10, 10, 10, 10)
        notes_layout.setAlignment(Qt.AlignCenter)
        notes_card.setLayout(notes_layout)
        notes_layout.addWidget(self.notes_circle, alignment=Qt.AlignCenter)

        notes_title = QLabel("Notes Filled")
        notes_title.setAlignment(Qt.AlignCenter)
        notes_title.setStyleSheet("font-weight: 600;")
        notes_layout.addWidget(notes_title)

        self.notes_label = QLabel("0 / 0 folders")
        self.notes_label.setAlignment(Qt.AlignCenter)
        notes_layout.addWidget(self.notes_label)

        stats_row.addWidget(todo_card)
        stats_row.addWidget(flash_card)
        stats_row.addWidget(notes_card)

        main.addLayout(stats_row)

        # ----- Tools -----
        tools_title = QLabel("Your Tools")
        tools_title.setStyleSheet("font-size: 18px; font-weight: 600; margin-top: 12px;")
        main.addWidget(tools_title)

        grid = QGridLayout()
        grid.setSpacing(20)

        tiles = [
            ("To-Do List", "todo"),
            ("Notes", "notes"),
            ("Flashcards", "flashcards"),
            ("Resources", "resources"),
            ("Schedule", "schedule"),
            ("Focus Timer", "timer"),
        ]

        icon = make_open_window_icon()

        for i, (label, key) in enumerate(tiles):
            row = i // 3
            col = i % 3

            card = QWidget()
            card.setObjectName("card")
            card.setStyleSheet(CARD_STYLE)
            v = QVBoxLayout()
            v.setContentsMargins(10, 10, 10, 10)
            card.setLayout(v)

            main_btn = QPushButton(label)
            main_btn.setStyleSheet(BUTTON_STYLE + "font-size: 17px;")
            main_btn.clicked.connect(lambda _, p=key: self.goto_page(p))
            v.addWidget(main_btn)

            open_btn = QPushButton()
            open_btn.setIcon(icon)
            open_btn.setToolTip("Open in new window")
            open_btn.setFixedSize(26, 26)
            open_btn.setStyleSheet("border: none; background: transparent;")
            open_btn.clicked.connect(lambda _, p=key: self.open_window(p))
            v.addWidget(open_btn, alignment=Qt.AlignRight)

            grid.addWidget(card, row, col)

        main.addLayout(grid)
        main.addStretch(1)
        self.setLayout(main)

        self.refresh()

    def refresh(self):
        # user label
        user = self.get_user()
        if user:
            self.user_label.setText("Logged in as: " + user)
        else:
            self.user_label.setText("Not logged in")

        # To-do progress
        todos = load_json("todos.json", [])
        total = len(todos)
        done = sum(1 for t in todos if t.get("done"))

        percent = int((done / total) * 100) if total else 0
        self.todo_circle.setValueAnimated(percent)
        self.todo_label.setText(f"{done} / {total} tasks")

        # Flashcards progress
        cards = load_json("flashcards.json", [])
        total_cards = len(cards)
        known_cards = sum(1 for c in cards if c.get("known"))

        percent_fc = int((known_cards / total_cards) * 100) if total_cards else 0
        self.flash_circle.setValueAnimated(percent_fc)
        self.flash_label.setText(f"{known_cards} / {total_cards} cards")

        # Notes progress: count folders that have non-empty content
        notes_data = load_json("notes.json", {"folders": {}})
        folders = {}
        if isinstance(notes_data, dict):
            if "folders" in notes_data and isinstance(notes_data["folders"], dict):
                folders = notes_data["folders"]
            elif "content" in notes_data:
                # old style single content
                folders = {"Notes": {"content": notes_data.get("content", "")}}

        total_folders = len(folders)
        filled_folders = 0
        for info in folders.values():
            content = ""
            if isinstance(info, dict):
                content = info.get("content", "")
            elif isinstance(info, str):
                content = info
            if str(content).strip():
                filled_folders += 1

        percent_notes = int((filled_folders / total_folders) * 100) if total_folders else 0
        self.notes_circle.setValueAnimated(percent_notes)
        self.notes_label.setText(f"{filled_folders} / {total_folders} folders")


# ================= TODO PAGE (priority + done/pending) =================

class TodoPage(BasePage):
    FNAME = "todos.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        self.data = load_json(self.FNAME, [])  # list of {text, priority, done}

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("To-Do List")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        filter_row = QHBoxLayout()
        filter_label = QLabel("Priority filter:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "High", "Medium", "Low"])
        self.filter_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.filter_combo)
        layout.addLayout(filter_row)

        lists_row = QHBoxLayout()
        self.pending_list = QListWidget()
        self.done_list = QListWidget()
        lists_row.addWidget(self.pending_list)
        lists_row.addWidget(self.done_list)
        layout.addLayout(lists_row)

        input_row = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New task…")
        self.priority_select = QComboBox()
        self.priority_select.addItems(["High", "Medium", "Low"])
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_task)
        input_row.addWidget(self.task_input)
        input_row.addWidget(self.priority_select)
        input_row.addWidget(add_btn)
        layout.addLayout(input_row)

        actions_row = QHBoxLayout()
        to_done = QPushButton("Pending → Done")
        to_todo = QPushButton("Done → Pending")
        delete_btn = QPushButton("Delete selected")
        for b in (to_done, to_todo, delete_btn):
            b.setStyleSheet(BUTTON_STYLE)
        to_done.clicked.connect(self.pending_to_done)
        to_todo.clicked.connect(self.done_to_pending)
        delete_btn.clicked.connect(self.delete_selected)
        actions_row.addWidget(to_done)
        actions_row.addWidget(to_todo)
        actions_row.addWidget(delete_btn)
        layout.addLayout(actions_row)

        self.setLayout(layout)
        self.refresh()

    def _load_data(self):
        self.data = load_json(self.FNAME, [])

    def _save_data(self):
        save_json(self.FNAME, self.data)

    def refresh(self):
        self._load_data()
        self.pending_list.clear()
        self.done_list.clear()

        filt = self.filter_combo.currentText()
        for item in self.data:
            if filt != "All" and item.get("priority") != filt:
                continue
            label = f"[{item.get('priority', 'Low')}] {item.get('text', '')}"
            lw = QListWidgetItem(label)
            if item.get("done"):
                self.done_list.addItem(lw)
            else:
                self.pending_list.addItem(lw)

    def add_task(self):
        txt = self.task_input.text().strip()
        if not txt:
            QMessageBox.information(self, "Empty task", "Please type a task before adding.")
            return
        priority = self.priority_select.currentText()
        self.data.append({"text": txt, "priority": priority, "done": False})
        self._save_data()
        self.task_input.clear()
        self.refresh()

    def _find_item_index(self, text, done_flag):
        for i, item in enumerate(self.data):
            if item.get("done") == done_flag:
                label = f"[{item.get('priority', 'Low')}] {item.get('text', '')}"
                if label == text:
                    return i
        return None

    def pending_to_done(self):
        item = self.pending_list.currentItem()
        if not item:
            QMessageBox.information(self, "No task selected", "Choose a task in the left list.")
            return
        idx = self._find_item_index(item.text(), False)
        if idx is not None:
            self.data[idx]["done"] = True
            self._save_data()
            self.refresh()

    def done_to_pending(self):
        item = self.done_list.currentItem()
        if not item:
            QMessageBox.information(self, "No task selected", "Choose a task in the right list.")
            return
        idx = self._find_item_index(item.text(), True)
        if idx is not None:
            self.data[idx]["done"] = False
            self._save_data()
            self.refresh()

    def delete_selected(self):
        item = self.pending_list.currentItem() or self.done_list.currentItem()
        if not item:
            QMessageBox.information(self, "No task selected", "Pick a task to delete.")
            return
        idx = self._find_item_index(item.text(), False)
        if idx is None:
            idx = self._find_item_index(item.text(), True)
        if idx is not None:
            del self.data[idx]
            self._save_data()
            self.refresh()


# ================= NOTES PAGE (folders / subjects) =================

class NotesPage(BasePage):
    FNAME = "notes.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        self.data = load_json(self.FNAME, {"folders": {}})
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Notes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        main_row = QHBoxLayout()

        # left: folders
        left_col = QVBoxLayout()
        folder_label = QLabel("Folders / Subjects")
        left_col.addWidget(folder_label)

        self.folder_list = QListWidget()
        self.folder_list.currentTextChanged.connect(self.select_folder)
        left_col.addWidget(self.folder_list)

        add_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("New folder / subject…")
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_folder)
        add_row.addWidget(self.folder_input)
        add_row.addWidget(add_btn)
        left_col.addLayout(add_row)

        left_widget = QWidget()
        left_widget.setLayout(left_col)
        main_row.addWidget(left_widget, 1)

        # right: note area
        right_col = QVBoxLayout()
        self.folder_title = QLabel("No folder selected")
        right_col.addWidget(self.folder_title)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("font-size: 16px;")
        right_col.addWidget(self.text_edit)

        save_btn = QPushButton("Save notes")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.clicked.connect(self.save_notes)
        right_col.addWidget(save_btn)

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        main_row.addWidget(right_widget, 2)

        layout.addLayout(main_row)
        self.setLayout(layout)
        self.refresh_folders()

    def refresh_folders(self):
        self.folder_list.clear()
        for name in sorted(self.data["folders"].keys()):
            self.folder_list.addItem(name)

    def add_folder(self):
        name = self.folder_input.text().strip()
        if not name:
            QMessageBox.information(self, "No name", "Type a folder/subject name.")
            return
        if name in self.data["folders"]:
            QMessageBox.information(self, "Exists", "That folder already exists.")
            return
        self.data["folders"][name] = {"content": ""}
        save_json(self.FNAME, self.data)
        self.folder_input.clear()
        self.refresh_folders()

    def select_folder(self, name):
        if not name:
            return
        self.current_folder = name
        self.folder_title.setText("Notes — " + name)
        content = self.data["folders"].get(name, {}).get("content", "")
        self.text_edit.setPlainText(content)

    def save_notes(self):
        if not self.current_folder:
            QMessageBox.information(self, "No folder", "Select or create a folder first.")
            return
        self.data["folders"][self.current_folder]["content"] = self.text_edit.toPlainText()
        save_json(self.FNAME, self.data)
        QMessageBox.information(self, "Saved", "Notes saved.")


# ================= FLASHCARDS (animated, known tracking) =================

class FlashcardsPage(BasePage):
    FNAME = "flashcards.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        self.cards = load_json(self.FNAME, [])
        changed = False
        for c in self.cards:
            if "known" not in c:
                c["known"] = False
                changed = True
        if changed:
            save_json(self.FNAME, self.cards)

        self.index = 0
        self.show_front = True

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Flashcards")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        self.card_label = QLabel("")
        self.card_label.setAlignment(Qt.AlignCenter)
        self.card_label.setWordWrap(True)
        self.card_label.setMinimumHeight(150)
        self.card_label.setObjectName("Flashcard")
        self.card_label.setStyleSheet(CARD_STYLE + "font-size: 18px;")
        layout.addWidget(self.card_label)

        # opacity effect for animation
        self.effect = QGraphicsOpacityEffect()
        self.card_label.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(200)

        self.counter_label = QLabel("")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)

        btn_row = QHBoxLayout()
        flip_btn = QPushButton("Flip")
        next_btn = QPushButton("Next")
        known_btn = QPushButton("Mark Known")
        delete_btn = QPushButton("Delete")
        for b in (flip_btn, next_btn, known_btn, delete_btn):
            b.setStyleSheet(BUTTON_STYLE)
        flip_btn.clicked.connect(self.flip)
        next_btn.clicked.connect(self.next_card)
        known_btn.clicked.connect(self.mark_known)
        delete_btn.clicked.connect(self.delete_current)
        btn_row.addWidget(flip_btn)
        btn_row.addWidget(next_btn)
        btn_row.addWidget(known_btn)
        btn_row.addWidget(delete_btn)
        layout.addLayout(btn_row)

        add_row = QHBoxLayout()
        self.front_input = QLineEdit()
        self.front_input.setPlaceholderText("Front (question)…")
        self.back_input = QLineEdit()
        self.back_input.setPlaceholderText("Back (answer)…")
        add_btn = QPushButton("Add card")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_card)
        add_row.addWidget(self.front_input)
        add_row.addWidget(self.back_input)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.setLayout(layout)
        self.refresh()

    def _play_flip_anim(self):
        self.anim.stop()
        self.effect.setOpacity(0.0)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def refresh(self):
        self.cards = load_json(self.FNAME, [])
        for c in self.cards:
            if "known" not in c:
                c["known"] = False
        save_json(self.FNAME, self.cards)

        if not self.cards:
            self.card_label.setText("No cards yet. Add one below.")
            self.counter_label.setText("")
            self.index = 0
            self.show_front = True
            return

        self.index %= len(self.cards)
        self.show_front = True
        self.card_label.setText(self.cards[self.index].get("front", ""))
        self.counter_label.setText(f"Card {self.index+1} / {len(self.cards)}")
        self._play_flip_anim()

    def flip(self):
        if not self.cards:
            return
        self.show_front = not self.show_front
        side = "front" if self.show_front else "back"
        self.card_label.setText(self.cards[self.index].get(side, ""))
        self._play_flip_anim()

    def next_card(self):
        if not self.cards:
            return
        self.index = (self.index + 1) % len(self.cards)
        self.show_front = True
        self.card_label.setText(self.cards[self.index].get("front", ""))
        self.counter_label.setText(f"Card {self.index+1} / {len(self.cards)}")
        self._play_flip_anim()

    def add_card(self):
        front = self.front_input.text().strip()
        back = self.back_input.text().strip()
        if not front or not back:
            QMessageBox.information(self, "Missing", "Please fill in both front and back.")
            return
        self.cards.append({"front": front, "back": back, "known": False})
        save_json(self.FNAME, self.cards)
        self.front_input.clear()
        self.back_input.clear()
        self.refresh()

    def delete_current(self):
        if not self.cards:
            QMessageBox.information(self, "No cards", "There is no card to delete.")
            return
        del self.cards[self.index]
        save_json(self.FNAME, self.cards)
        self.refresh()

    def mark_known(self):
        if not self.cards:
            return
        self.cards[self.index]["known"] = True
        save_json(self.FNAME, self.cards)
        self.next_card()


# ================= RESOURCES =================

class ResourcesPage(BasePage):
    FNAME = "resources.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        self.data = load_json(self.FNAME, [])

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Study Resources")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self.open_link)
        layout.addWidget(self.listw)

        row = QHBoxLayout()
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Paste a link…")
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_link)
        row.addWidget(self.link_input)
        row.addWidget(add_btn)
        layout.addLayout(row)

        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.data = load_json(self.FNAME, [])
        self.listw.clear()
        for url in self.data:
            self.listw.addItem(url)

    def add_link(self):
        url = self.link_input.text().strip()
        if not url:
            QMessageBox.information(self, "Empty link", "Paste a valid URL before adding.")
            return
        self.data.append(url)
        save_json(self.FNAME, self.data)
        self.link_input.clear()
        self.refresh()

    def open_link(self, item):
        QDesktopServices.openUrl(QUrl(item.text()))


# ================= SCHEDULE (calendar-based) =================

class SchedulePage(BasePage):
    FNAME = "schedule.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        raw = load_json(self.FNAME, {})
        # Backward compatibility: old list -> store under "__all__"
        if isinstance(raw, list):
            self.data = {"__all__": raw}
        else:
            self.data = raw

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Schedule")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.refresh_for_selected_date)
        layout.addWidget(self.calendar)

        self.entries_label = QLabel("")
        layout.addWidget(self.entries_label)

        self.listw = QListWidget()
        layout.addWidget(self.listw)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add entry for selected date…")
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_entry)
        row.addWidget(self.input)
        row.addWidget(add_btn)
        layout.addLayout(row)

        self.setLayout(layout)
        self.refresh_for_selected_date()

    def _date_key(self):
        d = self.calendar.selectedDate()
        return d.toString("yyyy-MM-dd")

    def refresh_for_selected_date(self):
        self.listw.clear()
        key = self._date_key()
        entries = self.data.get(key, [])
        self.entries_label.setText(f"Entries for {key}:")
        for e in entries:
            self.listw.addItem(e)

        # show legacy entries if any (pre-calendar data)
        legacy = self.data.get("__all__")
        if legacy:
            self.listw.addItem("---- Legacy entries ----")
            for e in legacy:
                self.listw.addItem(e)

    def add_entry(self):
        txt = self.input.text().strip()
        if not txt:
            QMessageBox.information(self, "Empty entry", "Write something before adding.")
            return
        key = self._date_key()
        self.data.setdefault(key, []).append(txt)
        save_json(self.FNAME, self.data)
        self.input.clear()
        self.refresh_for_selected_date()


# ================= TIMER (animated flip-style) =================

class TimerPage(BasePage):
    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)

        self.time_left = 25 * 60
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Focus Timer")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setObjectName("BigNumber")
        self.time_label.setStyleSheet("""
            font-size: 72px;
            font-weight: 600;
            padding: 24px 32px;
            border-radius: 22px;
            background-color: rgba(0, 0, 0, 0.06);
            letter-spacing: 6px;
        """)
        self.time_label.setMinimumHeight(180)
        layout.addWidget(self.time_label)

        # opacity effect for flip-ish animation
        self.time_effect = QGraphicsOpacityEffect()
        self.time_label.setGraphicsEffect(self.time_effect)
        self.time_anim = QPropertyAnimation(self.time_effect, b"opacity")
        self.time_anim.setDuration(180)

        self.minutes_input = QLineEdit()
        self.minutes_input.setPlaceholderText("Minutes (default 25)")
        layout.addWidget(self.minutes_input)

        row = QHBoxLayout()
        start_btn = QPushButton("Start")
        stop_btn = QPushButton("Stop")
        reset_btn = QPushButton("Reset")
        for b in (start_btn, stop_btn, reset_btn):
            b.setStyleSheet(BUTTON_STYLE)
        start_btn.clicked.connect(self.start_timer)
        stop_btn.clicked.connect(self.stop_timer)
        reset_btn.clicked.connect(self.reset_timer)
        row.addWidget(start_btn)
        row.addWidget(stop_btn)
        row.addWidget(reset_btn)
        layout.addLayout(row)

        self.setLayout(layout)
        self.update_label()

    def _play_tick_anim(self):
        self.time_anim.stop()
        self.time_effect.setOpacity(0.3)
        self.time_anim.setStartValue(0.3)
        self.time_anim.setEndValue(1.0)
        self.time_anim.start()

    def start_timer(self):
        if self.running:
            return
        text = self.minutes_input.text().strip()
        if text:
            try:
                mins = max(1, int(text))
                self.time_left = mins * 60
            except ValueError:
                QMessageBox.information(self, "Invalid minutes", "Please enter a whole number.")
                return
        self.running = True
        self.timer.start(1000)
        self.update_label()
        self._play_tick_anim()

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
            self.time_label.setText("00:00")
            return
        self.time_left -= 1
        self.update_label()
        self._play_tick_anim()

    def update_label(self):
        mins = self.time_left // 60
        secs = self.time_left % 60
        self.time_label.setText(f"{mins:02d}:{secs:02d}")
