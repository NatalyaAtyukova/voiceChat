import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QListWidget, \
    QListWidgetItem, QSplitter, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from websocket_listener import WebSocketListener


class MessageWidget(QWidget):
    def __init__(self, text, is_sender):
        super().__init__()
        layout = QHBoxLayout()

        # Настройка выравнивания и фона для отправителя и получателя
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))

        if is_sender:
            label.setStyleSheet("background-color: #00a86b; padding: 10px; border-radius: 10px;")
            layout.addWidget(label, alignment=Qt.AlignRight)
        else:
            label.setStyleSheet("background-color: #00754a; padding: 10px; border-radius: 10px;")
            layout.addWidget(label, alignment=Qt.AlignLeft)

        self.setLayout(layout)


class MainWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.friends = set()  # Множество для хранения ID друзей
        self.selected_contact_id = None
        self.initUI()
        self.load_contacts()

        # WebSocketListener для получения сообщений в реальном времени
        self.websocket_listener = WebSocketListener(self.chat_display, self.user_id)
        self.websocket_listener.start()

        # Таймер для проверки новых запросов на дружбу
        self.friend_request_timer = QTimer(self)
        self.friend_request_timer.timeout.connect(self.load_friend_requests)
        self.friend_request_timer.start(30000)  # Проверка каждые 30 секунд

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
        self.chat_display = QListWidget()  # Используем QListWidget для отображения сообщений
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
        # Загрузка списка друзей
        try:
            response = requests.get(f"http://127.0.0.1:8000/users/{self.user_id}/friends/")
            if response.status_code == 200:
                friends = response.json()
                self.contact_list.clear()
                for friend in friends:
                    friend_item = QListWidgetItem(f"{friend['username']} (Friend)")
                    self.contact_list.addItem(friend_item)
                    self.friends.add(friend['id'])  # Добавление в локальный список друзей
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
                is_sender = message["sender_id"] == self.user_id
                sender_name = "You" if is_sender else message["sender_username"]
                text = f"{sender_name}: {message['content']}"
                self.add_message(text, is_sender)
        else:
            QMessageBox.warning(self, "Error", f"Failed to load messages: {response.status_code} - {response.text}")

    def search_users(self):
        # Поиск всех пользователей и отображение их с кнопкой "Добавить в друзья"
        query = self.search_input.text()
        response = requests.get(f"http://127.0.0.1:8000/users?query={query}")
        if response.status_code == 200:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                # Создание элемента для каждого пользователя
                user_item = QListWidgetItem(f"{user['username']}")

                # Проверка, является ли пользователь другом
                if user['id'] in self.friends:
                    user_item.setText(f"{user['username']} (Friend)")
                else:
                    # Если не друг, добавляем кнопку "Добавить"
                    add_friend_button = QPushButton("Add Friend")
                    add_friend_button.clicked.connect(lambda _, uid=user['id']: self.add_friend(uid))
                    item_widget = QWidget()
                    layout = QHBoxLayout(item_widget)
                    layout.addWidget(QLabel(user['username']))
                    layout.addWidget(add_friend_button)
                    item_widget.setLayout(layout)
                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())
                    self.contact_list.addItem(item)
                    self.contact_list.setItemWidget(item, item_widget)
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
            self.add_message(f"You: {message}", is_sender=True)
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to send message")

    def add_message(self, text, is_sender):
        # Добавление сообщения в чат
        message_widget = MessageWidget(text, is_sender)
        list_item = QListWidgetItem(self.chat_display)
        list_item.setSizeHint(message_widget.sizeHint())
        self.chat_display.addItem(list_item)
        self.chat_display.setItemWidget(list_item, message_widget)

    def load_contacts(self):
        # Загрузка списка друзей
        try:
            response = requests.get(f"http://127.0.0.1:8000/users/{self.user_id}/friends/")
            if response.status_code == 200:
                friends = response.json()
                self.contact_list.clear()
                for friend in friends:
                    friend_item = QListWidgetItem(f"{friend['username']} (Friend)")
                    self.contact_list.addItem(friend_item)
                    self.friends.add(friend['id'])  # Добавление в локальный список друзей
            else:
                QMessageBox.warning(self, "Error", f"Failed to load contacts: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Error", f"Failed to connect to server: {e}")

    def load_friend_requests(self):
        # Запрашиваем запросы на добавление в друзья для текущего пользователя
        response = requests.get(f"http://127.0.0.1:8000/friend_requests/{self.user_id}")
        if response.status_code == 200:
            friend_requests = response.json()
            for req in friend_requests:
                self.show_friend_request(req["sender_id"], req["sender_username"])
        else:
            QMessageBox.warning(self, "Error", "Failed to load friend requests")

    def show_friend_request(self, sender_id, sender_username):
        # Показ уведомления с запросом на добавление в друзья
        message = f"{sender_username} has sent you a friend request."
        accept_button = QPushButton("Accept")
        reject_button = QPushButton("Reject")
        accept_button.clicked.connect(lambda: self.accept_friend_request(sender_id))
        reject_button.clicked.connect(lambda: self.reject_friend_request(sender_id))
        QMessageBox.information(self, "Friend Request", message)

    def accept_friend_request(self, sender_id):
        response = requests.put(f"http://127.0.0.1:8000/friend_requests/{sender_id}", json={"status": "accepted"})
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Friend request accepted")
            self.load_contacts()  # Обновление списка друзей
        else:
            QMessageBox.warning(self, "Error", "Failed to accept friend request")

    def reject_friend_request(self, sender_id):
        response = requests.put(f"http://127.0.0.1:8000/friend_requests/{sender_id}", json={"status": "rejected"})
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Friend request rejected")
        else:
            QMessageBox.warning(self, "Error", "Failed to reject friend request")

    def search_users(self):
        query = self.search_input.text()
        response = requests.get(f"http://127.0.0.1:8000/users?query={query}")
        if response.status_code == 200:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                user_item = QListWidgetItem()
                if user['id'] in self.friends:
                    user_item.setText(f"{user['username']} (Friend)")
                else:
                    add_friend_button = QPushButton("Add Friend")
                    add_friend_button.clicked.connect(lambda _, uid=user['id']: self.send_friend_request(uid))
                    item_widget = QWidget()
                    layout = QHBoxLayout(item_widget)
                    layout.addWidget(QLabel(user['username']))
                    layout.addWidget(add_friend_button)
                    item_widget.setLayout(layout)
                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())
                    self.contact_list.addItem(item)
                    self.contact_list.setItemWidget(item, item_widget)
        else:
            QMessageBox.warning(self, "Error", "Failed to search users")

    def send_friend_request(self, user_id):
        response = requests.post(f"http://127.0.0.1:8000/friend_requests/", json={
            "sender_id": self.user_id,
            "receiver_id": user_id
        })
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Friend request sent successfully")
        else:
            QMessageBox.warning(self, "Error", f"Failed to send friend request")