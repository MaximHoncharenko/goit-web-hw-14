"""
Основний файл FastAPI для керування користувачами та контактами.
Містить ендпоінти для реєстрації, автентифікації, підтвердження email, обмеження запитів, управління контактами тощо.
"""

from typing import Pattern
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import List
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader
import os
import logging
import secrets
from fastapi import File, UploadFile
from fastapi import Request

import models
import crud
import schemas
from crud import send_verification_email
from models import User

# Завантаження змінних середовища
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Ініціалізація бази даних
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)

# Ініціалізація FastAPI
app = FastAPI()

# Налаштування CORS
token_auth_scheme = OAuth2PasswordBearer(tokenUrl="login")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обмеження швидкості
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Налаштування безпеки
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Налаштування Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Налаштування логування
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Функція для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функція отримання поточного користувача
def get_current_user(db: Session = Depends(get_db), token: str = Depends(token_auth_scheme)):
    """Отримання поточного користувача за токеном."""
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Токен не містить email")
            raise credentials_exception
    except JWTError:
        logger.warning("Помилка JWT при розборі токена")
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        logger.warning(f"Користувача {email} не знайдено")
        raise credentials_exception
    return user

@app.get("/contacts/", response_model=List[schemas.ContactResponse])
@limiter.limit("5/minute")
def get_contacts(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Отримання всіх контактів поточного користувача."""
    return db.query(models.Contact).filter(models.Contact.owner_id == current_user.id).all()


# Функція створення токену доступу
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Створення access token для користувача."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Функція хешування пароля
def hash_password(password: str) -> str:
    """Хешування пароля за допомогою bcrypt."""
    return pwd_context.hash(password)

# Реєстрація користувача
@app.post("/register/")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    # Перевірка наявності користувача з таким email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    hashed_password = hash_password(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

# Оновлення аватара користувача
@app.put("/update_avatar/")
async def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Оновлення аватара користувача через Cloudinary."""
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Only PNG and JPEG are allowed.")

    try:
        upload_result = cloudinary.uploader.upload(file.file)
        avatar_url = upload_result['secure_url']
    except Exception:
        raise HTTPException(status_code=500, detail="Error uploading image to Cloudinary")

    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return {"message": "Avatar updated successfully", "avatar_url": avatar_url}

# Обробник перевищення ліміту запитів
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Обробка перевищення ліміту запитів."""
    return JSONResponse(status_code=429, content={"detail": "Занадто багато запитів! Спробуйте пізніше."})
