# user_interface.py

import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QTextEdit, QSplitter, QMessageBox
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

        # Левая панель для поиска и списка контактов
        contact_layout = QVBoxLayout()

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.on_search_input_changed)
        contact_layout.addWidget(self.search_input)

        # Список контактов
        self.contact_list = QListWidget()
        contact_layout.addWidget(self.contact_list)
        self.load_contacts()  # Загрузка контактов при инициализации

        # Правая панель для чата
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Поле ввода сообщения и кнопка отправки
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        chat_layout.addLayout(message_layout)

        # Разделитель для списка контактов и окна чата
        splitter = QSplitter(Qt.Horizontal)
        contact_container = QWidget()
        contact_container.setLayout(contact_layout)
        splitter.addWidget(contact_container)
        chat_container = QWidget()
        chat_container.setLayout(chat_layout)
        splitter.addWidget(chat_container)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_contacts(self, query=None):
        # Загрузка списка контактов, с опцией поиска
        url = "http://127.0.0.1:8000/users/"
        if query:
            url += f"?query={query}"
        response = requests.get(url)
        if response.status_code == 200:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                self.contact_list.addItem(user['username'])
        else:
            QMessageBox.warning(self, "Error", "Failed to load contacts")

    def on_search_input_changed(self):
        # Выполняет поиск при изменении текста в поле поиска
        query = self.search_input.text().strip()
        self.load_contacts(query=query)

    def send_message(self):
        message = self.message_input.text()
        if message:
            response = requests.post("http://127.0.0.1:8000/messages/", json={
                "sender_id": 1,  # Укажи ID текущего пользователя
                "content": message
            })
            if response.status_code == 200:
                self.chat_display.append(f"You: {message}")
                self.message_input.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to send message")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')
    window = ChatApplication()
    window.show()
    sys.exit(app.exec_())