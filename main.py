import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainter, QColor, QIcon, QPalette

from data_manager import ensure_all_defaults, load_settings, save_settings
from themes import build_stylesheet, THEME_NAMES, LIGHT_THEMES, DARK_THEMES
from pages import (
    LoginPage, DashboardPage, TodoPage, NotesPage,
    FlashcardsPage, ResourcesPage, SchedulePage, TimerPage
)


def make_open_window_icon(size=20):
    """
    Tiny square + plus symbol, used next to sidebar options.
    """
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # square outline
    p.setPen(QColor(80, 80, 80))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(3, 3, size - 6, size - 6, 3, 3)

    # plus sign
    mid = size // 2
    p.drawLine(mid, 5, mid, size - 5)
    p.drawLine(5, mid, size - 5, mid)

    p.end()
    return QIcon(pix)


class StandaloneWindow(QMainWindow):
    """
    Pop-out window for any page (ToDo, Notes, etc.).
    """
    def __init__(self, page_cls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Student Helper")
        page = page_cls(goto_page=None, standalone=True)
        self.setCentralWidget(page)
        self.resize(850, 550)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ensure_all_defaults()

        self.setWindowTitle("Student Helper")
        self.resize(1000, 650)

        self.current_user = None
        self.child_windows = []
        self.current_page_key = "login"
        self.sidebar_user_collapsed = False

        # load handwriting / app font if present
        self.font_name = self.load_handwriting_font()

        # settings & theme
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "Pink")
        if self.theme_name not in THEME_NAMES:
            self.theme_name = "Pink"
        self.dark_mode = bool(self.settings.get("dark", False))
        self.current_user = self.settings.get("last_user") or None

        central = QWidget()
        root = QVBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        # ---------- Top bar ----------
        top_bar = QHBoxLayout()

        # sidebar toggle (collapsible)
        self.toggle_sidebar_btn = QPushButton("☰")
        self.toggle_sidebar_btn.setFixedWidth(32)
        self.toggle_sidebar_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.toggle_sidebar_btn.setToolTip("Hide/show sidebar")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        top_bar.addWidget(self.toggle_sidebar_btn)

        # title
        self.title_label = QLabel("Student Helper")
        if self.current_user:
            self.title_label.setText("Student Helper — " + self.current_user)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # theme selector – icons only (no text)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(120)
        self.populate_theme_combo()
        try:
            idx = THEME_NAMES.index(self.theme_name)
        except ValueError:
            idx = 0
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        # dark / light toggle
        self.dark_btn = QPushButton("☾" if not self.dark_mode else "☀")
        self.dark_btn.setFixedWidth(40)
        self.dark_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.dark_btn.setToolTip("Toggle dark / light")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        root.addLayout(top_bar)

        # ---------- Body: sidebar + stacked pages ----------
        body = QHBoxLayout()

        # Sidebar
        self.sidebar = QWidget()
        side_layout = QVBoxLayout()
        side_layout.setAlignment(Qt.AlignTop)
        self.sidebar.setLayout(side_layout)

        self.open_icon = make_open_window_icon()

        nav_buttons = [
            ("Dashboard", "dashboard"),
            ("To-Do", "todo"),
            ("Notes", "notes"),
            ("Flashcards", "flashcards"),
            ("Resources", "resources"),
            ("Schedule", "schedule"),
            ("Timer", "timer"),
        ]

        self.nav_btns = {}
        for text, key in nav_buttons:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            btn = QPushButton(text)
            btn.setStyleSheet("border-radius: 10px; padding: 8px 10px;")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda _, p=key: self.switch_to(p))
            row_layout.addWidget(btn)
            self.nav_btns[key] = btn

            open_btn = QPushButton()
            open_btn.setIcon(self.open_icon)
            open_btn.setToolTip("Open in new window")
            open_btn.setFixedSize(26, 26)
            open_btn.setStyleSheet("border: none; padding: 2px;")
            open_btn.clicked.connect(lambda _, p=key: self.open_in_new_window(p))
            row_layout.addWidget(open_btn)

            side_layout.addWidget(row_widget)

        side_layout.addStretch(1)
        body.addWidget(self.sidebar, 0)

        # Stack
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)

        root.addLayout(body)

        # ---------- Create pages ----------
        self.pages = {}
        self.page_order = []

        self.add_page("login", LoginPage(self.switch_to, self.set_current_user))

        self.add_page(
            "dashboard",
            DashboardPage(
                goto_page=self.switch_to,
                open_window=self.open_in_new_window,
                get_user=self.get_current_user,
                logout=self.logout,
            ),
        )

        self.add_page("todo", TodoPage(self.switch_to))
        self.add_page("notes", NotesPage(self.switch_to))
        self.add_page("flashcards", FlashcardsPage(self.switch_to))
        self.add_page("resources", ResourcesPage(self.switch_to))
        self.add_page("schedule", SchedulePage(self.switch_to))
        self.add_page("timer", TimerPage(self.switch_to))

        # start page
        if self.current_user:
            self.switch_to("dashboard")
        else:
            self.switch_to("login")

        self.apply_theme()

    # ---------- fonts & themes ----------

    def load_handwriting_font(self):
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ttf_path = os.path.join(assets_dir, "handwriting.ttf")
        if os.path.exists(ttf_path):
            font_id = QFontDatabase.addApplicationFont(ttf_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "Avenir"

    def populate_theme_combo(self):
        self.theme_combo.clear()
        for name in THEME_NAMES:
            colors = LIGHT_THEMES[name]
            pix = QPixmap(20, 20)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)

            # big circle = accent
            p.setBrush(QColor(colors["button_bg"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(1, 1, 18, 18)

            # little arc = card bg
            p.setBrush(QColor(colors["card_bg"]))
            p.drawPie(1, 1, 18, 18, 90 * 16, 180 * 16)

            p.end()
            icon = QIcon(pix)
            # show only the icon – no text
            self.theme_combo.addItem(icon, "")

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("☾" if not self.dark_mode else "☀")

        # Make accent colour part of the palette, so custom painting (progress rings)
        # picks it up via palette().highlight().
        base = DARK_THEMES if self.dark_mode else LIGHT_THEMES
        theme = base.get(self.theme_name, base["Pink"])
        accent = QColor(theme["accent"])

        pal = self.palette()
        pal.setColor(QPalette.Highlight, accent)
        pal.setColor(QPalette.Link, accent)
        self.setPalette(pal)

    def change_theme(self, index):
        if 0 <= index < len(THEME_NAMES):
            self.theme_name = THEME_NAMES[index]
            self.apply_theme()
            self.save_settings()

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()

    def save_settings(self):
        self.settings["theme"] = self.theme_name
        self.settings["dark"] = self.dark_mode
        self.settings["last_user"] = self.current_user or ""
        self.settings["font"] = self.font_name
        save_settings(self.settings)

    # ---------- page / sidebar management ----------

    def add_page(self, key, widget):
        self.pages[key] = widget
        self.page_order.append(key)
        self.stack.addWidget(widget)

    def update_sidebar_visibility(self):
        # Sidebar always hidden on login page
        if self.current_page_key == "login":
            self.sidebar.setVisible(False)
            self.toggle_sidebar_btn.setEnabled(False)
            return

        self.toggle_sidebar_btn.setEnabled(True)
        collapsed = self.sidebar_user_collapsed or self.width() < 800
        self.sidebar.setVisible(not collapsed)
        self.toggle_sidebar_btn.setText("☰" if collapsed else "⮜")

    def toggle_sidebar(self):
        # User explicit toggle
        self.sidebar_user_collapsed = not self.sidebar_user_collapsed
        self.update_sidebar_visibility()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # auto-collapse based on width
        self.update_sidebar_visibility()

    def switch_to(self, key):
        if key not in self.pages:
            key = "login"
        self.current_page_key = key
        self.stack.setCurrentWidget(self.pages[key])

        if key == "dashboard":
            page = self.pages["dashboard"]
            if hasattr(page, "refresh"):
                page.refresh()

        self.update_sidebar_visibility()

    # ---------- user callbacks ----------

    def set_current_user(self, username):
        self.current_user = username
        self.title_label.setText("Student Helper — " + username)
        self.save_settings()
        self.switch_to("dashboard")

    def get_current_user(self):
        return self.current_user

    def logout(self):
        self.current_user = None
        self.title_label.setText("Student Helper")
        self.save_settings()
        self.switch_to("login")

    # ---------- multi window ----------

    def open_in_new_window(self, key):
        cls_map = {
            "todo": TodoPage,
            "notes": NotesPage,
            "flashcards": FlashcardsPage,
            "resources": ResourcesPage,
            "schedule": SchedulePage,
            "timer": TimerPage,
            "dashboard": DashboardPage,
        }
        if key not in cls_map:
            return
        win = StandaloneWindow(cls_map[key], parent=self)
        win.show()
        self.child_windows.append(win)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
