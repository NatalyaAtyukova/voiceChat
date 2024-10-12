from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas
from .database import SessionLocal, engine, Base
from passlib.context import CryptContext
from datetime import datetime

app = FastAPI()

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для хеширования пароля
def hash_password(password: str):
    return pwd_context.hash(password)

# Функция для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Регистрация нового пользователя
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    try:
        hashed_password = hash_password(user.password)
        db_user = models.User(username=user.username, hashed_password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        print("Error during registration:", str(e))
        raise HTTPException(status_code=500, detail="An error occurred during registration")

    return db_user

# Авторизация пользователя
@app.post("/login/")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"message": "Login successful", "user_id": db_user.id}

# Маршрут для отправки сообщения
@app.post("/messages/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    db_sender = db.query(models.User).filter(models.User.id == message.sender_id).first()
    db_receiver = db.query(models.User).filter(models.User.id == message.receiver_id).first()

    if not db_sender:
        raise HTTPException(status_code=404, detail=f"Sender with ID {message.sender_id} not found")
    if not db_receiver:
        raise HTTPException(status_code=404, detail=f"Receiver with ID {message.receiver_id} not found")

    try:
        db_message = models.Message(
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            content=message.content,
            timestamp=datetime.utcnow()
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        return schemas.MessageResponse(
            id=db_message.id,
            sender_id=db_message.sender_id,
            receiver_id=db_message.receiver_id,
            sender_username=db_sender.username,
            receiver_username=db_receiver.username,
            content=db_message.content,
            timestamp=db_message.timestamp
        )
    except Exception as e:
        print("Error while creating message:", str(e))
        raise HTTPException(status_code=500, detail="Failed to send message")

# Маршрут для получения сообщений
@app.get("/messages/", response_model=List[schemas.MessageResponse])
def get_messages(
        db: Session = Depends(get_db),
        sender_id: Optional[int] = None,
        receiver_id: Optional[int] = None,
        limit: int = Query(100, description="Limit the number of messages returned"),
        offset: int = Query(0, description="Offset for pagination")
):
    query = db.query(models.Message).order_by(models.Message.timestamp)

    if sender_id:
        query = query.filter(models.Message.sender_id == sender_id)
    if receiver_id:
        query = query.filter(models.Message.receiver_id == receiver_id)

    messages = query.offset(offset).limit(limit).all()
    return [
        schemas.MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            sender_username=msg.sender.username,
            receiver_username=msg.receiver.username,
            content=msg.content,
            timestamp=msg.timestamp
        )
        for msg in messages
    ]

# Маршрут для поиска пользователей
@app.get("/users/", response_model=List[schemas.UserResponse])
def search_users(query: Optional[str] = None, db: Session = Depends(get_db)):
    if query:
        users = db.query(models.User).filter(models.User.username.contains(query)).all()
    else:
        users = db.query(models.User).all()
    return users