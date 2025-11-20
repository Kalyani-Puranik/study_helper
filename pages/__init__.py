class BasePage(QWidget):
    def __init__(self, app, standalone=False):
        super().__init__()
        self.app = app          # main window / controller
        self.standalone = standalone
        self.setContentsMargins(40, 30, 40, 30)

    def add_back(self, layout):
        if not self.standalone:
            back = QPushButton("← Back to Dashboard")
            back.setStyleSheet(BUTTON_STYLE)
            back.clicked.connect(lambda: self.app.switch_to("dashboard"))
            layout.addWidget(back)
