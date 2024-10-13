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

# Новые схемы для работы с друзьями и запросами на дружбу

# Схема для создания дружбы
class FriendshipCreate(BaseModel):
    user_id: int
    friend_id: int

# Схема для отображения дружеской связи
class FriendshipResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    friend_username: Optional[str]

    class Config:
        from_attributes = True

# Схема для создания запроса на добавление в друзья
class FriendRequestCreate(BaseModel):
    sender_id: int
    receiver_id: int

# Схема для отображения информации о запросе на добавление в друзья
class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str  # например, "pending", "accepted", "rejected"
    timestamp: datetime
    sender_username: Optional[str]
    receiver_username: Optional[str]

    class Config:
        from_attributes = True