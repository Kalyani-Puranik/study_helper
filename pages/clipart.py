class ClipartPage(BasePage):
    def __init__(self, app, standalone=False):
        super().__init__(app, standalone)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.add_back(layout)

        title = QLabel("Clipart Generator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(TITLE_STYLE)
        layout.addWidget(title)

        desc = QLabel(
            "Upload any image and we’ll open a clipart-maker website so you\n"
            "can generate cute stickers, icons, or outlines."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(TEXT_STYLE)
        layout.addWidget(desc)

        upload_btn = QPushButton("Upload Image")
        upload_btn.setStyleSheet(BUTTON_STYLE)
        upload_btn.setMinimumHeight(55)
        upload_btn.clicked.connect(self.pick_file)
        layout.addWidget(upload_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def pick_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)",
        )

        if file:
            # clipart generator website
            QDesktopServices.openUrl(QUrl("https://vectorizer.ai"))
