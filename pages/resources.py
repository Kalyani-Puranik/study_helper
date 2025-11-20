class ResourcesPage(BasePage):
    def __init__(self, app, standalone=False):
        super().__init__(app, standalone)
        self.data = load_json("data/resources.json")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Study Resources")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.listbox = QListWidget()
        layout.addWidget(self.listbox)
        self.refresh()

        row = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Paste link…")
        row.addWidget(self.input)

        add = QPushButton("Add")
        add.setStyleSheet(BUTTON_STYLE)
        add.clicked.connect(self.add)
        row.addWidget(add)

        layout.addLayout(row)
        self.setLayout(layout)

    def refresh(self):
        self.listbox.clear()
        for url in self.data:
            self.listbox.addItem(url)

    def add(self):
        url = self.input.text().strip()
        if url:
            self.data.append(url)
            save_json("data/resources.json", self.data)
            self.refresh()
            self.input.clear()
