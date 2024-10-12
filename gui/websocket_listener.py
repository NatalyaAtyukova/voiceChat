import asyncio
import json
import websockets
from PyQt5.QtCore import QThread

class WebSocketListener(QThread):
    def __init__(self, chat_display, user_id):
        super().__init__()
        self.chat_display = chat_display
        self.user_id = user_id

    async def listen(self):
        uri = f"ws://127.0.0.1:8000/ws/chat/{self.user_id}"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        sender = data.get("sender_username", "Unknown")
                        content = data.get("content", "")
                        self.chat_display.append(f"{sender}: {content}")
            except websockets.ConnectionClosedError:
                self.chat_display.append("Connection to server closed. Reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                self.chat_display.append(f"Error: {e}")
                await asyncio.sleep(2)

    def run(self):
        asyncio.run(self.listen())