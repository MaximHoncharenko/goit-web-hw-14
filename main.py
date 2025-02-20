from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from typing import List, Optional
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import logging
import secrets
from fastapi import File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

import models
import crud
import schemas
from crud import send_verification_email  # Import the function from the appropriate module

# URL для підключення до бази даних
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Створення engine для з'єднання з базою даних
engine = create_engine(DATABASE_URL)

# Створення сесії для виконання запитів
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Створення таблиць, якщо вони ще не існують
models.Base.metadata.create_all(bind=engine)

# Ініціалізація FastAPI
app = FastAPI()

# Додаємо middleware для CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Список дозволених доменів, "*" дозволяє всі
    allow_credentials=True,
    allow_methods=["*"],  # Дозволяємо всі HTTP методи (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Дозволяємо всі заголовки
)


# **Створюємо об'єкт лімітера**
limiter = Limiter(key_func=get_remote_address)

# **Додаємо middleware для обмеження швидкості**
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# **Хешування паролів**
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# **JWT-конфігурація**
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Завантажуємо змінні з .env
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# **Функція для отримання БД-сесії**
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# **Функція для отримання поточного користувача**
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
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

# **Отримання всіх контактів користувача з лімітом 5 запитів на хвилину**
@app.get("/contacts/", response_model=List[schemas.ContactResponse])
@limiter.limit("5/minute")

def get_contacts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Contact).filter(models.Contact.owner_id == current_user.id).all()

# **Функція для створення токена доступу (access token)**
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# **Функція для створення refresh токена**
def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# **Реєстрація користувача**
@app.post("/register/", status_code=status.HTTP_201_CREATED)
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    # Перевірка, чи вже існує користувач з таким email
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Генерація коду підтвердження
    verification_code = secrets.token_urlsafe(16)  # Генеруємо випадковий код підтвердження

    # Створення нового користувача
    hashed_password = pwd_context.hash(password)  # Хешування пароля за допомогою pwd_context
    new_user = models.User(
        email=email,
        hashed_password=hashed_password,
        verification_code=verification_code,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Відправка листа з кодом підтвердження
        send_verification_email(email, verification_code)

        return {"message": "User created successfully. Please verify your email."}
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user")
    
# **Авторизація користувача (отримання access token)**
@app.post("/login/")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# **Оновлення access токену за допомогою refresh токену**
@app.post("/refresh/")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

# **Створення нового контакту**
@app.post("/contacts/", response_model=schemas.ContactResponse)
@limiter.limit("3/minute")  # Обмеження: не більше 3 запитів на хвилину
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_contact(db=db, contact=contact, owner_id=current_user.id)

# **Отримання конкретного контакту**
@app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_contact = crud.get_contact(db=db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

# **Оновлення контакту**
@app.put("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_contact = crud.get_contact(db=db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    updated_contact = crud.update_contact(db=db, contact_id=contact_id, contact=contact)
    return updated_contact

# **Видалення контакту**
@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Спочатку отримуємо контакт, щоб перевірити власника
    db_contact = crud.get_contact(db=db, contact_id=contact_id)
    if db_contact is None or db_contact.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Contact not found")

    # Якщо перевірка пройдена, видаляємо контакт
    crud.delete_contact(db=db, contact_id=contact_id)
    return {"message": "Contact deleted successfully"}

# Додаємо middleware для обробки перевищення ліміту
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Занадто багато запитів! Спробуйте пізніше."}
    )

@app.post("/verify_email/")
def verify_email(email: str, verification_code: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if db_user.verification_code != verification_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    db_user.is_verified = True
    db_user.verification_code = None  # Видаляти код після підтвердження
    db.commit()

    return {"message": "Email verified successfully!"}

@app.put("/update_avatar/")
async def update_avatar(
    file: UploadFile = File(...),  # Приймаємо файл
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Перевірка типу файлу (наприклад, тільки зображення)
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Only PNG and JPEG are allowed.")

    # Завантажуємо зображення в Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(file.file)
        avatar_url = upload_result['secure_url']  # Отримуємо URL аватара після завантаження
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error uploading image to Cloudinary")

    # Оновлення аватара в базі даних
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)

    return {"message": "Avatar updated successfully", "avatar_url": avatar_url}