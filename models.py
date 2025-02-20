from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Базовий клас для всіх моделей
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    avatar_url = Column(String, nullable=True)  # Поле для аватара користувача
    is_verified = Column(Boolean, default=False)  # Нове поле для верифікації email
    verification_code = Column(String, nullable=True)  # Код для підтвердження email
    # Зв'язок один-до-багатьох з контактами
    contacts = relationship("Contact", back_populates="owner")


class Contact(Base):
    __tablename__ = "contacts"  # Назва таблиці в базі даних

    # Опис полів таблиці
    id = Column(Integer, primary_key=True, index=True)  # Унікальний ідентифікатор
    first_name = Column(String, index=True)  # Ім'я контакту
    last_name = Column(String, index=True)  # Прізвище контакту
    email = Column(String, unique=True, index=True)  # Електронна адреса контакту
    phone_number = Column(String)  # Номер телефону контакту
    birthday = Column(Date)  # Дата народження контакту
    additional_info = Column(Text, nullable=True)  # Додаткові дані (необов'язкові)
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата створення контакту

    # Нове поле для зв’язку контакту з користувачем
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="contacts")  # Власник контакту


# Відповідь API для контактів
class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date  # Якщо хочете, щоб це було як об'єкт типу `date`
    additional_info: str | None
    created_at: datetime  # Додаємо поле створення контакту

    class Config:
        orm_mode = True
