# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Схемы для пользователей
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

# Схемы для сообщений
class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    sender_username: Optional[str]
    receiver_username: Optional[str]

    class Config:
        from_attributes = True

# Схемы для дружбы
class FriendshipCreate(BaseModel):
    user_id: int
    friend_id: int

class FriendshipResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    friend_username: Optional[str]

    class Config:
        from_attributes = True

# Схемы для запросов дружбы
class FriendRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    timestamp: datetime
    sender_username: Optional[str]
    receiver_username: Optional[str]

    class Config:
        from_attributes = True