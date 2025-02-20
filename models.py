from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, constr
from typing import Pattern


# Base class for all models
Base = declarative_base()

class User(Base):
    """
    Represents a user in the database.
    
    Attributes:
        id (int): Unique identifier for the user.
        email (str): Unique email address of the user.
        hashed_password (str): Hashed password of the user.
        created_at (datetime): Timestamp of user creation.
        avatar_url (str | None): URL of the user's avatar.
        is_verified (bool): Indicates if the email is verified.
        verification_code (str | None): Verification code for email confirmation.
        contacts (List[Contact]): List of contacts associated with the user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    avatar_url = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    contacts = relationship("Contact", back_populates="owner")

class Contact(Base):
    """
    Represents a contact in the database.
    
    Attributes:
        id (int): Unique identifier for the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        email (str): Unique email address of the contact.
        phone_number (str): Contact's phone number.
        birthday (date): Contact's date of birth.
        additional_info (str | None): Additional information about the contact.
        created_at (datetime): Timestamp of contact creation.
        owner_id (int): ID of the user who owns the contact.
        owner (User): The user associated with the contact.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, nullable=False)  
    birthday = Column(Date)
    additional_info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="contacts")

class ContactResponse(BaseModel):
    """
    API response schema for a contact.
    
    Attributes:
        id (int): Unique identifier for the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        email (str): Email address of the contact.
        phone_number (str): Phone number of the contact.
        birthday (date): Date of birth of the contact.
        additional_info (str | None): Additional information about the contact.
        created_at (datetime): Timestamp of contact creation.
    """
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_info: str | None
    created_at: datetime

    class Config:
        orm_mode = True
