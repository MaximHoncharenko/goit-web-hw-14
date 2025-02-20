from sqlalchemy.orm import Session
import models
import schemas
from fastapi import HTTPException, status
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Створення нового контакту
def create_contact(db: Session, contact: schemas.ContactCreate, owner_id: int):
    db_contact = models.Contact(
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone_number=contact.phone_number,
        birthday=contact.birthday,
        additional_info=contact.additional_info,
        owner_id=owner_id
    )
    try:
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return db_contact


# Отримання всіх контактів поточного користувача
def get_contacts(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Contact).filter(models.Contact.owner_id == owner_id).offset(skip).limit(limit).all()


# Отримання контакту за id для поточного користувача
def get_contact(db: Session, contact_id: int, owner_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == owner_id).first()


# Оновлення контакту
def update_contact(db: Session, contact_id: int, contact: schemas.ContactUpdate, owner_id: int):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == owner_id).first()
    if not db_contact:
        raise ValueError("Contact not found")
    
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == owner_id).first()
    if db_contact:
        if contact.first_name:
            db_contact.first_name = contact.first_name
        if contact.last_name:
            db_contact.last_name = contact.last_name
        if contact.email:
            db_contact.email = contact.email
        if contact.phone_number:
            db_contact.phone_number = contact.phone_number
        if contact.birthday:
            db_contact.birthday = contact.birthday
        if contact.additional_info:
            db_contact.additional_info = contact.additional_info

        db.commit()
        db.refresh(db_contact)
    return db_contact


# Видалення контакту
def delete_contact(db: Session, contact_id: int, owner_id: int):
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == owner_id).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def update_user_avatar(db: Session, user_id: int, avatar_url: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.avatar_url = avatar_url
        db.commit()
        db.refresh(db_user)
    return db_user

# Генерація випадкового коду
def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Збереження коду верифікації в БД
def create_verification_code(db: Session, user_id: int):
    code = generate_verification_code()
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.verification_code = code
        db.commit()
        db.refresh(db_user)
        return code
    return None

def send_verification_email(email: str, verification_code: str):
    msg = MIMEMultipart()
    msg['From'] = 'your-email@example.com'
    msg['To'] = email
    msg['Subject'] = 'Email Verification'

    body = f"Your verification code is: {verification_code}"
    msg.attach(MIMEText(body, 'plain'))

    # Відправка email
    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login('your-email@example.com', 'your-email-password')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error sending verification email")