from pydantic import BaseModel
from datetime import date
from typing import Optional

class ContactCreate(BaseModel):
    """
    Schema for creating a new contact.
    
    Attributes:
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (str): The unique email of the contact.
        phone_number (str): The phone number of the contact.
        birthday (date): The birth date of the contact.
        additional_info (Optional[str]): Additional information about the contact.
    """
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True

class ContactResponse(ContactCreate):
    """
    Schema for returning a contact in API responses.
    
    Attributes:
        id (int): The unique identifier of the contact.
    """
    id: int

    class Config:
        orm_mode = True

class ContactSearch(BaseModel):
    """
    Schema for searching contacts.
    
    Attributes:
        first_name (Optional[str]): The first name to search for.
        last_name (Optional[str]): The last name to search for.
        email (Optional[str]): The email to search for.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

class ContactUpdate(BaseModel):
    """
    Schema for updating contact details.
    
    Attributes:
        first_name (Optional[str]): The updated first name of the contact.
        last_name (Optional[str]): The updated last name of the contact.
        email (Optional[str]): The updated email of the contact.
        phone_number (Optional[str]): The updated phone number of the contact.
        birthday (Optional[date]): The updated birth date of the contact.
        additional_info (Optional[str]): Additional updated information.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    Attributes:
        email (str): The email address of the user.
        password (str): The password of the user.
    """
    email: str
    password: str

    class Config:
        orm_mode = True

class UserResponse(BaseModel):
    """
    Schema for returning user information in API responses.
    
    Attributes:
        id (int): The unique identifier of the user.
        email (str): The email address of the user.
        created_at (date): The date when the user was created.
    """
    id: int
    email: str
    created_at: date

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    """
    Schema for user login credentials.
    
    Attributes:
        email (str): The email address of the user.
        password (str): The password of the user.
    """
    email: str
    password: str

class Token(BaseModel):
    """
    Schema for authentication token response.
    
    Attributes:
        access_token (str): The access token string.
        token_type (str): The type of the token (e.g., 'bearer').
    """
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    """
    Schema for email verification.
    
    Attributes:
        token (str): The verification token sent to the user's email.
    """
    token: str

class UserAvatarUpdate(BaseModel):
    """
    Schema for updating the user's avatar.
    
    Attributes:
        avatar_url (str): The URL of the new avatar image.
    """
    avatar_url: str

class UserBase(BaseModel):
    """
    Base schema for user-related responses.
    
    Attributes:
        email (str): The email address of the user.
        avatar_url (Optional[str]): The URL of the user's avatar.
    """
    email: str
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    """
    Extended schema for user responses.
    
    Attributes:
        id (int): The unique identifier of the user.
    """
    id: int

    class Config:
        orm_mode = True
