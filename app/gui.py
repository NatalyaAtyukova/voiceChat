# gui.py

import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidget, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt
from qt_material import apply_stylesheet  # Импорт для Material Design

class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Registration")
        self.setGeometry(100, 100, 300, 250)

        layout = QVBoxLayout()

        self.username_label = QLabel("Username")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("Password")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.login_button = QPushButton("Already have an account? Login")
        self.login_button.clicked.connect(self.open_login_window)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def register_user(self):
        username = self.username_input.text()
        password = self.password_input.text()

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


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Login")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.username_label = QLabel("Username")
        self.username_input = QLineEdit()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QLabel("Password")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login_user)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login_user(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password")
            return

        response = requests.post("http://127.0.0.1:8000/login/", json={"username": username, "password": password})

        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Login successful!")
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Error", "Incorrect username or password")

    def open_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_contacts()  # Загружаем список контактов при запуске окна

    def initUI(self):
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout(self)

        # Левая панель для поиска и списка контактов
        contact_layout = QVBoxLayout()

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.search_users)  # Связываем ввод с методом поиска
        contact_layout.addWidget(self.search_input)

        # Список контактов
        self.contact_list = QListWidget()
        contact_layout.addWidget(self.contact_list)

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

    def load_contacts(self):
        # Загрузка начального списка контактов
        response = requests.get("http://127.0.0.1:8000/users/")
        if response.status_code == 200:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                self.contact_list.addItem(user['username'])
        else:
            QMessageBox.warning(self, "Error", "Failed to load contacts")

    def search_users(self):
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
        message = self.message_input.text()
        receiver_id = 2  # Временно установите ID получателя, например, `2`
        sender_id = 1  # Укажите ID текущего пользователя

        if message:
            response = requests.post("http://127.0.0.1:8000/messages/", json={
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": message
            })
            if response.status_code == 200:
                self.chat_display.append(f"You: {message}")
                self.message_input.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to send message")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Применяем тему Material Design
    apply_stylesheet(app, theme='dark_teal.xml')

    window = RegistrationWindow()
    window.show()
    sys.exit(app.exec_())