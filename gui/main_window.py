import asyncio
import aiohttp
import logging
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QListWidget, \
    QListWidgetItem, QSplitter, QLabel
from PyQt5.QtGui import QFont

# Настройка логирования
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")


class AsyncRequestThread(QThread):
    finished = pyqtSignal(object)  # Передача данных обратно в основной поток

    def __init__(self, url, method="get", params=None, json=None):
        super().__init__()
        self.url = url
        self.method = method
        self.params = params
        self.json = json

    async def make_request(self):
        async with aiohttp.ClientSession() as session:
            try:
                if self.method == "get":
                    async with session.get(self.url, params=self.params) as response:
                        data = await response.json()
                elif self.method == "post":
                    async with session.post(self.url, json=self.json) as response:
                        data = await response.json()
                elif self.method == "put":
                    async with session.put(self.url, json=self.json) as response:
                        data = await response.json()
                else:
                    data = None
                return data
            except aiohttp.ClientError as e:
                logging.error(f"Request failed: {e}")
                return None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(self.make_request())
        self.finished.emit(data)


class MessageWidget(QWidget):
    def __init__(self, text, is_sender):
        super().__init__()
        layout = QHBoxLayout()

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
        self.friends = set()
        self.selected_contact_id = None
        self.processed_request_ids = set()
        self.initUI()
        self.load_contacts()

    def initUI(self):
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)
        main_layout = QHBoxLayout(self)

        contact_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.search_users)
        contact_layout.addWidget(self.search_input)

        self.contact_list = QListWidget()
        self.contact_list.itemClicked.connect(self.on_contact_selected)
        contact_layout.addWidget(self.contact_list)

        chat_layout = QVBoxLayout()
        self.chat_display = QListWidget()
        chat_layout.addWidget(self.chat_display)

        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        chat_layout.addLayout(message_layout)

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
        self.contact_thread = AsyncRequestThread(url, method="get")
        self.contact_thread.finished.connect(self.update_contacts)
        self.contact_thread.start()

    def update_contacts(self, data):
        if data and isinstance(data, list):  # Проверка, что data не None и это список
            self.contact_list.clear()
            for friend in data:
                friend_item = QListWidgetItem(f"{friend['username']} (Friend)")
                self.contact_list.addItem(friend_item)
                self.friends.add(friend['id'])
        else:
            QMessageBox.warning(self, "Error", "Failed to load contacts.")

    def on_contact_selected(self, item):
        selected_username = item.text()
        self.selected_contact_id = next((user['id'] for user in self.friends if user['username'] == selected_username), None)
        self.load_messages()

    def load_messages(self):
        if not self.selected_contact_id:
            return

        url = f"http://127.0.0.1:8000/messages"
        params = {
            "sender_id": self.user_id,
            "receiver_id": self.selected_contact_id
        }
        self.message_thread = AsyncRequestThread(url, method="get", params=params)
        self.message_thread.finished.connect(self.update_messages)
        self.message_thread.start()

    def update_messages(self, messages):
        if messages:
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
        url = f"http://127.0.0.1:8000/users?query={query}"
        self.search_thread = AsyncRequestThread(url, method="get")
        self.search_thread.finished.connect(self.update_search_results)
        self.search_thread.start()

    def update_search_results(self, users):
        if users:
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
        if not message or not self.selected_contact_id:
            QMessageBox.warning(self, "Error", "Select a contact and enter a message")
            return

        url = "http://127.0.0.1:8000/messages/"
        data = {
            "sender_id": self.user_id,
            "receiver_id": self.selected_contact_id,
            "content": message
        }
        self.send_thread = AsyncRequestThread(url, method="post", json=data)
        self.send_thread.finished.connect(lambda response: self.handle_send_message(response, message))
        self.send_thread.start()

    def handle_send_message(self, response, message):
        if response is not None:  # Дополнительная проверка
            self.add_message(f"You: {message}", is_sender=True)
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Failed to send message.")

    def load_friend_requests(self):
        url = f"http://127.0.0.1:8000/friend_requests/{self.user_id}"
        self.friend_request_thread = AsyncRequestThread(url, method="get")
        self.friend_request_thread.finished.connect(self.update_friend_requests)
        self.friend_request_thread.start()

    def update_friend_requests(self, friend_requests):
        if friend_requests:
            for req in friend_requests:
                if req["id"] not in self.processed_request_ids:
                    self.show_friend_request(req["sender_id"], req["sender_username"])
                    self.processed_request_ids.add(req["id"])
        else:
            QMessageBox.warning(self, "Error", "Failed to load friend requests.")

    def accept_friend_request(self, sender_id):
        url = f"http://127.0.0.1:8000/friend_requests/{sender_id}?status=accepted"
        self.accept_request_thread = AsyncRequestThread(url, method="put")
        self.accept_request_thread.finished.connect(lambda response: self.handle_friend_request_response(response, sender_id))
        self.accept_request_thread.start()

    def reject_friend_request(self, sender_id):
        url = f"http://127.0.0.1:8000/friend_requests/{sender_id}?status=rejected"
        self.reject_request_thread = AsyncRequestThread(url, method="put")
        self.reject_request_thread.finished.connect(lambda response: self.handle_friend_request_response(response, sender_id))
        self.reject_request_thread.start()

    def handle_friend_request_response(self, response, sender_id):
        if response:
            QMessageBox.information(self, "Success", "Friend request processed successfully")
            self.load_contacts()  # Обновление списка друзей после принятия или отклонения запроса
            self.remove_friend_request_items(sender_id)  # Удаление UI-запроса
        else:
            QMessageBox.warning(self, "Error", "Failed to process friend request")

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

        # Добавление в словарь для последующего удаления
        if not hasattr(self, 'friend_request_items'):
            self.friend_request_items = {}
        self.friend_request_items[sender_id] = (item, button_item)

    def add_friend(self, user_id):
        url = f"http://127.0.0.1:8000/friend_requests/"
        data = {
            "sender_id": self.user_id,
            "receiver_id": user_id
        }
        self.add_friend_thread = AsyncRequestThread(url, method="post", json=data)
        self.add_friend_thread.finished.connect(lambda response: self.handle_add_friend(response))
        self.add_friend_thread.start()

    def handle_add_friend(self, response):
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