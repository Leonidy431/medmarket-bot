"""
DietaryApp Configuration Module
================================
PEP8 Compliant Configuration Management for Production

Модуль управления конфигурацией приложения с использованием Pydantic.
Автоматически загружает переменные из .env файла и Railway Deployment.

Author: DietaryApp Team
License: MIT
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


# ============================================================================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ============================================================================

class Settings(BaseSettings):
    """
    Основные настройки приложения, загружаемые из переменных окружения.

    Attributes:
        APP_VERSION: Версия приложения
        ENVIRONMENT: Тип окружения (development, production, testing)
        DEBUG: Режим отладки
        TELEGRAM_BOT_TOKEN: Токен Telegram бота
        POLLING_TIMEOUT: Timeout между запросами к API Telegram
        TELEGRAM_API_SERVER: URL сервера Telegram API (по умолчанию официальный)
        DATABASE_URL: URL подключения к PostgreSQL (Railway автоматически)
        OPENAI_API_KEY: API ключ OpenAI для GPT-4
        GOOGLE_MAPS_API_KEY: API ключ Google Maps
        REDIS_URL: URL Redis для кэширования (опционально)
        LOG_LEVEL: Уровень логирования
        MAX_RECIPE_RESULTS: Максимум результатов при поиске рецептов
        MAX_SHOPS_RESULTS: Максимум магазинов в результатах
    """

    # ========================================================================
    # ОСНОВНЫЕ НАСТРОЙКИ
    # ========================================================================

    app_version: str = "1.0.0"
    environment: Literal["development", "production", "testing"] = "development"
    debug: bool = False

    # ========================================================================
    # TELEGRAM НАСТРОЙКИ
    # ========================================================================

    telegram_bot_token: str
    polling_timeout: int = 60
    telegram_api_server: str = "https://api.telegram.org"

    # ========================================================================
    # DATABASE НАСТРОЙКИ (Railway PostgreSQL)
    # ========================================================================

    # Railway автоматически создаёт DATABASE_URL вида:
    # postgresql://user:password@host:port/database
    database_url: str

    # ========================================================================
    # ВНЕШНИЕ API КЛЮЧИ
    # ========================================================================

    openai_api_key: str
    google_maps_api_key: str

    # ========================================================================
    # REDIS НАСТРОЙКИ (опционально, для кэширования)
    # ========================================================================

    redis_url: str = "redis://localhost:6379/0"

    # ========================================================================
    # ЛОГИРОВАНИЕ И ОТЛАДКА
    # ========================================================================

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    max_recipe_results: int = 10
    max_shops_results: int = 5

    # ========================================================================
    # ПАРАМЕТРЫ МОДЕЛИ
    # ========================================================================

    class Config:
        """Pydantic конфигурация."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# ============================================================================
# КЭШИРОВАНИЕ НАСТРОЕК
# ============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Получает и кэширует настройки приложения.

    Функция использует LRU кэширование для того, чтобы не перезагружать
    конфигурацию из файла каждый раз. Это повышает производительность.

    Returns:
        Settings: Объект настроек с загруженными параметрами.

    Raises:
        ValueError: Если необходимые переменные окружения не установлены.
    """
    return Settings()


# ============================================================================
# ГЛОБАЛЬНЫЙ ОБЪЕКТ НАСТРОЕК
# ============================================================================

settings = get_settings()

# ============================================================================
# ВАЛИДАЦИЯ НАСТРОЕК ПРИ ЗАПУСКЕ
# ============================================================================

def validate_settings() -> None:
    """
    Валидирует критические настройки приложения при запуске.

    Проверяет наличие всех необходимых API ключей и конфигурации.

    Raises:
        ValueError: Если отсутствуют критические переменные окружения.
    """
    critical_vars = [
        ("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token),
        ("DATABASE_URL", settings.database_url),
        ("OPENAI_API_KEY", settings.openai_api_key),
        ("GOOGLE_MAPS_API_KEY", settings.google_maps_api_key),
    ]

    missing_vars = [
        name for name, value in critical_vars
        if not value
    ]

    if missing_vars:
        raise ValueError(
            f"❌ Отсутствуют критические переменные окружения: "
            f"{', '.join(missing_vars)}\n"
            f"Установите их в .env файле или переменных окружения Railway."
        )


# Запускаем валидацию при импорте модуля
validate_settings()
