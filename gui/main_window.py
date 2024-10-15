import requests
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QListWidget, \
    QListWidgetItem, QSplitter, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from websocket_listener import WebSocketListener

# Настройка логирования
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Вспомогательная функция для обработки GET-запросов с логированием ошибок
def safe_get(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"GET request failed. URL: {url}, Params: {params}, Error: {e}")
        return None

# Вспомогательная функция для обработки POST-запросов с логированием ошибок
def safe_post(url, json=None):
    try:
        response = requests.post(url, json=json)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"POST request failed. URL: {url}, Data: {json}, Error: {e}")
        return None

# Вспомогательная функция для обработки PUT-запросов с логированием ошибок
def safe_put(url, json=None):
    try:
        response = requests.put(url, json=json)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"PUT request failed. URL: {url}, Data: {json}, Error: {e}")
        return None


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
        self.processed_request_ids = set()  # Инициализация для отслеживания ID запросов на дружбу
        self.initUI()
        self.load_contacts()

        # WebSocketListener для получения сообщений в реальном времени
        self.websocket_listener = WebSocketListener(self.chat_display, self.user_id)
        self.websocket_listener.start()

        # Таймер для проверки новых запросов на дружбу
        self.friend_request_timer = QTimer(self)
        self.friend_request_timer.timeout.connect(self.load_friend_requests)
        self.friend_request_timer.start(5000)  # Проверка каждые 30 секунд

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
        url = f"http://127.0.0.1:8000/users/{self.user_id}/friends/"
        response = safe_get(url)
        if response:
            friends = response.json()
            self.contact_list.clear()
            for friend in friends:
                friend_item = QListWidgetItem(f"{friend['username']} (Friend)")
                self.contact_list.addItem(friend_item)
                self.friends.add(friend['id'])  # Добавление в локальный список друзей
        else:
            QMessageBox.warning(self, "Error", "Failed to load contacts.")

    def on_contact_selected(self, item):
        selected_username = item.text()
        response = safe_get("http://127.0.0.1:8000/users/")
        if response:
            users = response.json()
            for user in users:
                if user['username'] == selected_username:
                    self.selected_contact_id = user['id']
                    break
            self.load_messages()
        else:
            QMessageBox.warning(self, "Error", "Failed to retrieve user information.")

    def load_messages(self):
        if self.selected_contact_id is None:
            return

        url = f"http://127.0.0.1:8000/messages"
        params = {
            "sender_id": self.user_id,
            "receiver_id": self.selected_contact_id
        }
        response = safe_get(url, params=params)
        if response:
            messages = response.json()
            self.chat_display.clear()
            for message in messages:
                is_sender = message["sender_id"] == self.user_id
                sender_name = "You" if is_sender else message["sender_username"]
                text = f"{sender_name}: {message['content']}"
                self.add_message(text, is_sender)
        else:
            QMessageBox.warning(self, "Error", "Failed to load messages.")

    def search_users(self):
        query = self.search_input.text()
        response = safe_get(f"http://127.0.0.1:8000/users?query={query}")
        if response:
            users = response.json()
            self.contact_list.clear()
            for user in users:
                user_item = QListWidgetItem()
                if user['id'] in self.friends:
                    user_item.setText(f"{user['username']} (Friend)")
                else:
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
            QMessageBox.warning(self, "Error", "Failed to search users.")

    def send_message(self):
        message = self.message_input.text()
        if not message or self.selected_contact_id is None:
            QMessageBox.warning(self, "Error", "Select a contact and enter a message")
            return

        url = "http://127.0.0.1:8000/messages/"
        data = {
            "sender_id": self.user_id,
            "receiver_id": self.selected_contact_id,
            "content": message
        }
        response = safe_post(url, json=data)
        if response:
            self.add_message(f"You: {message}", is_sender=True)
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to send message.")

    def load_friend_requests(self):
        url = f"http://127.0.0.1:8000/friend_requests/{self.user_id}"
        response = safe_get(url)
        if response:
            friend_requests = response.json()
            for req in friend_requests:
                if req["id"] not in self.processed_request_ids:
                    self.show_friend_request(req["sender_id"], req["sender_username"])
                    self.processed_request_ids.add(req["id"])
        else:
            QMessageBox.warning(self, "Error", "Failed to load friend requests.")

    def accept_friend_request(self, sender_id):
        url = f"http://127.0.0.1:8000/friend_requests/{sender_id}?status=accepted"
        response = safe_put(url)
        if response:
            QMessageBox.information(self, "Success", "Friend request accepted")
            self.load_contacts()  # Обновление списка друзей после принятия запроса
            self.remove_friend_request_items(sender_id)  # Удаление UI-запроса
        else:
            QMessageBox.warning(self, "Error", "Failed to accept friend request")

    def reject_friend_request(self, sender_id):
        url = f"http://127.0.0.1:8000/friend_requests/{sender_id}?status=rejected"
        response = safe_put(url)
        if response:
            QMessageBox.information(self, "Success", "Friend request rejected")
            self.remove_friend_request_items(sender_id)  # Удаление UI-запроса
        else:
            QMessageBox.warning(self, "Error", "Failed to reject friend request")

    def show_friend_request(self, sender_id, sender_username):
        # Показ сообщения о запросе на дружбу в окне чата
        request_message = f"{sender_username} has sent you a friend request."
        item = QListWidgetItem(request_message)
        self.chat_display.addItem(item)

        # Создание кнопок для принятия и отклонения запроса
        accept_button = QPushButton("Accept")
        reject_button = QPushButton("Reject")

        # Привязываем кнопки к функциям, передавая sender_id
        accept_button.clicked.connect(lambda _, uid=sender_id: self.accept_friend_request(uid))
        reject_button.clicked.connect(lambda _, uid=sender_id: self.reject_friend_request(uid))

        # Создание виджета для кнопок
        layout = QHBoxLayout()
        layout.addWidget(accept_button)
        layout.addWidget(reject_button)
        button_widget = QWidget()
        button_widget.setLayout(layout)
        button_item = QListWidgetItem()
        button_item.setSizeHint(button_widget.sizeHint())
        self.chat_display.addItem(button_item)
        self.chat_display.setItemWidget(button_item, button_widget)

        # Добавление в словарь для последующего удаления (если не было инициализировано ранее)
        if not hasattr(self, 'friend_request_items'):
            self.friend_request_items = {}
        self.friend_request_items[sender_id] = (item, button_item)

    def add_friend(self, user_id):
        url = f"http://127.0.0.1:8000/friend_requests/"
        data = {
            "sender_id": self.user_id,
            "receiver_id": user_id
        }
        response = safe_post(url, json=data)
        if response:
            QMessageBox.information(self, "Success", "Friend request sent successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to send friend request")

    def remove_friend_request_items(self, sender_id):
        # Удаление элементов сообщения и кнопок, связанных с запросом на дружбу
        if sender_id in self.friend_request_items:
            request_message_item, button_item = self.friend_request_items.pop(sender_id)
            self.chat_display.takeItem(self.chat_display.row(request_message_item))
            self.chat_display.takeItem(self.chat_display.row(button_item))