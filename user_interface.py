# user_interface.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt
from qt_material import apply_stylesheet


class ChatApplication(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)

        # Основной макет
        main_layout = QHBoxLayout(self)

        # Левая панель для списка контактов
        self.contact_list = QListWidget()
        self.contact_list.addItems(["User 1", "User 2", "User 3"])  # Пример контактов
        self.contact_list.setFixedWidth(200)

        # Правая панель для чата
        chat_layout = QVBoxLayout()

        # Поле для отображения сообщений
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Нижняя панель для ввода сообщения
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)

        chat_layout.addLayout(message_layout)

        # Разделитель для контактов и чата
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.contact_list)
        chat_container = QWidget()
        chat_container.setLayout(chat_layout)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def send_message(self):
        message = self.message_input.text()
        if message:
            self.chat_display.append(f"You: {message}")
            self.message_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Применение темы Material Design
    apply_stylesheet(app, theme='dark_teal.xml')

    window = ChatApplication()
    window.show()
    sys.exit(app.exec_())