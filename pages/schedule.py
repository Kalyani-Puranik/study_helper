class SchedulePage(BasePage):
    def __init__(self, app, standalone=False):
        super().__init__(app, standalone)
        self.data = load_json("data/schedule.json")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Schedule")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.listbox = QListWidget()
        layout.addWidget(self.listbox)
        self.refresh()

        row = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("New schedule entry…")
        row.addWidget(self.input)

        add = QPushButton("Add")
        add.setStyleSheet(BUTTON_STYLE)
        add.clicked.connect(self.add)
        row.addWidget(add)

        layout.addLayout(row)
        self.setLayout(layout)

    def refresh(self):
        self.listbox.clear()
        for e in self.data:
            self.listbox.addItem(e)

    def add(self):
        txt = self.input.text().strip()
        if txt:
            self.data.append(txt)
            save_json("data/schedule.json", self.data)
            self.refresh()
            self.input.clear()
