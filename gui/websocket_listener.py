import asyncio
import json
import websockets
from PyQt5.QtCore import QThread, pyqtSignal

class WebSocketListener(QThread):
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    connection_closed = pyqtSignal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.is_running = True  # Контрольный флаг для работы потока

    async def listen(self):
        uri = f"ws://127.0.0.1:8000/ws/chat/{self.user_id}"
        while self.is_running:
            try:
                async with websockets.connect(uri) as websocket:
                    while self.is_running:
                        message = await websocket.recv()
                        data = json.loads(message)
                        sender = data.get("sender_username", "Unknown")
                        content = data.get("content", "")
                        self.message_received.emit(f"{sender}: {content}")
            except websockets.ConnectionClosedError:
                self.connection_closed.emit()
                await asyncio.sleep(2)
            except Exception as e:
                self.error_occurred.emit(f"Error: {e}")
                await asyncio.sleep(2)

    def run(self):
        asyncio.run(self.listen())

    def stop(self):
        self.is_running = False  # Останавливает поток