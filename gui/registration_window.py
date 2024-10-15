from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
import requests

class RegistrationWindow(QWidget):
    open_login_signal = pyqtSignal()  # Сигнал для открытия окна входа

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Регистрация пользователя")
        self.setGeometry(100, 100, 300, 250)
        layout = QVBoxLayout()

        # Поле для имени пользователя
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Имя пользователя")

        # Поле для пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Кнопка для регистрации
        register_button = QPushButton("Регистрация")
        register_button.clicked.connect(self.register_user)

        # Кнопка для открытия окна входа
        login_button = QPushButton("Уже есть аккаунт? Войти")
        login_button.clicked.connect(self.open_login)

        # Добавление виджетов в макет
        layout.addWidget(QLabel("Имя пользователя"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Пароль"))
        layout.addWidget(self.password_input)
        layout.addWidget(register_button)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def register_user(self):
        username, password = self.username_input.text(), self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка ввода", "Пожалуйста, введите имя пользователя и пароль")
            return

        try:
            response = requests.post("http://127.0.0.1:8000/users/", json={"username": username, "password": password})
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован!")
            else:
                error_message = response.text  # Показываем ответ сервера
                QMessageBox.warning(self, "Ошибка", f"Не удалось зарегистрировать пользователя: {error_message}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сети: {str(e)}")

    def open_login(self):
        self.open_login_signal.emit()  # Отправка сигнала вместо прямого вызова окна входа
        self.close()