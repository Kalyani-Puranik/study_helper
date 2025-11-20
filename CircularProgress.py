from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QFont, QColor
from PyQt5.QtCore import Qt, QRectF

class CircularProgress(QWidget):
    def __init__(self, value=0, size=140, text="Progress", color="#ff78b5", parent=None):
        super().__init__(parent)
        self.value = value
        self.size = size
        self.text = text
        self.color = QColor(color)
        self.resize(size, size)

    def setValue(self, v):
        self.value = min(max(v, 0), 100)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(10, 10, self.size - 20, self.size - 20)
        start_angle = -90 * 16
        span_angle = -(self.value / 100) * 360 * 16

        # background circle
        pen = QPen(QColor(230, 230, 230), 12)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # progress circle
        pen.setColor(self.color)
        p.setPen(pen)
        p.drawArc(rect, start_angle, span_angle)

        # text
        p.setPen(Qt.black)
        p.setFont(QFont("Avenir", 13, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, f"{self.value}%\n{self.text}")
