# app/main.py

import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select  # Импорт select для корректного запроса
from typing import List, Optional
from . import models, schemas
from passlib.context import CryptContext
from datetime import datetime

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user_connections = {}

# Асинхронный движок и сессия для базы данных
DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@localhost/voicechat"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Зависимость для подключения к базе данных
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Асинхронные функции для WebSocket
async def connect_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    user_connections.setdefault(user_id, []).append(websocket)
    print(f"User {user_id} connected")

def disconnect_websocket(websocket: WebSocket, user_id: int):
    if user_id in user_connections:
        user_connections[user_id].remove(websocket)
        if not user_connections[user_id]:
            del user_connections[user_id]
    print(f"User {user_id} disconnected")

async def broadcast_message_to_user(user_id: int, message: dict):
    for connection in user_connections.get(user_id, []):
        try:
            await connection.send_json(message)
        except Exception as e:
            print(f"Error sending message to user {user_id}: {e}")

# Функции хеширования пароля
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Асинхронное создание пользователя
@app.post("/users/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Проверка на существующего пользователя
        stmt = select(models.User).where(models.User.username == user.username)
        result = await db.execute(stmt)
        db_user = result.scalars().first()
        if db_user:
            raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")

        # Создание нового пользователя
        hashed_password = hash_password(user.password)
        new_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"Ошибка создания пользователя: {e}")  # Логирование ошибки
        raise HTTPException(status_code=500, detail="Ошибка на сервере")

# Асинхронный вход пользователя
@app.post("/login/")
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User).where(models.User.username == user.username)
    result = await db.execute(stmt)
    db_user = result.scalars().first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Login successful", "user_id": db_user.id}

# Асинхронный поиск пользователей
@app.get("/users/", response_model=List[schemas.UserResponse])
async def search_users(query: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(models.User)
    if query:
        stmt = stmt.where(models.User.username.contains(query))
    result = await db.execute(stmt)
    return result.scalars().all()

# Асинхронное получение списка друзей
@app.get("/users/{user_id}/friends/", response_model=List[schemas.UserResponse])
async def get_friends(user_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(models.Friendship).where(
        (models.Friendship.user_id == user_id) | (models.Friendship.friend_id == user_id)
    )
    friendships = await db.execute(stmt)
    friend_ids = [
        f.friend_id if f.user_id == user_id else f.user_id for f in friendships.scalars().all()
    ]
    friends_stmt = select(models.User).where(models.User.id.in_(friend_ids))
    friends = await db.execute(friends_stmt)
    return friends.scalars().all()

# Асинхронная отправка сообщений
@app.post("/messages/", response_model=schemas.MessageResponse)
async def send_message(message: schemas.MessageCreate, db: AsyncSession = Depends(get_db)):
    db_sender = await db.get(models.User, message.sender_id)
    db_receiver = await db.get(models.User, message.receiver_id)

    if not db_sender or not db_receiver:
        raise HTTPException(status_code=404, detail="User not found")

    db_message = models.Message(
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)

    message_data = {
        "id": db_message.id,
        "sender_id": db_message.sender_id,
        "receiver_id": db_message.receiver_id,
        "content": db_message.content,
        "timestamp": db_message.timestamp.isoformat(),
        "sender_username": db_sender.username,
        "receiver_username": db_receiver.username
    }

    await broadcast_message_to_user(message.sender_id, message_data)
    await broadcast_message_to_user(message.receiver_id, message_data)

    return message_data

# Асинхронный WebSocket для чата
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await connect_websocket(websocket, user_id)
    try:
        async with AsyncSessionLocal() as db:
            while True:
                message_text = await websocket.receive_text()
                message_data = json.loads(message_text)
                await send_message(schemas.MessageCreate(**message_data), db=db)
    except WebSocketDisconnect:
        disconnect_websocket(websocket, user_id)