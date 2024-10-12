import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QListWidget, QTextEdit, QSplitter
from PyQt5.QtCore import Qt
from websocket_listener import WebSocketListener

# Окно основного чата
class MainWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.selected_contact_id = None
        self.initUI()
        self.load_contacts()

        # WebSocketListener для получения сообщений в реальном времени
        self.websocket_listener = WebSocketListener(self.chat_display, self.user_id)
        self.websocket_listener.start()

    def initUI(self):
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)
        main_layout = QHBoxLayout(self)

        # Левый раздел для контактов
        contact_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.search_users)
        contact_layout.addWidget(self.search_input)

        self.contact_list = QListWidget()
        self.contact_list.itemClicked.connect(self.on_contact_selected)
        contact_layout.addWidget(self.contact_list)

        # Правый раздел для чата
        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        chat_layout.addLayout(message_layout)

        # Разделение окна на два сегмента
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

    def load_contacts(self):
        # Загрузка списка пользователей
        try:
            response = requests.get("http://127.0.0.1:8000/users/")
            if response.status_code == 200:
                users = response.json()
                self.contact_list.clear()
                for user in users:
                    self.contact_list.addItem(user['username'])
            else:
                QMessageBox.warning(self, "Error", f"Failed to load contacts: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Error", f"Failed to connect to server: {e}")

    def on_contact_selected(self, item):
        # Обновление выбранного пользователя и загрузка его сообщений
        selected_username = item.text()
        response = requests.get("http://127.0.0.1:8000/users/")
        users = response.json()
        for user in users:
            if user['username'] == selected_username:
                self.selected_contact_id = user['id']
                break
        self.load_messages()

    def load_messages(self):
        # Загрузка сообщений с выбранным контактом
        if self.selected_contact_id is None:
            return

        response = requests.get(
            f"http://127.0.0.1:8000/messages", params={
                "sender_id": self.user_id,
                "receiver_id": self.selected_contact_id
            })
        if response.status_code == 200:
            messages = response.json()
            self.chat_display.clear()
            for message in messages:
                sender_name = "You" if message["sender_id"] == self.user_id else message["sender_username"]
                self.chat_display.append(f"{sender_name}: {message['content']}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load messages: {response.status_code} - {response.text}")

    def search_users(self):
        # Поиск пользователей
        query = self.search_input.text()
        response = requests.get(f"http://127.0.0.1:8000/users?query={query}")
        if response.status_code == 200:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                self.contact_list.addItem(user['username'])
        else:
            QMessageBox.warning(self, "Error", "Failed to search users")

    def send_message(self):
        # Отправка сообщения выбранному контакту
        message = self.message_input.text()
        if not message or self.selected_contact_id is None:
            QMessageBox.warning(self, "Error", "Select a contact and enter a message")
            return

        response = requests.post("http://127.0.0.1:8000/messages/", json={
            "sender_id": self.user_id,
            "receiver_id": self.selected_contact_id,
            "content": message
        })
        if response.status_code == 200:
            self.chat_display.append(f"You: {message}")
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to send message")