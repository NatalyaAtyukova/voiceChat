import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from main_window import MainWindow

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