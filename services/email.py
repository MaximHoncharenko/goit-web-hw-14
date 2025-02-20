import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Завантажуємо змінні середовища
load_dotenv()

# Змінні для налаштувань SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER")  # Твоя email адреса
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Твій пароль для SMTP

# Функція для надсилання email з токеном підтвердження
def send_verification_email(to_email: str, token: str):
    subject = "Підтвердження електронної пошти"
    body = f"Перейдіть за цим посиланням, щоб підтвердити свою електронну пошту: http://yourfrontend.com/verify-email/{token}"
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Підключення до сервера SMTP і відправка листа
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Захищений режим
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        raise Exception(f"Не вдалося надіслати email: {str(e)}")
