import asyncio
import aiohttp
import logging
from PyQt5.QtCore import QThread, pyqtSignal

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
                logging.error(f"Ошибка запроса: {e}")
                return None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(self.make_request())
        self.finished.emit(data)