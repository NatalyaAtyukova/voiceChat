import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from login_window import LoginWindow

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