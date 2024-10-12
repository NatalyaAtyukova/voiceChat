# app/main.py

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
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
        # Хеширование пароля
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
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Проверка введенного пароля
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"message": "Login successful", "user_id": db_user.id}

# Маршрут для отправки сообщения
@app.post("/messages/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    db_message = models.Message(
        sender_id=message.sender_id,
        content=message.content,
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Маршрут для получения сообщений
@app.get("/messages/", response_model=List[schemas.MessageResponse])
def get_messages(
    db: Session = Depends(get_db),
    limit: int = Query(100, description="Limit the number of messages returned"),
    offset: int = Query(0, description="Offset for pagination")
):
    messages = db.query(models.Message).order_by(models.Message.timestamp).offset(offset).limit(limit).all()
    return messages