import sys
import subprocess
import logging
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet
from registration_window import RegistrationWindow
from login_window import LoginWindow
from main_window import MainWindow

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        apply_stylesheet(self.app, theme='dark_teal.xml')

        # Инициализируем окна
        self.registration_window = RegistrationWindow()
        self.login_window = LoginWindow()
        self.main_window = None  # Инициализируем позже после успешного входа

        # Устанавливаем сигналы для переключения окон
        self.registration_window.open_login_signal.connect(self.show_login)
        self.login_window.open_registration_signal.connect(self.show_registration)
        self.login_window.successful_login_signal.connect(self.show_main)

        # Начальное окно - регистрация
        self.show_registration()

    def show_registration(self):
        logging.info("Открытие окна регистрации")
        self.login_window.close()
        self.registration_window.show()

    def show_login(self):
        logging.info("Открытие окна входа")
        self.registration_window.close()
        self.login_window.show()

    def show_main(self, user_id):
        logging.info("Успешный вход в систему, открытие главного окна")
        self.login_window.close()
        self.main_window = MainWindow(user_id)
        self.main_window.show()

    def run(self):
        # Запуск основного цикла приложения
        exit_code = self.app.exec_()
        self.cleanup()
        sys.exit(exit_code)

    def cleanup(self):
        logging.info("Завершение приложения")
        # Если вы запускали какие-либо фоновые процессы, завершите их здесь