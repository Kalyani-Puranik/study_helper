from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QMessageBox,
    QCalendarWidget,
    QGraphicsOpacityEffect,
    QGridLayout,
    QFrame,
    QInputDialog,
)
from PyQt5.QtCore import (
    Qt,
    QUrl,
    QTimer,
    QPropertyAnimation,
    QRectF,
    QDate,
    pyqtProperty,
    QEasingCurve,
)
from PyQt5.QtGui import (
    QDesktopServices,
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QFont,
)

from data_manager import (
    load_json,
    save_json,
    load_users,
    save_users,
    load_settings,
    save_settings,
)

# ---------- Shared styles (colors come from theme stylesheet) ----------

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

    p.setPen(QColor(80, 80, 80))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(3, 3, size - 6, size - 6, 3, 3)

    mid = size // 2
    p.drawLine(mid, 5, mid, size - 5)
    p.drawLine(5, mid, size - 5, mid)

    p.end()
    return QIcon(pix)


# ---------- Helpers for legacy data ----------

def normalize_notes_data(data):
    """
    Normalise any previous notes.json format into:
    {
        "folders": {
            "Subject": {
                "complete": bool,
                "units": {
                    "Unit name": {"content": "..."}
                }
            }
        }
    }
    """
    if not isinstance(data, dict):
        data = {}
    folders = data.get("folders", {})

    # If folders is a list of names, convert
    if isinstance(folders, list):
        new_f = {}
        for f in folders:
            if isinstance(f, str):
                new_f[f] = {"complete": False, "units": {}}
        folders = new_f

    if not isinstance(folders, dict):
        folders = {}

    changed = False
    for name, val in list(folders.items()):
        if isinstance(val, dict):
            # Old shape: {"content": "..."}
            if "units" not in val and "content" in val:
                content = val.get("content", "")
                folders[name] = {
                    "complete": False,
                    "units": {"General": {"content": content}},
                }
                changed = True
            else:
                if "complete" not in val:
                    val["complete"] = False
                    changed = True
                if "units" not in val or not isinstance(val["units"], dict):
                    val["units"] = {}
                    changed = True
        else:
            folders[name] = {"complete": False, "units": {}}
            changed = True

    data["folders"] = folders
    if changed:
        save_json("notes.json", data)
    return data


def normalize_schedule_data(raw):
    """
    Legacy schedule.json might be a list; new is a dict.
    """
    if isinstance(raw, list):
        return {"__all__": raw}
    if not isinstance(raw, dict):
        return {}
    return raw


# ================== Multi-ring circular progress ==================


class MultiRingProgress(QWidget):
    """
    Concentric animated rings in Pinterest-style, using theme accent colours.

    - Expects a callback get_theme_colors() -> current theme dict
    - Use set_items([("Tasks", 0.4), ("Flashcards", 0.6), ("Notes", 0.2)])
    """

    def __init__(self, get_theme_colors, parent=None):
        super().__init__(parent)
        self._get_theme_colors = get_theme_colors
        self._items = []  # list of (label, ratio)
        self._anim_progress = 0.0

        self._animation = QPropertyAnimation(self, b"animProgress")
        self._animation.setDuration(900)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.setMinimumSize(260, 260)

    def get_anim_progress(self):
        return self._anim_progress

    def set_anim_progress(self, value):
        self._anim_progress = float(value)
        self.update()

    animProgress = pyqtProperty(float, fget=get_anim_progress, fset=set_anim_progress)

    def set_items(self, items):
        """
        items: list of (label, ratio 0..1)
        """
        self._items = list(items)
        self._animation.stop()
        self._anim_progress = 0.0
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def theme_changed(self):
        """Call when theme updates."""
        self.update()

    def _theme_colors_for_rings(self):
        colors = self._get_theme_colors()
        accent = QColor(colors.get("accent", "#cccccc"))
        hover = QColor(colors.get("accent_hover", colors.get("accent", "#bbbbbb")))
        button_bg = QColor(colors.get("button_bg", colors.get("accent", "#bbbbbb")))

        # Three shades: outer = darker, mid = base, inner = lighter / hover
        outer = accent.darker(120)
        mid = button_bg
        inner = hover.lighter(115)
        return [outer, mid, inner]

    def paintEvent(self, event):
        if not self._items:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        size = min(self.width(), self.height())
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        ring_thickness = size * 0.08
        spacing = size * 0.02
        max_radius = (size / 2.0) - ring_thickness - 8

        # Background rings & progress rings
        ring_colors = self._theme_colors_for_rings()
        bg_color = self.palette().window().color()
        text_color = self.palette().text().color()

        base_rect = QRectF(
            center_x - max_radius,
            center_y - max_radius,
            2 * max_radius,
            2 * max_radius,
        )

        for idx, item in enumerate(self._items):
            label, ratio = item
            if ratio < 0.0:
                ratio = 0.0
            if ratio > 1.0:
                ratio = 1.0

            # radii from outside to inside
            offset = idx * (ring_thickness + spacing)
            rect = QRectF(
                base_rect.left() + offset,
                base_rect.top() + offset,
                base_rect.width() - 2 * offset,
                base_rect.height() - 2 * offset,
            )

            # background ring
            p.setPen(QPen(bg_color.lighter(130), ring_thickness))
            p.setBrush(Qt.NoBrush)
            p.drawArc(rect, 0, 360 * 16)

            # progress ring
            span_angle = 360.0 * ratio * self._anim_progress
            color = ring_colors[min(idx, len(ring_colors) - 1)]
            p.setPen(QPen(color, ring_thickness, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, -90 * 16, -span_angle * 16)

        # Center text: show percentages for each
        p.setPen(text_color)
        font = QFont(self.font())
        font.setPointSize(11)
        font.setWeight(QFont.DemiBold)
        p.setFont(font)

        lines = []
        for label, ratio in self._items:
            percent = int(round(ratio * 100))
            lines.append(u"{0}: {1}%".format(label, percent))

        text_rect = QRectF(
            center_x - size * 0.22,
            center_y - size * 0.12,
            size * 0.44,
            size * 0.24,
        )
        p.drawText(text_rect, Qt.AlignCenter, "\n".join(lines))

        p.end()


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
        delete_btn = QPushButton("Delete User")

        for b in (login_btn, signup_btn, delete_btn):
            b.setStyleSheet(BUTTON_STYLE)

        login_btn.clicked.connect(self.handle_login)
        signup_btn.clicked.connect(self.handle_signup)
        delete_btn.clicked.connect(self.handle_delete)

        row.addWidget(login_btn)
        row.addWidget(signup_btn)
        row.addWidget(delete_btn)
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

    def handle_delete(self):
        username, password = self._get_credentials()
        if not username:
            return
        users = load_users()
        if username not in users:
            QMessageBox.warning(self, "User not found", "That user does not exist.")
            return
        if users[username] != password:
            QMessageBox.warning(self, "Wrong password", "Password incorrect.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete user",
            u"Delete user '{0}' and their login?\n(Notes etc. stay in shared JSON.)".format(
                username
            ),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            del users[username]
            save_users(users)
            settings = load_settings()
            if settings.get("last_user") == username:
                settings["last_user"] = ""
                save_settings(settings)
            QMessageBox.information(self, "Deleted", "User deleted.")

    def finish_login(self, username):
        settings = load_settings()
        settings["last_user"] = username
        save_settings(settings)
        self.on_login(username)
        self.goto_page("dashboard")


# ================= DASHBOARD =================


class DashboardPage(QWidget):
    """
    New dashboard:
    - Only big concentric progress rings
    - Today's To-Do (all pending tasks)
    - Today's Schedule (today's entries)
    """

    def __init__(self, goto_page, open_window, get_user, get_theme_colors, logout):
        super().__init__()
        self.goto_page = goto_page
        self.open_window = open_window
        self.get_user = get_user
        self.get_theme_colors = get_theme_colors
        self.logout = logout

        main = QVBoxLayout()
        main.setAlignment(Qt.AlignTop)

        # Top bar: title + user + logout
        top_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        top_row.addWidget(title)

        self.user_label = QLabel("")
        self.user_label.setStyleSheet("margin-left: 12px; color: #777777;")
        top_row.addWidget(self.user_label, stretch=0)

        top_row.addStretch()

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(BUTTON_STYLE + "font-size: 12px; padding: 4px 10px;")
        logout_btn.clicked.connect(self.logout)
        top_row.addWidget(logout_btn)

        main.addLayout(top_row)

        # Center: progress rings
        rings_frame = QFrame()
        rings_frame.setStyleSheet(CARD_STYLE)
        rings_layout = QVBoxLayout()
        rings_layout.setContentsMargins(18, 18, 18, 18)
        rings_frame.setLayout(rings_layout)

        self.progress_rings = MultiRingProgress(self.get_theme_colors)
        rings_layout.addWidget(self.progress_rings, alignment=Qt.AlignCenter)

        main.addWidget(rings_frame)

        # Bottom: two cards side by side: Today's To-Do, Today's Schedule
        bottom_row = QHBoxLayout()

        # Today's To-Do
        todo_frame = QFrame()
        todo_frame.setStyleSheet(CARD_STYLE)
        todo_layout = QVBoxLayout()
        todo_layout.setContentsMargins(12, 12, 12, 12)
        todo_frame.setLayout(todo_layout)

        todo_title = QLabel("Today's To-Do")
        todo_title.setStyleSheet("font-size: 16px; font-weight: 600; margin-bottom: 6px;")
        todo_layout.addWidget(todo_title)

        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet("font-size: 13px;")
        todo_layout.addWidget(self.todo_list)

        bottom_row.addWidget(todo_frame)

        # Today's Schedule
        sched_frame = QFrame()
        sched_frame.setStyleSheet(CARD_STYLE)
        sched_layout = QVBoxLayout()
        sched_layout.setContentsMargins(12, 12, 12, 12)
        sched_frame.setLayout(sched_layout)

        self.today_label = QLabel("")
        self.today_label.setStyleSheet("font-size: 16px; font-weight: 600; margin-bottom: 6px;")
        sched_layout.addWidget(self.today_label)

        self.today_list = QListWidget()
        self.today_list.setStyleSheet("font-size: 13px;")
        sched_layout.addWidget(self.today_list)

        bottom_row.addWidget(sched_frame)

        main.addLayout(bottom_row)

        main.addStretch(1)
        self.setLayout(main)

        self.refresh()

    def theme_changed(self):
        self.progress_rings.theme_changed()

    def refresh(self):
        # User label
        user = self.get_user()
        if user:
            self.user_label.setText(u"Logged in as: {0}".format(user))
        else:
            self.user_label.setText("Not logged in")

        # --- Load To-Do stats ---
        todos = load_json("todos.json", [])
        total_tasks = len(todos)
        done_tasks = sum(1 for t in todos if t.get("done"))
        pending_tasks = [t for t in todos if not t.get("done")]

        # show all pending tasks
        self.todo_list.clear()
        if not pending_tasks:
            self.todo_list.addItem("You're all caught up! ✨")
        else:
            for t in pending_tasks:
                label = u"[{0}] {1}".format(
                    t.get("priority", "Low"),
                    t.get("text", ""),
                )
                item = QListWidgetItem(label)
                self.todo_list.addItem(item)

        tasks_ratio = (float(done_tasks) / float(total_tasks)) if total_tasks > 0 else 0.0

        # --- Flashcards stats ---
        cards = load_json("flashcards.json", [])
        total_cards = len(cards)
        known_cards = sum(1 for c in cards if c.get("known"))
        flash_ratio = (float(known_cards) / float(total_cards)) if total_cards > 0 else 0.0

        # --- Notes stats (folders complete) ---
        notes_raw = load_json("notes.json", {"folders": {}})
        notes_data = normalize_notes_data(notes_raw)
        folders = notes_data.get("folders", {})
        total_folders = len(folders)
        complete_folders = sum(1 for f in folders.values() if f.get("complete"))
        notes_ratio = (
            float(complete_folders) / float(total_folders) if total_folders > 0 else 0.0
        )

        # Update multi-ring
        items = [
            ("Tasks", tasks_ratio),
            ("Flashcards", flash_ratio),
            ("Notes", notes_ratio),
        ]
        self.progress_rings.set_items(items)

        # --- Today's schedule ---
        raw_schedule = load_json("schedule.json", {})
        schedule = normalize_schedule_data(raw_schedule)

        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.today_label.setText(u"Today's Schedule — {0}".format(today))
        self.today_list.clear()
        entries = schedule.get(today, [])
        if not entries:
            self.today_list.addItem("No entries for today.")
        else:
            for e in entries:
                self.today_list.addItem(e)


# ================= TODO PAGE =================


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
        self.pending_list.setStyleSheet("font-size: 13px;")
        self.done_list = QListWidget()
        self.done_list.setStyleSheet("font-size: 13px; color: #888888;")
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

    def _style_item(self, lw_item, priority, done):
        if priority == "High":
            color = "#ff6b6b"
        elif priority == "Medium":
            color = "#ffb347"
        else:
            color = "#6bd36b"
        if done:
            lw_item.setForeground(QColor("#888888"))
        else:
            lw_item.setForeground(QColor(color))

    def refresh(self):
        self._load_data()
        self.pending_list.clear()
        self.done_list.clear()

        filt = self.filter_combo.currentText()
        for item in self.data:
            if filt != "All" and item.get("priority") != filt:
                continue
            label = u"[{0}] {1}".format(
                item.get("priority", "Low"),
                item.get("text", ""),
            )
            lw = QListWidgetItem(label)
            done = item.get("done")
            self._style_item(lw, item.get("priority", "Low"), done)
            if done:
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
                label = u"[{0}] {1}".format(
                    item.get("priority", "Low"),
                    item.get("text", ""),
                )
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


# ================= NOTES PAGE =================


class NotesPage(BasePage):
    FNAME = "notes.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        raw = load_json(self.FNAME, {"folders": {}})
        self.data = normalize_notes_data(raw)
        self.current_subject = None
        self.current_unit = None

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Notes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        main_row = QHBoxLayout()

        # Left: subjects list
        left_col = QVBoxLayout()
        subj_header_row = QHBoxLayout()
        subj_header_row.addWidget(QLabel("Subjects"))

        delete_subject_btn = QPushButton("Delete subject")
        delete_subject_btn.setStyleSheet(BUTTON_STYLE)
        delete_subject_btn.clicked.connect(self.delete_subject)
        subj_header_row.addWidget(delete_subject_btn)

        complete_btn = QPushButton("Mark folder complete")
        complete_btn.setStyleSheet(BUTTON_STYLE)
        complete_btn.clicked.connect(self.toggle_subject_complete)
        subj_header_row.addWidget(complete_btn)

        left_col.addLayout(subj_header_row)

        self.subject_list = QListWidget()
        self.subject_list.setViewMode(QListWidget.IconMode)
        self.subject_list.setResizeMode(QListWidget.Adjust)
        self.subject_list.setSpacing(12)
        self.subject_list.setMovement(QListWidget.Static)
        self.subject_list.setWrapping(True)
        self.subject_list.currentTextChanged.connect(self.select_subject)
        left_col.addWidget(self.subject_list)

        subj_add_row = QHBoxLayout()
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("New subject…")
        subj_add_btn = QPushButton("Add")
        subj_add_btn.setStyleSheet(BUTTON_STYLE)
        subj_add_btn.clicked.connect(self.add_subject)
        subj_add_row.addWidget(self.subject_input)
        subj_add_row.addWidget(subj_add_btn)
        left_col.addLayout(subj_add_row)

        left_widget = QWidget()
        left_widget.setLayout(left_col)
        main_row.addWidget(left_widget, 1)

        # Right: units + editor
        right_col = QVBoxLayout()

        self.subject_title = QLabel("No subject selected")
        right_col.addWidget(self.subject_title)

        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.currentTextChanged.connect(self.select_unit)
        unit_row.addWidget(self.unit_combo)

        add_unit_btn = QPushButton("Add unit")
        add_unit_btn.setStyleSheet(BUTTON_STYLE)
        add_unit_btn.clicked.connect(self.add_unit)
        unit_row.addWidget(add_unit_btn)

        del_unit_btn = QPushButton("Delete unit")
        del_unit_btn.setStyleSheet(BUTTON_STYLE)
        del_unit_btn.clicked.connect(self.delete_unit)
        unit_row.addWidget(del_unit_btn)

        right_col.addLayout(unit_row)

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

        self.refresh_subjects()

    def refresh_subjects(self):
        self.subject_list.clear()
        for name, info in self.data["folders"].items():
            complete = info.get("complete", False)
            label = u"✓ {0}".format(name) if complete else name
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, name)
            self.subject_list.addItem(item)

    def add_subject(self):
        name = self.subject_input.text().strip()
        if not name:
            QMessageBox.information(self, "No name", "Type a subject name.")
            return
        if name in self.data["folders"]:
            QMessageBox.information(self, "Exists", "That subject already exists.")
            return
        self.data["folders"][name] = {"complete": False, "units": {}}
        save_json(self.FNAME, self.data)
        self.subject_input.clear()
        self.refresh_subjects()

    def delete_subject(self):
        if not self.current_subject:
            QMessageBox.information(self, "No subject", "Select a subject to delete.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete subject",
            u"Delete subject '{0}' and all its units?".format(self.current_subject),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.data["folders"].pop(self.current_subject, None)
            save_json(self.FNAME, self.data)
            self.current_subject = None
            self.current_unit = None
            self.text_edit.clear()
            self.unit_combo.clear()
            self.subject_title.setText("No subject selected")
            self.refresh_subjects()

    def toggle_subject_complete(self):
        if not self.current_subject:
            QMessageBox.information(self, "No subject", "Select a subject first.")
            return
        folder = self.data["folders"].get(self.current_subject, {})
        folder["complete"] = not folder.get("complete", False)
        save_json(self.FNAME, self.data)
        self.refresh_subjects()

    def select_subject(self, display_name):
        if not display_name:
            return
        item = self.subject_list.currentItem()
        if not item:
            return
        name = item.data(Qt.UserRole)
        self.current_subject = name
        self.subject_title.setText(u"Notes — {0}".format(name))
        self.refresh_units()

    def refresh_units(self):
        self.unit_combo.blockSignals(True)
        self.unit_combo.clear()
        if not self.current_subject:
            self.unit_combo.blockSignals(False)
            return
        units = self.data["folders"][self.current_subject]["units"]
        for unit_name in units.keys():
            self.unit_combo.addItem(unit_name)
        self.unit_combo.blockSignals(False)
        if units:
            first = next(iter(units.keys()))
            self.unit_combo.setCurrentText(first)
            self.select_unit(first)
        else:
            self.current_unit = None
            self.text_edit.clear()

    def add_unit(self):
        if not self.current_subject:
            QMessageBox.information(self, "No subject", "Select a subject first.")
            return
        suggested = u"Unit {0}".format(
            len(self.data["folders"][self.current_subject]["units"]) + 1
        )
        text, ok = QInputDialog.getText(self, "New unit", "Unit name:", text=suggested)
        if not ok or not text.strip():
            return
        name = text.strip()
        units = self.data["folders"][self.current_subject]["units"]
        if name in units:
            QMessageBox.information(self, "Exists", "That unit already exists.")
            return
        units[name] = {"content": ""}
        save_json(self.FNAME, self.data)
        self.refresh_units()
        self.unit_combo.setCurrentText(name)
        self.select_unit(name)

    def delete_unit(self):
        if not self.current_subject or not self.current_unit:
            QMessageBox.information(self, "No unit", "Select a unit first.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete unit",
            u"Delete unit '{0}'?".format(self.current_unit),
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            units = self.data["folders"][self.current_subject]["units"]
            units.pop(self.current_unit, None)
            save_json(self.FNAME, self.data)
            self.current_unit = None
            self.refresh_units()

    def select_unit(self, unit_name):
        if not self.current_subject or not unit_name:
            return
        self.current_unit = unit_name
        content = (
            self.data["folders"][self.current_subject]["units"]
            .get(unit_name, {})
            .get("content", "")
        )
        self.text_edit.setPlainText(content)

    def save_notes(self):
        if not self.current_subject or not self.current_unit:
            QMessageBox.information(self, "No unit", "Select subject and unit first.")
            return
        self.data["folders"][self.current_subject]["units"][self.current_unit][
            "content"
        ] = self.text_edit.toPlainText()
        save_json(self.FNAME, self.data)
        QMessageBox.information(self, "Saved", "Notes saved.")


# ================= FLASHCARDS =================


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
        self.card_label.setStyleSheet(CARD_STYLE + "font-size: 18px;")
        layout.addWidget(self.card_label)

        self.effect = QGraphicsOpacityEffect()
        self.card_label.setGraphicsEffect(self.effect)
        self.anim = QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(180)

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
        changed = False
        for c in self.cards:
            if "known" not in c:
                c["known"] = False
                changed = True
        if changed:
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
        self.counter_label.setText(
            u"Card {0} / {1}".format(self.index + 1, len(self.cards))
        )
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
        self.counter_label.setText(
            u"Card {0} / {1}".format(self.index + 1, len(self.cards))
        )
        self._play_flip_anim()

    def add_card(self):
        front = self.front_input.text().strip()
        back = self.back_input.text().strip()
        if not front or not back:
            QMessageBox.information(
                self, "Missing", "Please fill in both front and back."
            )
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
        self.data = load_json(self.FNAME, {"subjects": {}})
        self._normalize_data()
        self.current_subject = None
        self.current_unit = None

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Study Resources")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        main_row = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("Subjects"))
        self.subject_box = QListWidget()
        self.subject_box.currentTextChanged.connect(self.select_subject)
        left_col.addWidget(self.subject_box)

        subj_add_row = QHBoxLayout()
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("New subject…")
        add_subj_btn = QPushButton("Add")
        add_subj_btn.setStyleSheet(BUTTON_STYLE)
        add_subj_btn.clicked.connect(self.add_subject)
        subj_add_row.addWidget(self.subject_input)
        subj_add_row.addWidget(add_subj_btn)
        left_col.addLayout(subj_add_row)

        left_widget = QWidget()
        left_widget.setLayout(left_col)
        main_row.addWidget(left_widget, 1)

        right_col = QVBoxLayout()

        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.currentTextChanged.connect(self.select_unit)
        unit_row.addWidget(self.unit_combo)

        add_unit_btn = QPushButton("Add unit")
        add_unit_btn.setStyleSheet(BUTTON_STYLE)
        add_unit_btn.clicked.connect(self.add_unit)
        unit_row.addWidget(add_unit_btn)

        right_col.addLayout(unit_row)

        self.listw = QListWidget()
        self.listw.itemDoubleClicked.connect(self.open_link)
        right_col.addWidget(self.listw)

        bottom_row = QHBoxLayout()
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Paste a link…")
        add_btn = QPushButton("Add link")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self.add_link)
        bottom_row.addWidget(self.link_input)
        bottom_row.addWidget(add_btn)
        right_col.addLayout(bottom_row)

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        main_row.addWidget(right_widget, 2)

        layout.addLayout(main_row)
        self.setLayout(layout)
        self.refresh_subjects()

    def _normalize_data(self):
        if isinstance(self.data, list):
            self.data = {"subjects": {"General": {"units": {"All": self.data}}}}
            save_json(self.FNAME, self.data)
            return
        if "subjects" not in self.data or not isinstance(self.data["subjects"], dict):
            self.data["subjects"] = {}
            save_json(self.FNAME, self.data)

    def refresh_subjects(self):
        self.subject_box.clear()
        for subj in sorted(self.data["subjects"].keys()):
            self.subject_box.addItem(subj)

    def select_subject(self, name):
        if not name:
            return
        self.current_subject = name
        self.refresh_units()

    def refresh_units(self):
        self.unit_combo.blockSignals(True)
        self.unit_combo.clear()
        if not self.current_subject:
            self.unit_combo.blockSignals(False)
            self.listw.clear()
            return
        units = self.data["subjects"][self.current_subject]["units"]
        for unit in units.keys():
            self.unit_combo.addItem(unit)
        self.unit_combo.blockSignals(False)
        if units:
            first = next(iter(units.keys()))
            self.unit_combo.setCurrentText(first)
            self.select_unit(first)
        else:
            self.current_unit = None
            self.listw.clear()

    def add_subject(self):
        name = self.subject_input.text().strip()
        if not name:
            QMessageBox.information(self, "No name", "Type a subject name.")
            return
        if name in self.data["subjects"]:
            QMessageBox.information(self, "Exists", "That subject already exists.")
            return
        self.data["subjects"][name] = {"units": {}}
        save_json(self.FNAME, self.data)
        self.subject_input.clear()
        self.refresh_subjects()

    def add_unit(self):
        if not self.current_subject:
            QMessageBox.information(self, "No subject", "Select a subject first.")
            return
        suggested = u"Unit {0}".format(
            len(self.data["subjects"][self.current_subject]["units"]) + 1
        )
        text, ok = QInputDialog.getText(self, "New unit", "Unit name:", text=suggested)
        if not ok or not text.strip():
            return
        name = text.strip()
        units = self.data["subjects"][self.current_subject]["units"]
        if name in units:
            QMessageBox.information(self, "Exists", "That unit already exists.")
            return
        units[name] = []
        save_json(self.FNAME, self.data)
        self.refresh_units()
        self.unit_combo.setCurrentText(name)
        self.select_unit(name)

    def select_unit(self, unit_name):
        if not self.current_subject or not unit_name:
            return
        self.current_unit = unit_name
        self.refresh_links()

    def refresh_links(self):
        self.listw.clear()
        if not self.current_subject or not self.current_unit:
            return
        links = self.data["subjects"][self.current_subject]["units"].get(
            self.current_unit, []
        )
        for url in links:
            self.listw.addItem(url)

    def add_link(self):
        if not self.current_subject or not self.current_unit:
            QMessageBox.information(self, "No unit", "Select subject & unit first.")
            return
        url = self.link_input.text().strip()
        if not url:
            QMessageBox.information(
                self, "Empty link", "Paste a valid URL before adding."
            )
            return
        units = self.data["subjects"][self.current_subject]["units"]
        units.setdefault(self.current_unit, []).append(url)
        save_json(self.FNAME, self.data)
        self.link_input.clear()
        self.refresh_links()

    def open_link(self, item):
        QDesktopServices.openUrl(QUrl(item.text()))


# ================= SCHEDULE PAGE =================


class SchedulePage(BasePage):
    FNAME = "schedule.json"

    def __init__(self, goto_page, standalone=False):
        super().__init__(goto_page, standalone)
        raw = load_json(self.FNAME, {})
        self.data = normalize_schedule_data(raw)

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
        self.entries_label.setText(u"Entries for {0}:".format(key))
        for e in entries:
            self.listw.addItem(e)

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


# ================= TIMER PAGE =================


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
        self.time_label.setStyleSheet(
            """
            font-size: 72px;
            font-weight: 600;
            padding: 24px 32px;
            border-radius: 22px;
            background-color: rgba(0, 0, 0, 0.06);
            letter-spacing: 6px;
            """
        )
        self.time_label.setMinimumHeight(180)
        layout.addWidget(self.time_label)

        self.time_effect = QGraphicsOpacityEffect()
        self.time_label.setGraphicsEffect(self.time_effect)
        self.time_anim = QPropertyAnimation(self.time_effect, b"opacity")
        self.time_anim.setDuration(160)

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
        self.time_effect.setOpacity(0.2)
        self.time_anim.setStartValue(0.2)
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
                QMessageBox.information(
                    self, "Invalid minutes", "Please enter a whole number."
                )
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
        self.time_label.setText("{0:02d}:{1:02d}".format(mins, secs))
