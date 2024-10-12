import sys
import requests
import websockets
import asyncio
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QThread
from qt_material import apply_stylesheet

# Класс для обработки WebSocket соединения
class WebSocketListener(QThread):
    def __init__(self, chat_display, user_id):
        super().__init__()
        self.chat_display = chat_display
        self.user_id = user_id

    async def listen(self):
        uri = f"ws://127.0.0.1:8000/ws/chat/{self.user_id}"
        print("Connecting to WebSocket:", uri)  # Отладка
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print("Connected to WebSocket")  # Отладка
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        sender = data.get("sender_username", "Unknown")
                        content = data.get("content", "")
                        self.chat_display.append(f"{sender}: {content}")
            except websockets.ConnectionClosedError:
                self.chat_display.append("Connection to server closed. Reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                self.chat_display.append(f"Error: {e}")
                await asyncio.sleep(2)

    def run(self):
        asyncio.run(self.listen())
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

# Окно регистрации
class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Registration")
        self.setGeometry(100, 100, 300, 250)
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register_user)
        login_button = QPushButton("Already have an account? Login")
        login_button.clicked.connect(self.open_login_window)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)
        layout.addWidget(register_button)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def register_user(self):
        username, password = self.username_input.text(), self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password")
            return

        response = requests.post("http://127.0.0.1:8000/users/", json={"username": username, "password": password})
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "User registered successfully!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to register: {response.json().get('detail')}")

    def open_login_window(self):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()


# Окно входа
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Login")
        self.setGeometry(100, 100, 300, 200)
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login_user)

        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def login_user(self):
        username, password = self.username_input.text(), self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password")
            return

        response = requests.post("http://127.0.0.1:8000/login/", json={"username": username, "password": password})
        if response.status_code == 200:
            user_id = response.json().get("user_id")
            QMessageBox.information(self, "Success", "Login successful!")
            self.open_main_window(user_id)
        else:
            QMessageBox.warning(self, "Error", "Incorrect username or password")

    def open_main_window(self, user_id):
        self.main_window = MainWindow(user_id)
        self.main_window.show()
        self.close()


# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')  # Применяем Material Design тему

    # Создаем начальное окно регистрации
    window = RegistrationWindow()
    window.show()
    sys.exit(app.exec_())  # Запускаем главный цикл приложения