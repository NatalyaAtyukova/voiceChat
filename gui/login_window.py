from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
import requests
import logging

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

class AsyncLoginThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password

    def run(self):
        try:
            response = requests.post("http://127.0.0.1:8000/login/", json={"username": self.username, "password": self.password})
            if response.status_code == 200:
                data = response.json()  # успешный вход
            else:
                data = {"detail": response.text}  # ошибки сервера
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            data = {"detail": "Ошибка сети или неверный формат ответа"}
        self.finished.emit(data)

class LoginWindow(QWidget):
    open_registration_signal = pyqtSignal()  # Сигнал для открытия окна регистрации
    successful_login_signal = pyqtSignal(int)  # Сигнал для успешного входа с передачей user_id

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Login")
        self.setGeometry(100, 100, 300, 250)
        layout = QVBoxLayout()

        # Поля ввода для имени пользователя и пароля
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Кнопки входа и регистрации
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login_user)
        register_button = QPushButton("Don't have an account? Register")
        register_button.clicked.connect(self.open_registration)

        # Добавление виджетов в макет
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        self.setLayout(layout)

    def login_user(self):
        username, password = self.username_input.text(), self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password")
            return

        # Создаем поток для асинхронного выполнения запроса на вход
        self.login_thread = AsyncLoginThread(username, password)
        self.login_thread.finished.connect(self.handle_login_response)
        self.login_thread.start()

    def handle_login_response(self, response):
        if not response:
            QMessageBox.warning(self, "Error", "Не удалось получить ответ от сервера")
            return

        if "detail" in response:
            QMessageBox.warning(self, "Error", f"Failed to login: {response['detail']}")
        else:
            QMessageBox.information(self, "Success", "Login successful!")
            user_id = response.get("user_id")  # Получаем user_id из ответа
            if user_id is not None:
                self.successful_login_signal.emit(user_id)  # Отправляем сигнал успешного входа
            self.close()  # Закрытие окна входа после успешного входа

    def open_registration(self):
        self.open_registration_signal.emit()  # Отправка сигнала для открытия окна регистрации
        self.close()