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

class TestUserRegistration(unittest.TestCase):

    def setUp(self):
        """Ініціалізуємо тестову базу даних та клієнта FastAPI перед кожним тестом"""
        self.db = SessionLocal()
        self.client = TestClient(app)
        # Очищаємо базу даних перед кожним тестом
        self.db.query(User).delete()
        self.db.commit()

    def tearDown(self):
        """Закриваємо тестову базу після кожного тесту"""
        self.db.close()

    def test_register_user(self):
        """Тестуємо реєстрацію нового користувача"""
        response = self.client.post("/register/", json={"email": "newuser@example.com", "password": "testpassword"})
        print(response.json())  # Додаємо виведення відповіді на помилку
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.json())

    def test_register_existing_user(self):
        """Тестуємо реєстрацію користувача, який вже існує"""
        # Створюємо користувача в базі даних
        db_user = User(email="testuser@example.com", hashed_password="hashedpassword", verification_code="code")
        self.db.add(db_user)
        self.db.commit()

        response = self.client.post("/register/", json={"email": "testuser@example.com", "password": "testpassword"})
        print(response.json())  # Виводимо помилку, щоб зрозуміти, чому 422
        self.assertEqual(response.status_code, 409)  # Повинно бути 409
        self.assertEqual(response.json()["detail"], "Email already registered")

        # Тепер намагаємося зареєструвати користувача з таким же email
        response = self.client.post("/register/", json={"email": "testuser@example.com", "password": "testpassword"})
        self.assertEqual(response.status_code, 409)  # Повинно бути 409, оскільки користувач вже існує
        self.assertEqual(response.json()["detail"], "Email already registered")

    def test_register_user_missing_fields(self):
        """Тестуємо реєстрацію користувача без обов'язкових полів"""
        response = self.client.post("/register/", json={"email": "incompleteuser@example.com"})
        print(response.json())  # Додаємо виведення помилки для зрозумілості
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())
        self.assertEqual(response.json()["detail"][0]["msg"].lower(), "field required")
