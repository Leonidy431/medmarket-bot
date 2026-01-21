"""
DietaryApp Middleware Module
============================
PEP8 Compliant Message Processing Middleware

Модуль middleware для обработки сообщений перед основными хендлерами.
Используется для логирования, валидации и other preprocessing.

Author: DietaryApp Team
License: MIT
"""

import time
from typing import Callable

import telebot
from loguru import logger


# ============================================================================
# MIDDLEWARE ФУНКЦИИ
# ============================================================================

def setup_middleware(bot: telebot.TeleBot) -> None:
    """
    Настраивает middleware для обработки сообщений.

    Args:
        bot: Экземпляр Telegram бота
    """

    @bot.message_handler(func=lambda message: True, content_types=["text"])
    def log_message(message) -> None:
        """
        Middleware для логирования всех текстовых сообщений.

        Args:
            message: Объект сообщения
        """
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
        text = message.text[:50] + "..." if len(message.text) > 50 else message.text

        logger.info(
            f"📨 Сообщение от {username} ({user_id}): {text}"
        )

    logger.info("✅ Middleware инициализирована")
