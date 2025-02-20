import unittest
from fastapi.testclient import TestClient
from main import app  # імпортуємо додаток FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User  # імпортуємо необхідні моделі

# Налаштування тестової бази даних
DATABASE_URL = "sqlite:///./test.db"  # використовується SQLite для тестування
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Створення таблиць для тестів
Base.metadata.create_all(bind=engine)

# Створення клієнта FastAPI для тестів
client = TestClient(app)

class TestUserRegistration(unittest.TestCase):

    def setUp(self):
        """Ініціалізуємо тестову базу даних перед кожним тестом"""
        self.db = SessionLocal()

    def tearDown(self):
        """Закриваємо тестову базу після кожного тесту"""
        self.db.close()

    def test_register_user(self):
        """Тест на успішну реєстрацію нового користувача"""
        response = client.post("/register/", data={"email": "testuser@example.com", "password": "testpassword"})
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.json()["message"])

    def test_register_existing_user(self):
        """Тест на спробу реєстрації користувача з уже зареєстрованим email"""
        # Спочатку створюємо користувача в базі даних
        db_user = User(email="testuser@example.com", hashed_password="hashedpassword", verification_code="code")
        self.db.add(db_user)
        self.db.commit()

        # Тепер намагаємося зареєструвати користувача з таким же email
        response = client.post("/register/", data={"email": "testuser@example.com", "password": "testpassword"})
        self.assertEqual(response.status_code, 409)  # Повинно бути 409, оскільки користувач вже існує
        self.assertEqual(response.json()["detail"], "Email already registered")
