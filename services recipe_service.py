"""
DietaryApp Services Module - Recipe Service
============================================
PEP8 Compliant Recipe Search and Filtering

Сервис для поиска и фильтрации рецептов по диагнозам.

Author: DietaryApp Team
License: MIT
"""

import json
from typing import Dict, List, Optional, Any

from loguru import logger

from config import settings

# ============================================================================
# МОКИ ДАННЫХ РЕЦЕПТОВ (в production заменить на реальную БД)
# ============================================================================

MOCK_RECIPES: List[Dict[str, Any]] = [
    {
        "id": "r_001",
        "name": "Курица с брокколи на пару",
        "description": "Лёгкое диетическое блюдо для диабетиков",
        "calories": 320,
        "proteins": 42,
        "fats": 9,
        "carbs": 18,
        "glycemic_index": 35,
        "purines": 45,
        "suitable_for_diabetes": True,
        "suitable_for_gout": False,
        "suitable_for_celiac": True,
        "ingredients": [
            {"name": "Куриное филе", "amount": 300, "unit": "g"},
            {"name": "Брокколи", "amount": 200, "unit": "g"},
            {"name": "Оливковое масло", "amount": 10, "unit": "ml"},
            {"name": "Соль, перец", "amount": 1, "unit": "щепотка"},
        ],
        "instructions": [
            "Нарезать курицу кусочками",
            "Разделить брокколи на соцветия",
            "Готовить на пару 15-20 минут",
            "Приправить солью и перцем",
        ]
    },
    {
        "id": "r_002",
        "name": "Салат «Зелёный микс»",
        "description": "Лёгкий овощной салат для всех диагнозов",
        "calories": 150,
        "proteins": 5,
        "fats": 8,
        "carbs": 12,
        "glycemic_index": 20,
        "purines": 5,
        "suitable_for_diabetes": True,
        "suitable_for_gout": True,
        "suitable_for_celiac": True,
        "ingredients": [
            {"name": "Листья салата", "amount": 100, "unit": "g"},
            {"name": "Помидоры", "amount": 100, "unit": "g"},
            {"name": "Огурец", "amount": 1, "unit": "шт"},
            {"name": "Оливковое масло", "amount": 15, "unit": "ml"},
            {"name": "Лимонный сок", "amount": 15, "unit": "ml"},
        ],
        "instructions": [
            "Промыть салат и овощи",
            "Нарезать овощи",
            "Смешать в миске",
            "Приправить маслом и лимоном",
        ]
    },
    {
        "id": "r_003",
        "name": "Рыба на гриле",
        "description": "Белая рыба с минимумом пуринов",
        "calories": 280,
        "proteins": 38,
        "fats": 12,
        "carbs": 2,
        "glycemic_index": 10,
        "purines": 120,  # Умеренное количество пуринов
        "suitable_for_diabetes": True,
        "suitable_for_gout": False,
        "suitable_for_celiac": True,
        "ingredients": [
            {"name": "Морская рыба", "amount": 300, "unit": "g"},
            {"name": "Лимон", "amount": 1, "unit": "шт"},
            {"name": "Зелень", "amount": 20, "unit": "g"},
        ],
        "instructions": [
            "Подготовить рыбу",
            "Выложить на гриль",
            "Готовить 12-15 минут",
            "Украсить лимоном и зеленью",
        ]
    },
]


# ============================================================================
# СЕРВИС РЕЦЕПТОВ
# ============================================================================

class RecipeService:
    """
    Сервис для работы с рецептами.

    Методы:
        search_recipes: Поиск рецептов по критериям
        get_recipe_details: Получить полную информацию о рецепте
        filter_by_diagnosis: Фильтрация по диагнозам
    """

    @staticmethod
    def search_recipes(
        query: str,
        has_diabetes: bool = False,
        has_gout: bool = False,
        has_celiac: bool = False,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Поиск рецептов по названию/ингредиентам с фильтрацией.

        Args:
            query: Поисковый запрос (название или ингредиент)
            has_diabetes: Имеет ли пользователь диабет
            has_gout: Имеет ли пользователь подагру
            has_celiac: Имеет ли пользователь целиакию
            limit: Максимум результатов

        Returns:
            List[Dict]: Список найденных рецептов
        """
        # Нормализуем запрос
        query_lower = query.lower().strip()

        # Фильтруем рецепты по названию
        matching_recipes = [
            recipe for recipe in MOCK_RECIPES
            if query_lower in recipe["name"].lower()
            or any(
                query_lower in ing["name"].lower()
                for ing in recipe.get("ingredients", [])
            )
        ]

        # Применяем фильтрацию по диагнозам
        filtered_recipes = RecipeService._filter_by_diagnosis(
            matching_recipes,
            has_diabetes,
            has_gout,
            has_celiac
        )

        logger.info(
            f"🔍 Найдено рецептов: {len(filtered_recipes)} "
            f"(диабет:{has_diabetes}, подагра:{has_gout}, целиакия:{has_celiac})"
        )

        return filtered_recipes[:limit]

    @staticmethod
    def _filter_by_diagnosis(
        recipes: List[Dict[str, Any]],
        has_diabetes: bool,
        has_gout: bool,
        has_celiac: bool
    ) -> List[Dict[str, Any]]:
        """
        Фильтрует рецепты по диагнозам пользователя.

        Args:
            recipes: Список рецептов
            has_diabetes: Диабет
            has_gout: Подагра
            has_celiac: Целиакия

        Returns:
            List[Dict]: Отфильтрованные рецепты
        """
        filtered = []

        for recipe in recipes:
            # Если диабет - проверяем гликемический индекс
            if has_diabetes and recipe["glycemic_index"] > 60:
                continue

            # Если подагра - проверяем пурины
            if has_gout and recipe["purines"] > 100:
                continue

            # Если целиакия - только без глютена
            if has_celiac and not recipe.get("suitable_for_celiac", False):
                continue

            filtered.append(recipe)

        return filtered

    @staticmethod
    def get_recipe_details(recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить полную информацию о рецепте по ID.

        Args:
            recipe_id: ID рецепта

        Returns:
            Dict: Информация о рецепте или None
        """
        for recipe in MOCK_RECIPES:
            if recipe["id"] == recipe_id:
                return recipe
        return None
