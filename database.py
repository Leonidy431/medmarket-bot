"""
DietaryApp Database Module
==========================
PEP8 Compliant SQLAlchemy ORM for PostgreSQL

Модуль работы с базой данных PostgreSQL на Railway.
Использует SQLAlchemy ORM для типизации и безопасности.

Author: DietaryApp Team
License: MIT
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger

from config import settings

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ SQLAlchemy
# ============================================================================

# Создаём базовый класс для всех моделей
Base = declarative_base()

# Создаём engine (подключение к БД)
# echo=True в development для логирования SQL запросов
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    pool_size=10,
    max_overflow=20,  # Дополнительные соединения при нагрузке
)

# Создаём factory для сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================================================
# МОДЕЛИ ДАННЫХ (PEP8 COMPLIANT)
# ============================================================================

class User(Base):
    """
    Модель пользователя Telegram.

    Attributes:
        id: Уникальный идентификатор (Telegram user_id)
        username: Username пользователя в Telegram
        first_name: Имя пользователя
        last_name: Фамилия пользователя
        language_code: Язык интерфейса (ru, en, etc)
        is_active: Активен ли пользователь
        has_diabetes: Есть ли диагноз сахарный диабет
        has_gout: Есть ли диагноз подагра
        has_celiac: Есть ли целиакия
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="ru")

    # Медицинская информация
    is_active = Column(Boolean, default=True)
    has_diabetes = Column(Boolean, default=False)
    has_gout = Column(Boolean, default=False)
    has_celiac = Column(Boolean, default=False)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserDiary(Base):
    """
    Модель дневника питания пользователя.

    Attributes:
        id: Уникальный идентификатор записи
        user_id: ID пользователя (FK)
        recipe_id: ID рецепта
        recipe_name: Название рецепта
        calories: Калорийность (ккал)
        proteins: Белки (г)
        fats: Жиры (г)
        carbs: Углеводы (г)
        glycemic_index: Гликемический индекс
        purines: Содержание пуринов (для подагры)
        date_eaten: Дата/время приёма пищи
        meal_type: Тип приёма пищи (breakfast, lunch, dinner, snack)
    """

    __tablename__ = "user_diary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    recipe_id = Column(String(100), nullable=True)
    recipe_name = Column(String(255))

    # Пищевая ценность
    calories = Column(Float, default=0.0)
    proteins = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)

    # Специфичные для диагнозов параметры
    glycemic_index = Column(Integer, default=0)
    purines = Column(Float, default=0.0)

    # Типы приёмов пищи
    meal_type = Column(
        String(20),
        default="snack"
    )  # breakfast, lunch, dinner, snack

    date_eaten = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecipeCache(Base):
    """
    Кэш рецептов для оптимизации производительности.

    Attributes:
        id: Уникальный идентификатор
        recipe_id: ID рецепта
        recipe_name: Название рецепта
        description: Описание рецепта
        ingredients: JSON с ингредиентами
        instructions: JSON с инструкциями
        calories: Калорийность
        proteins: Белки
        fats: Жиры
        carbs: Углеводы
        glycemic_index: Гликемический индекс
        purines: Пурины (для подагры)
        suitable_for_diabetes: Подходит для диабета
        suitable_for_gout: Подходит для подагры
        suitable_for_celiac: Подходит для целиакии
        created_at: Дата добавления в кэш
    """

    __tablename__ = "recipe_cache"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(String(100), unique=True, index=True)
    recipe_name = Column(String(255))
    description = Column(Text, nullable=True)

    # JSON поля для гибкости
    ingredients = Column(Text)  # JSON string
    instructions = Column(Text)  # JSON string

    # Пищевая ценность
    calories = Column(Float, default=0.0)
    proteins = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)

    # Специфичные параметры
    glycemic_index = Column(Integer, default=0)
    purines = Column(Float, default=0.0)

    # Пригодность для диагнозов
    suitable_for_diabetes = Column(Boolean, default=False)
    suitable_for_gout = Column(Boolean, default=False)
    suitable_for_celiac = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class Shop(Base):
    """
    Модель для кэширования магазинов.

    Attributes:
        id: Уникальный идентификатор
        google_place_id: ID места в Google Maps
        name: Название магазина
        latitude: Широта
        longitude: Долгота
        address: Адрес
        rating: Рейтинг
        is_available: Доступен ли для скрейпинга цен
    """

    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    google_place_id = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(500))
    rating = Column(Float, default=0.0)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# ФУНКЦИИ ИНИЦИАЛИЗАЦИИ
# ============================================================================

def init_db() -> None:
    """
    Инициализирует базу данных: создаёт все таблицы.

    Вызывается при запуске приложения. Безопасна для повторного вызова
    (не создаст таблицы, если они уже существуют).

    Raises:
        Exception: Если ошибка подключения к БД.
    """
    try:
        logger.info("🗄️  Создание таблиц в PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы созданы успешно")
    except Exception as exc:
        logger.error(f"❌ Ошибка инициализации БД: {exc}", exc_info=True)
        raise


def get_db_session():
    """
    Получает новую сессию БД.

    Используется как dependency injection для функций.

    Yields:
        Session: Объект сессии SQLAlchemy.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
