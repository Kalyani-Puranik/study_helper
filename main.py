import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainter, QColor, QIcon

from data_manager import ensure_all_defaults, load_settings, save_settings
from themes import build_stylesheet, THEME_NAMES, LIGHT_THEMES
from pages import (
    LoginPage, DashboardPage, TodoPage, NotesPage,
    FlashcardsPage, ResourcesPage, SchedulePage, TimerPage
)


class StandaloneWindow(QMainWindow):
    """Pop-out window for any page."""
    def __init__(self, page_cls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Student Helper")

        page = page_cls(goto_page=None, standalone=True)
        self.setCentralWidget(page)

        # Resizable window
        self.resize(900, 600)
        self.setMinimumSize(700, 450)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ensure_all_defaults()

        self.setWindowTitle("Student Helper")
        self.resize(1100, 700)
        self.setMinimumSize(900, 550)

        self.current_user = None
        self.child_windows = []
        self.sidebar_collapsed = False

        # load handwriting font if present
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
        root.setContentsMargins(10, 10, 10, 10)
        central.setLayout(root)
        self.setCentralWidget(central)

        # ---------- Top bar ----------
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Student Helper")
        if self.current_user:
            self.title_label.setText("Student Helper — " + self.current_user)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Theme selector with only coloured circles (no text)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(90)
        self.populate_theme_combo()
        self.set_theme_combo_index_from_name(self.theme_name)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        # Dark / Light toggle
        self.dark_btn = QPushButton("☾" if not self.dark_mode else "☀")
        self.dark_btn.setFixedWidth(40)
        self.dark_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.dark_btn.setToolTip("Toggle dark / light")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        # Sidebar collapse / expand button
        self.toggle_sidebar_btn = QPushButton("☰")
        self.toggle_sidebar_btn.setFixedWidth(40)
        self.toggle_sidebar_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.toggle_sidebar_btn.setToolTip("Hide / Show Sidebar")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        top_bar.addWidget(self.toggle_sidebar_btn)

        root.addLayout(top_bar)

        # ---------- Body: sidebar + stacked pages ----------
        body = QHBoxLayout()

        # Sidebar
        self.sidebar = QWidget()
        side_layout = QVBoxLayout()
        side_layout.setAlignment(Qt.AlignTop)
        self.sidebar.setLayout(side_layout)

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
            btn = QPushButton(text)
            btn.setStyleSheet("border-radius: 10px; padding: 8px 10px;")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, p=key: self.switch_to(p))
            side_layout.addWidget(btn)
            self.nav_btns[key] = btn

        side_layout.addStretch(1)
        body.addWidget(self.sidebar, 0)

        # Stack
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        body.addWidget(self.stack, 1)

        root.addLayout(body)

        # ---------- Create pages ----------
        self.pages = {}
        self.page_order = []

        self.add_page("login", LoginPage(self.switch_to, self.set_current_user))
        self.add_page(
            "dashboard",
            DashboardPage(self.switch_to, self.open_in_new_window,
                          self.get_current_user, self.logout),
        )
        self.add_page("todo",    TodoPage(self.switch_to))
        self.add_page("notes",   NotesPage(self.switch_to))
        self.add_page("flashcards", FlashcardsPage(self.switch_to))
        self.add_page("resources",  ResourcesPage(self.switch_to))
        self.add_page("schedule",   SchedulePage(self.switch_to))
        self.add_page("timer",      TimerPage(self.switch_to))

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
        """Populate combo with coloured circles only; store names in itemData."""
        self.theme_combo.clear()
        for name in THEME_NAMES:
            colors = LIGHT_THEMES[name]
            pix = QPixmap(22, 22)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)

            # big circle = accent
            p.setBrush(QColor(colors["button_bg"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(1, 1, 20, 20)

            # small circle inside = card bg
            p.setBrush(QColor(colors["card_bg"]))
            p.drawEllipse(6, 6, 10, 10)

            p.end()
            icon = QIcon(pix)

            index = self.theme_combo.count()
            self.theme_combo.addItem(icon, "")            # no visible name
            self.theme_combo.setItemData(index, name)     # store actual theme name

    def set_theme_combo_index_from_name(self, theme_name):
        index_to_set = 0
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme_name:
                index_to_set = i
                break
        self.theme_combo.setCurrentIndex(index_to_set)

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("☾" if not self.dark_mode else "☀")

    def change_theme(self, index):
        name = self.theme_combo.itemData(index)
        if not name:
            return
        self.theme_name = name
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

    # ---------- sidebar toggle ----------

    def toggle_sidebar(self):
        """Collapse / expand the sidebar."""
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.sidebar_collapsed = True
        else:
            # Don't show sidebar on login page
            current_widget = self.stack.currentWidget()
            if current_widget is self.pages.get("login"):
                return
            self.sidebar.show()
            self.sidebar_collapsed = False

    # ---------- page management ----------

    def add_page(self, key, widget):
        self.pages[key] = widget
        self.page_order.append(key)
        self.stack.addWidget(widget)

    def switch_to(self, key):
        if key not in self.pages:
            key = "login"

        self.stack.setCurrentWidget(self.pages[key])

        # Sidebar visibility: always hidden on login, otherwise follow collapse state
        if key == "login":
            self.sidebar.hide()
        else:
            if not self.sidebar_collapsed:
                self.sidebar.show()

        if key == "dashboard":
            page = self.pages["dashboard"]
            if hasattr(page, "refresh"):
                page.refresh()

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
            "todo":      TodoPage,
            "notes":     NotesPage,
            "flashcards": FlashcardsPage,
            "resources":  ResourcesPage,
            "schedule":   SchedulePage,
            "timer":      TimerPage,
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
