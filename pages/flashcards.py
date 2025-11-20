class FlashcardPage(BasePage):
    def __init__(self, app, standalone=False):
        super().__init__(app, standalone)

        self.cards = load_json("data/flashcards.json")
        self.index = 0
        self.front_side = True

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Flashcards")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.card_box = QLabel("No cards yet." if not self.cards else self.cards[0]["front"])
        self.card_box.setStyleSheet(CARD_STYLE + "font-size:20px; font-family:'Avenir';")
        self.card_box.setAlignment(Qt.AlignCenter)
        self.card_box.setMinimumHeight(180)
        layout.addWidget(self.card_box)

        row = QHBoxLayout()

        flip = QPushButton("Flip")
        flip.setStyleSheet(BUTTON_STYLE)
        flip.clicked.connect(self.flip)
        row.addWidget(flip)

        nxt = QPushButton("Next")
        nxt.setStyleSheet(BUTTON_STYLE)
        nxt.clicked.connect(self.next)
        row.addWidget(nxt)

        layout.addLayout(row)
        self.setLayout(layout)

    def flip(self):
        if not self.cards:
            return
        self.front_side = not self.front_side
        side = "front" if self.front_side else "back"
        self.card_box.setText(self.cards[self.index][side])

    def next(self):
        if not self.cards:
            return
        self.index = (self.index + 1) % len(self.cards)
        self.front_side = True
        self.card_box.setText(self.cards[self.index]["front"])
