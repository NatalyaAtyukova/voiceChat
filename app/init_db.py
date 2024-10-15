# init_db.py
import sys
import asyncio
from app.database import engine, Base
from app import models  # Импортируем модели, чтобы SQLAlchemy знал о них

# Добавляем корневую папку проекта в sys.path для корректного импорта модулей
sys.path.append("..")

async def init_db():
    async with engine.begin() as conn:
        # Создание всех таблиц, описанных в моделях
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())