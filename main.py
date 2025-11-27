import sys
import os

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QComboBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QPixmap, QPainter, QColor, QIcon

from data_manager import ensure_all_defaults, load_settings, save_settings
from themes import build_stylesheet, THEME_NAMES, LIGHT_THEMES, DARK_THEMES
from pages import (
    LoginPage,
    DashboardPage,
    TodoPage,
    NotesPage,
    FlashcardsPage,
    ResourcesPage,
    SchedulePage,
    TimerPage,
)


class StandaloneWindow(QMainWindow):
    """
    Simple resizable window used for "open in new window".
    """

    def __init__(self, page_cls, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Student Helper")
        page = page_cls(goto_page=None, standalone=True)
        self.setCentralWidget(page)
        self.resize(900, 650)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ensure_all_defaults()

        self.setWindowTitle("Student Helper")
        self.resize(1100, 700)

        self.current_user = None
        self.child_windows = []
        self.sidebar_collapsed_manual = False
        self.current_page_key = "login"

        # Load handwriting font if present
        self.font_name = self.load_handwriting_font()

        # Settings & theme
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme", "Pink")
        if self.theme_name not in THEME_NAMES:
            self.theme_name = "Pink"
        self.dark_mode = bool(self.settings.get("dark", False))
        self.current_user = self.settings.get("last_user") or None

        # Central layout
        central = QWidget()
        central_layout = QVBoxLayout()
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        # ---------- Top Bar ----------
        top_bar = QHBoxLayout()

        self.title_label = QLabel("Student Helper")
        if self.current_user:
            self.title_label.setText("Student Helper — " + self.current_user)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        top_bar.addWidget(self.title_label)

        top_bar.addStretch()

        # Sidebar toggle button
        self.sidebar_toggle_btn = QPushButton("☰")
        self.sidebar_toggle_btn.setFixedWidth(36)
        self.sidebar_toggle_btn.setToolTip("Toggle sidebar")
        self.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        top_bar.addWidget(self.sidebar_toggle_btn)

        # Theme combo (icons only, names hidden)
        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(110)
        self.populate_theme_combo()
        # Set current index by theme_name
        if self.theme_name in THEME_NAMES:
            idx = THEME_NAMES.index(self.theme_name)
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_combo_changed)
        top_bar.addWidget(self.theme_combo)

        # Dark / light toggle
        self.dark_btn = QPushButton("☾" if not self.dark_mode else "☀")
        self.dark_btn.setFixedWidth(40)
        self.dark_btn.setStyleSheet("border-radius: 12px; padding: 4px;")
        self.dark_btn.setToolTip("Toggle dark / light")
        self.dark_btn.clicked.connect(self.toggle_dark)
        top_bar.addWidget(self.dark_btn)

        central_layout.addLayout(top_bar)

        # ---------- Body: sidebar + stacked pages ----------
        body = QHBoxLayout()

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(6)
        side_layout.setAlignment(Qt.AlignTop)
        self.sidebar.setLayout(side_layout)

        self.popout_icon = self.make_popout_icon()

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
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            row_widget.setLayout(row_layout)

            btn = QPushButton(text)
            btn.setStyleSheet("border-radius: 10px; padding: 8px 10px;")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, p=key: self.switch_to(p))
            row_layout.addWidget(btn)
            self.nav_btns[key] = btn

            # square + icon to open in new window (skip for dashboard)
            if key != "dashboard":
                pop_btn = QPushButton()
                pop_btn.setIcon(self.popout_icon)
                pop_btn.setToolTip("Open in new window")
                pop_btn.setFixedSize(26, 26)
                pop_btn.setStyleSheet("border: none; padding: 0;")
                pop_btn.clicked.connect(lambda _, p=key: self.open_in_new_window(p))
                row_layout.addWidget(pop_btn)

            side_layout.addWidget(row_widget)

        side_layout.addStretch(1)
        body.addWidget(self.sidebar, 0)

        # Main stack
        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)

        central_layout.addLayout(body)

        # ---------- Create pages ----------
        self.pages = {}
        self.page_order = []

        self.add_page("login", LoginPage(self.switch_to, self.set_current_user))
        self.add_page(
            "dashboard",
            DashboardPage(
                self.switch_to,
                self.open_in_new_window,
                self.get_current_user,
                self.get_theme_colors,
                self.logout,
            ),
        )
        self.add_page("todo", TodoPage(self.switch_to))
        self.add_page("notes", NotesPage(self.switch_to))
        self.add_page("flashcards", FlashcardsPage(self.switch_to))
        self.add_page("resources", ResourcesPage(self.switch_to))
        self.add_page("schedule", SchedulePage(self.switch_to))
        self.add_page("timer", TimerPage(self.switch_to))

        # Start page
        if self.current_user:
            self.switch_to("dashboard")
        else:
            self.switch_to("login")

        self.apply_theme()

    # ---------- Fonts & Themes ----------

    def load_handwriting_font(self):
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ttf_path = os.path.join(assets_dir, "handwriting.ttf")
        if os.path.exists(ttf_path):
            font_id = QFontDatabase.addApplicationFont(ttf_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        return "Avenir"

    def make_popout_icon(self, size=18):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        # square
        p.setPen(QColor(80, 80, 80))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(2, 2, size - 4, size - 4, 3, 3)

        # plus
        mid = size // 2
        p.drawLine(mid, 4, mid, size - 4)
        p.drawLine(4, mid, size - 4, mid)

        p.end()
        return QIcon(pix)

    def populate_theme_combo(self):
        self.theme_combo.clear()
        for name in THEME_NAMES:
            colors = LIGHT_THEMES[name]  # use light palette for preview
            pix = QPixmap(20, 20)
            pix.fill(Qt.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.Antialiasing)

            # big circle = accent/button bg
            p.setBrush(QColor(colors["button_bg"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(1, 1, 18, 18)

            # small arc = card bg
            p.setBrush(QColor(colors["card_bg"]))
            p.drawPie(1, 1, 18, 18, 90 * 16, 180 * 16)

            p.end()
            icon = QIcon(pix)
            # Text intentionally left empty; store name in userData
            self.theme_combo.addItem(icon, "")
            index = self.theme_combo.count() - 1
            self.theme_combo.setItemData(index, name, Qt.UserRole)

    def get_theme_colors(self):
        base = DARK_THEMES if self.dark_mode else LIGHT_THEMES
        if self.theme_name not in base:
            return base["Pink"]
        return base[self.theme_name]

    def apply_theme(self):
        sheet = build_stylesheet(self.theme_name, self.dark_mode, self.font_name)
        self.setStyleSheet(sheet)
        self.dark_btn.setText("☾" if not self.dark_mode else "☀")

        # Let dashboard redraw its rings with new theme
        dash = self.pages.get("dashboard")
        if dash is not None and hasattr(dash, "theme_changed"):
            dash.theme_changed()

    def on_theme_combo_changed(self, index):
        name = self.theme_combo.itemData(index, Qt.UserRole)
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

    # ---------- Page management ----------

    def add_page(self, key, widget):
        self.pages[key] = widget
        self.page_order.append(key)
        self.stack.addWidget(widget)

    def switch_to(self, key):
        if key not in self.pages:
            key = "login"
        self.current_page_key = key
        self.stack.setCurrentWidget(self.pages[key])

        # Sidebar visibility (login hides sidebar)
        self.update_sidebar_visibility()

        # Refresh dashboard when shown
        if key == "dashboard":
            page = self.pages["dashboard"]
            if hasattr(page, "refresh"):
                page.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_sidebar_visibility()

    def update_sidebar_visibility(self):
        # No sidebar on login page
        if self.current_page_key == "login":
            self.sidebar.setVisible(False)
            return

        if self.sidebar_collapsed_manual:
            self.sidebar.setVisible(False)
            return

        # Auto-collapse when narrow
        if self.width() < 720:
            self.sidebar.setVisible(False)
        else:
            self.sidebar.setVisible(True)

    def toggle_sidebar(self):
        self.sidebar_collapsed_manual = not self.sidebar_collapsed_manual
        self.update_sidebar_visibility()

    # ---------- User callbacks ----------

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

    # ---------- Multi-window ----------

    def open_in_new_window(self, key):
        cls_map = {
            "todo": TodoPage,
            "notes": NotesPage,
            "flashcards": FlashcardsPage,
            "resources": ResourcesPage,
            "schedule": SchedulePage,
            "timer": TimerPage,
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
