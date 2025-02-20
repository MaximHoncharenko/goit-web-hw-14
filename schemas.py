from pydantic import BaseModel
from datetime import date
from typing import Optional

# Модель для створення контакту
class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True

# Модель для відповіді на запит контакту
class ContactResponse(ContactCreate):
    id: int

    class Config:
        orm_mode = True

# Модель для пошукових запитів
class ContactSearch(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

# Модель для оновлення контакту
class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True

# Модель для реєстрації користувача
class UserCreate(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode = True

# Модель для відповіді на запит користувача (для авторизації)
class UserResponse(BaseModel):
    id: int
    email: str
    created_at: date

    class Config:
        orm_mode = True

# Модель для входу користувача
class UserLogin(BaseModel):
    email: str
    password: str

# Модель для відповіді з токеном
class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    token: str

class UserAvatarUpdate(BaseModel):
    avatar_url: str

class UserBase(BaseModel):
    email: str
    avatar_url: Optional[str] = None  # Додаємо URL аватара як опційне поле

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True