# app/main.py

import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
from .database import SessionLocal, engine, Base
from passlib.context import CryptContext
from datetime import datetime

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user_connections = {}

Base.metadata.create_all(bind=engine)


# Функция для подключения WebSocket
async def connect_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in user_connections:
        user_connections[user_id] = []
    user_connections[user_id].append(websocket)
    print(f"User {user_id} connected")


# Функция для отключения WebSocket
def disconnect_websocket(websocket: WebSocket, user_id: int):
    if user_id in user_connections:
        user_connections[user_id].remove(websocket)
        if not user_connections[user_id]:  # Если у пользователя нет активных подключений
            del user_connections[user_id]
    print(f"User {user_id} disconnected")


# Функция для отправки сообщения пользователю через WebSocket
async def broadcast_message_to_user(user_id: int, message: dict):
    if user_id in user_connections:
        for connection in user_connections[user_id]:
            try:
                await connection.send_json(message)
                print(f"Message sent to user {user_id}: {message}")
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")


# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Функции хеширования паролей
def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Создание пользователя
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Авторизация пользователя
@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Login successful", "user_id": db_user.id}


@app.post("/messages/", response_model=schemas.MessageResponse)
async def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    # Проверка существования отправителя и получателя
    db_sender = db.query(models.User).filter(models.User.id == message.sender_id).first()
    db_receiver = db.query(models.User).filter(models.User.id == message.receiver_id).first()

    if not db_sender or not db_receiver:
        raise HTTPException(status_code=404, detail="User not found")

    # Создание и сохранение сообщения
    db_message = models.Message(
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Данные для WebSocket
    message_data = {
        "id": db_message.id,
        "sender_id": db_message.sender_id,
        "receiver_id": db_message.receiver_id,
        "content": db_message.content,
        "timestamp": db_message.timestamp.isoformat(),
        "sender_username": db_sender.username,
        "receiver_username": db_receiver.username
    }

    # Отправка сообщения отправителю и получателю через WebSocket
    try:
        await broadcast_message_to_user(message.sender_id, message_data)
        await broadcast_message_to_user(message.receiver_id, message_data)
    except Exception as e:
        print("WebSocket error:", e)

    return message_data

# WebSocket для чата
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await connect_websocket(websocket, user_id)
    try:
        while True:
            # Получение сообщения через WebSocket
            message_text = await websocket.receive_text()
            print(f"Message received from user {user_id}: {message_text}")

            # Парсим сообщение и отправляем его
            try:
                message_data = json.loads(message_text)
                await send_message(schemas.MessageCreate(**message_data), db=SessionLocal())
            except Exception as e:
                print("Failed to process WebSocket message:", e)
    except WebSocketDisconnect:
        disconnect_websocket(websocket, user_id)


# Получение списка пользователей
@app.get("/users/", response_model=List[schemas.UserResponse])
def search_users(query: Optional[str] = None, db: Session = Depends(get_db)):
    if query:
        users = db.query(models.User).filter(models.User.username.contains(query)).all()
    else:
        users = db.query(models.User).all()
    return users


@app.get("/messages/", response_model=List[schemas.MessageResponse])
def get_messages(
        user_id: Optional[int] = Query(None, description="User ID for filtering messages"),
        # Устанавливаем user_id как необязательный
        db: Session = Depends(get_db),
        limit: int = Query(100, description="Limit the number of messages returned"),
        offset: int = Query(0, description="Offset for pagination")
):
    query = db.query(models.Message).order_by(models.Message.timestamp)

    # Фильтруем сообщения только для указанного пользователя, если user_id передан
    if user_id:
        query = query.filter(
            (models.Message.sender_id == user_id) | (models.Message.receiver_id == user_id)
        )

    messages = query.offset(offset).limit(limit).all()

    # Формируем ответы с именами отправителя и получателя
    message_responses = []
    for message in messages:
        sender = db.query(models.User).filter(models.User.id == message.sender_id).first()
        receiver = db.query(models.User).filter(models.User.id == message.receiver_id).first()

        message_responses.append(
            schemas.MessageResponse(
                id=message.id,
                sender_id=message.sender_id,
                receiver_id=message.receiver_id,
                content=message.content,
                timestamp=message.timestamp,
                sender_username=sender.username if sender else "Unknown",
                receiver_username=receiver.username if receiver else "Unknown"
            )
        )

    return message_responses

