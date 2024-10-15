from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class MessageWidget(QWidget):
    def __init__(self, text, is_sender):
        super().__init__()
        layout = QHBoxLayout()

        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))

        if is_sender:
            label.setStyleSheet("background-color: #00a86b; padding: 10px; border-radius: 10px;")
            layout.addWidget(label, alignment=Qt.AlignRight)
        else:
            label.setStyleSheet("background-color: #00754a; padding: 10px; border-radius: 10px;")
            layout.addWidget(label, alignment=Qt.AlignLeft)

        self.setLayout(layout)