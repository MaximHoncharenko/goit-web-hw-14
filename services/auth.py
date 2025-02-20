from fastapi import HTTPException, status
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from models import User  # Adjust the import according to your project structure

# Функція для надсилання email
def send_email(to_email: str, token: str):
    """Надсилає email з токеном для верифікації."""
    from_email = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    # Створення листа
    subject = "Підтвердження електронної пошти"
    body = f"Будь ласка, використайте наступний токен для підтвердження вашої електронної пошти: {token}"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        # Підключення до SMTP сервера (для Gmail)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, email_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка при надсиланні email."
        )

# Функція для створення токена підтвердження email
def create_email_verification_token(email: str) -> str:
    """Генерує токен для підтвердження email."""
    # Тут має бути логіка генерації токена
    return "dummy_token"

# Маршрут для надсилання токена підтвердження email
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

# Функція для перевірки токена підтвердження email
def verify_email_token(token: str) -> str:
    """Перевіряє токен підтвердження email."""
    # Тут має бути логіка перевірки токена
    return "dummy_email@example.com"

router = APIRouter()

class EmailVerificationRequest(BaseModel):
    email: str

@router.post("/send-verification-email/")
async def send_verification_email_route(email: EmailStr):
    # Створюємо токен для підтвердження email
    token = create_email_verification_token(email)
    
    # Надсилаємо email з токеном
    try:
        send_email(email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка при надсиланні email: {str(e)}")
    
    return {"message": "Лист з токеном підтвердження надіслано на вашу електронну пошту."}

@router.get("/verify-email/{token}")
async def verify_email(token: str):
    try:
        # Перевіряємо токен
        email = verify_email_token(token)
        
        # Знаходимо користувача за email і оновлюємо його статус верифікації
        user = await User.get(email=email)
        if user is None:
            raise HTTPException(status_code=404, detail="Користувача не знайдено.")
        
        user.is_verified = True
        await user.save()

        return {"message": "Електронну пошту успішно підтверджено!"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Невірний токен підтвердження.")