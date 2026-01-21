"""
DietaryApp Services Module - GPT Service
========================================
PEP8 Compliant AI Dietician using OpenAI GPT-4

Сервис для взаимодействия с GPT-4 как с AI-диетологом.

Author: DietaryApp Team
License: MIT
"""

from typing import Optional

import openai
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import settings

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ OpenAI
# ============================================================================

openai.api_key = settings.openai_api_key


# ============================================================================
# GPT СЕРВИС
# ============================================================================

class GPTService:
    """
    Сервис для работы с OpenAI GPT-4 как AI-диетолог.

    Методы:
        ask_dietician: Получить рекомендацию от AI диетолога
    """

    # Системное сообщение для GPT (контекст диетолога)
    SYSTEM_PROMPT = (
        "Вы профессиональный диетолог с 20-летним опытом. "
        "Отвечайте на вопросы о питании кратко, ясно и научно обоснованно. "
        "Всегда рекомендуйте консультацию с врачом для серьёзных проблем. "
        "Ответы должны быть на русском языке."
    )

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError))
    )
    def ask_dietician(
        question: str,
        has_diabetes: bool = False,
        has_gout: bool = False,
        has_celiac: bool = False,
        max_tokens: int = 500
    ) -> str:
        """
        Получить рекомендацию от AI-диетолога.

        Args:
            question: Вопрос пользователя
            has_diabetes: Есть ли диабет
            has_gout: Есть ли подагра
            has_celiac: Есть ли целиакия
            max_tokens: Максимум токенов в ответе

        Returns:
            str: Ответ от GPT-4

        Raises:
            openai.APIError: Ошибка API OpenAI
        """
        try:
            # Формируем контекст диагнозов
            diagnoses = []
            if has_diabetes:
                diagnoses.append("сахарный диабет")
            if has_gout:
                diagnoses.append("подагра")
            if has_celiac:
                diagnoses.append("целиакия")

            diagnosis_context = (
                f"Пользователь имеет: {', '.join(diagnoses)}. "
                if diagnoses
                else "Пользователь без специальных диагнозов. "
            )

            # Формируем полное сообщение
            full_prompt = (
                f"{diagnosis_context}\n"
                f"Вопрос: {question}\n"
                f"Ответьте с учётом здоровья пользователя."
            )

            logger.info(
                f"🤖 Запрос к GPT-4 от пользователя: {question[:50]}..."
            )

            # Запрашиваем GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": GPTService.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9
            )

            # Извлекаем ответ
            answer = response.choices[0].message["content"].strip()

            logger.info(f"✅ Ответ от GPT-4 получен ({len(answer)} символов)")

            return answer

        except openai.APIError as exc:
            logger.error(f"❌ Ошибка API OpenAI: {exc}", exc_info=True)
            return (
                "❌ Извините, диетолог временно недоступен. "
                "Пожалуйста, попробуйте позже."
            )
        except Exception as exc:
            logger.error(f"❌ Неожиданная ошибка в GPT сервисе: {exc}", exc_info=True)
            return "❌ Произошла ошибка. Попробуйте позже."

    @staticmethod
    def generate_meal_plan(
        days: int = 7,
        has_diabetes: bool = False,
        has_gout: bool = False,
        has_celiac: bool = False
    ) -> str:
        """
        Генерирует план питания на N дней.

        Args:
            days: Количество дней
            has_diabetes: Диабет
            has_gout: Подагра
            has_celiac: Целиакия

        Returns:
            str: План питания
        """
        diagnoses = []
        if has_diabetes:
            diagnoses.append("низкий гликемический индекс")
        if has_gout:
            diagnoses.append("низкое содержание пуринов")
        if has_celiac:
            diagnoses.append("без глютена")

        dietary_restrictions = (
            f"План питания должен включать: {', '.join(diagnoses)}."
            if diagnoses
            else "Сбалансированный план питания."
        )

        prompt = (
            f"Создайте план питания на {days} дней. "
            f"{dietary_restrictions} "
            f"Для каждого дня укажите завтрак, обед, ужин и перекус. "
            f"Включите основные питательные показатели."
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": GPTService.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message["content"].strip()

        except Exception as exc:
            logger.error(f"❌ Ошибка генерации плана: {exc}", exc_info=True)
            return "❌ Не удалось создать план питания."
