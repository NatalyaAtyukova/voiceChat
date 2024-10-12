# app/schemas.py

from pydantic import BaseModel
from datetime import datetime

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

class MessageCreate(BaseModel):
    sender_id: int
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True