"""
DietaryApp Handlers Module
==========================
PEP8 Compliant Telegram Message Handlers

Модуль обработки команд и сообщений от пользователей.
Содержит логику основного функционала бота.

Author: DietaryApp Team
License: MIT
"""

import json
from typing import Dict, List, Optional

import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal, User, UserDiary, RecipeCache
from services.recipe_service import RecipeService
from services.gpt_service import GPTService
from services.shop_service import ShopService

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ
# ============================================================================

recipe_service = RecipeService()
gpt_service = GPTService()
shop_service = ShopService()

# ============================================================================
# ХРАНИЛИЩЕ СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЯ (для конечного автомата)
# ============================================================================

user_state: Dict[int, Dict[str, str]] = {}


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_or_create_user(message: Message, db: Session) -> User:
    """
    Получает или создаёт пользователя в БД.

    Args:
        message: Объект сообщения от Telegram
        db: Сессия БД

    Returns:
        User: Объект пользователя из БД
    """
    user = db.query(User).filter(
        User.telegram_id == message.from_user.id
    ).first()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code or "ru",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✨ Новый пользователь: {message.from_user.id}")

    return user


def create_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создаёт главное меню с кнопками.

    Returns:
        InlineKeyboardMarkup: Объект клавиатуры
    """
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🔍 Поиск рецепта",
            callback_data="search_recipe"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "📍 Магазины рядом",
            callback_data="find_shops"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "📔 Мой дневник",
            callback_data="view_diary"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "🤖 Спросить диетолога",
            callback_data="ask_dietician"
        )
    )
    markup.add(
        InlineKeyboardButton(
            "⚙️ Настройки",
            callback_data="settings"
        )
    )
    return markup


# ============================================================================
# РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# ============================================================================

def register_handlers(bot: telebot.TeleBot) -> None:
    """
    Регистрирует все обработчики команд и сообщений в боте.

    Args:
        bot: Экземпляр Telegram бота
    """

    # ========================================================================
    # КОМАНДА /start
    # ========================================================================

    @bot.message_handler(commands=["start"])
    def handle_start(message: Message) -> None:
        """
        Обработчик команды /start. Приветствие и главное меню.

        Args:
            message: Объект сообщения от Telegram
        """
        db = SessionLocal()
        try:
            user = get_or_create_user(message, db)

            welcome_text = (
                f"👋 Добро пожаловать, {user.first_name}!\n\n"
                f"🥗 <b>DietaryApp</b> — ваш персональный диетолог на Telegram.\n"
                f"Приложение подбирает рецепты с учётом:\n"
                f"• 🩺 Сахарного диабета\n"
                f"• 🦶 Подагры\n"
                f"• 🌾 Целиакии\n\n"
                f"Выберите действие:"
            )

            bot.send_message(
                message.chat.id,
                welcome_text,
                parse_mode="HTML",
                reply_markup=create_main_keyboard()
            )
            logger.info(f"🎯 Пользователь {user.telegram_id} вызвал /start")

        except Exception as exc:
            logger.error(
                f"❌ Ошибка в /start для {message.from_user.id}: {exc}",
                exc_info=True
            )
            bot.send_message(
                message.chat.id,
                "❌ Ошибка при инициализации. Попробуйте позже."
            )
        finally:
            db.close()

    # ========================================================================
    # КОМАНДА /help
    # ========================================================================

    @bot.message_handler(commands=["help"])
    def handle_help(message: Message) -> None:
        """
        Обработчик команды /help. Справка по боту.

        Args:
            message: Объект сообщения от Telegram
        """
        help_text = (
            "<b>📚 Справка DietaryApp</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/status - Статус подписки\n"
            "/settings - Настройки профиля\n\n"
            "<b>Основные функции:</b>\n"
            "🔍 Поиск рецептов с фильтрацией по диагнозам\n"
            "📍 Поиск ближайших магазинов и цен\n"
            "📔 Дневник питания с аналитикой\n"
            "🤖 AI-диетолог на базе GPT-4\n"
            "💪 Челленджи и геймификация\n\n"
            "<b>Нужна помощь?</b>\n"
            "📧 support@dietaryapp.com\n"
            "💬 Telegram: @dietaryapp_ru"
        )

        bot.send_message(
            message.chat.id,
            help_text,
            parse_mode="HTML",
            reply_markup=create_main_keyboard()
        )

    # ========================================================================
    # ОБРАБОТЧИК CALLBACK КНОПОК
    # ========================================================================

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call) -> None:
        """
        Обработчик всех callback запросов от кнопок.

        Args:
            call: Объект callback запроса
        """
        try:
            # Ответим на callback, чтобы убрать загрузку на клиенте
            bot.answer_callback_query(call.id)

            if call.data == "search_recipe":
                bot.send_message(
                    call.message.chat.id,
                    "🔍 Введите ингредиенты или название блюда:\n"
                    "(например: 'курица с овощами')"
                )
                user_state[call.from_user.id] = {"action": "search_recipe"}

            elif call.data == "find_shops":
                bot.send_message(
                    call.message.chat.id,
                    "📍 Отправьте вашу геолокацию для поиска магазинов"
                )
                user_state[call.from_user.id] = {"action": "find_shops"}

            elif call.data == "view_diary":
                db = SessionLocal()
                try:
                    diary_entries = db.query(UserDiary).filter(
                        UserDiary.user_id == call.from_user.id
                    ).limit(10).all()

                    if diary_entries:
                        diary_text = "📔 <b>Ваш дневник питания (последние 10)</b>\n\n"
                        for entry in diary_entries:
                            diary_text += (
                                f"<b>{entry.recipe_name}</b>\n"
                                f"Калории: {entry.calories}ккал | "
                                f"БЖУ: {entry.proteins}g/{entry.fats}g/{entry.carbs}g\n"
                                f"⏰ {entry.date_eaten.strftime('%d.%m.%Y %H:%M')}\n\n"
                            )
                        bot.send_message(
                            call.message.chat.id,
                            diary_text,
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            call.message.chat.id,
                            "📔 Ваш дневник пуст. Начните добавлять рецепты!"
                        )
                finally:
                    db.close()

            elif call.data == "ask_dietician":
                bot.send_message(
                    call.message.chat.id,
                    "🤖 Спросите у AI-диетолога (любой вопрос о питании):"
                )
                user_state[call.from_user.id] = {"action": "ask_dietician"}

            elif call.data == "settings":
                bot.send_message(
                    call.message.chat.id,
                    "⚙️ Настройки профиля (в разработке)"
                )

        except Exception as exc:
            logger.error(
                f"❌ Ошибка в callback {call.data}: {exc}",
                exc_info=True
            )
            bot.send_message(
                call.message.chat.id,
                "❌ Ошибка обработки. Попробуйте позже."
            )

    # ========================================================================
    # ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
    # ========================================================================

    @bot.message_handler(content_types=["text"])
    def handle_text(message: Message) -> None:
        """
        Обработчик текстовых сообщений с учётом состояния пользователя.

        Args:
            message: Объект сообщения от Telegram
        """
        user_id = message.from_user.id
        db = SessionLocal()

        try:
            # Получаем пользователя
            user = get_or_create_user(message, db)

            # Проверяем состояние пользователя
            if user_id in user_state:
                action = user_state[user_id].get("action")

                if action == "search_recipe":
                    # Поиск рецепта по ингредиентам
                    query = message.text
                    bot.send_message(
                        message.chat.id,
                        f"🔄 Ищем рецепты для '{query}'..."
                    )

                    # Запрашиваем рецепты у сервиса
                    recipes = recipe_service.search_recipes(
                        query=query,
                        has_diabetes=user.has_diabetes,
                        has_gout=user.has_gout,
                        has_celiac=user.has_celiac,
                        limit=settings.max_recipe_results
                    )

                    if recipes:
                        response = "✅ <b>Найденные рецепты:</b>\n\n"
                        for idx, recipe in enumerate(recipes, 1):
                            response += (
                                f"<b>{idx}. {recipe['name']}</b>\n"
                                f"Калории: {recipe['calories']}ккал | "
                                f"ГИ: {recipe.get('glycemic_index', 'N/A')}\n"
                                f"{recipe.get('description', '')[:100]}...\n\n"
                            )
                        bot.send_message(
                            message.chat.id,
                            response,
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            message.chat.id,
                            "❌ Рецепты не найдены. Попробуйте другой запрос."
                        )

                    del user_state[user_id]

                elif action == "ask_dietician":
                    # AI диетолог
                    bot.send_message(
                        message.chat.id,
                        "🤖 Диетолог думает..."
                    )

                    response = gpt_service.ask_dietician(
                        message.text,
                        user.has_diabetes,
                        user.has_gout,
                        user.has_celiac
                    )

                    bot.send_message(
                        message.chat.id,
                        response,
                        parse_mode="HTML"
                    )

                    del user_state[user_id]

            else:
                # Если состояния нет, показываем главное меню
                bot.send_message(
                    message.chat.id,
                    "👋 Используйте главное меню для навигации:",
                    reply_markup=create_main_keyboard()
                )

        except Exception as exc:
            logger.error(
                f"❌ Ошибка обработки текста от {user_id}: {exc}",
                exc_info=True
            )
            bot.send_message(
                message.chat.id,
                "❌ Ошибка обработки. Попробуйте позже."
            )
        finally:
            db.close()

    logger.info("✅ Все обработчики зарегистрированы")
