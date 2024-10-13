# app/main.py

import json
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
from .database import SessionLocal, engine, Base
from passlib.context import CryptContext
from datetime import datetime
from .schemas import FriendRequestCreate

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

# Добавление друзей
@app.post("/friends/")
def add_friend(user_id: int, friend_id: int, db: Session = Depends(get_db)):
    # Дополните проверку на существование, добавив вывод для отладки
    user = db.query(models.User).filter(models.User.id == user_id).first()
    friend = db.query(models.User).filter(models.User.id == friend_id).first()

    if not user or not friend:
        print(f"User {user_id} or friend {friend_id} not found in database.")
        raise HTTPException(status_code=404, detail="User not found")

    # Проверьте наличие дружбы и добавьте вывод для отладки
    existing_friendship = db.query(models.Friendship).filter(
        models.Friendship.user_id == user_id,
        models.Friendship.friend_id == friend_id
    ).first()
    if existing_friendship:
        print(f"User {user_id} and friend {friend_id} are already friends.")
        raise HTTPException(status_code=400, detail="Already friends")

    # Добавление в таблицу Friendship
    friendship = models.Friendship(user_id=user_id, friend_id=friend_id)
    db.add(friendship)
    db.commit()
    return {"message": "Friend added successfully"}

@app.post("/friend_requests/")
def send_friend_request(request: FriendRequestCreate, db: Session = Depends(get_db)):
    # Используйте request.sender_id и request.receiver_id
    existing_request = db.query(models.FriendRequest).filter(
        models.FriendRequest.sender_id == request.sender_id,
        models.FriendRequest.receiver_id == request.receiver_id,
        models.FriendRequest.status == "pending"
    ).first()
    if existing_request:
        raise HTTPException(status_code=400, detail="Friend request already sent")

    # Создание нового запроса на дружбу
    friend_request = models.FriendRequest(sender_id=request.sender_id, receiver_id=request.receiver_id)
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    return {"message": "Friend request sent successfully"}


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

@app.put("/friend_requests/{request_id}")
def respond_to_friend_request(request_id: int, status: str, db: Session = Depends(get_db)):
    # Поиск запроса на добавление в друзья
    friend_request = db.query(models.FriendRequest).filter(models.FriendRequest.id == request_id).first()

    if not friend_request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    if status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Обновление статуса запроса
    friend_request.status = status
    db.commit()

    # Если запрос принят, добавляем запись в таблицу Friendship
    if status == "accepted":
        # Создание взаимной дружбы (две записи для каждого пользователя)
        friendship1 = models.Friendship(
            user_id=friend_request.sender_id,
            friend_id=friend_request.receiver_id
        )
        friendship2 = models.Friendship(
            user_id=friend_request.receiver_id,
            friend_id=friend_request.sender_id
        )
        db.add_all([friendship1, friendship2])
        db.commit()
        return {"message": "Friend request accepted, friendship created"}

    # Если запрос отклонен, возвращаем сообщение об успешном отклонении
    return {"message": f"Friend request {status}"}