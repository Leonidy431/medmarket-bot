"""
DietaryApp Services Package
===========================

Пакет сервисов для работы с рецептами, GPT, магазинами и т.д.

Author: DietaryApp Team
License: MIT
"""

from .recipe_service import RecipeService
from .gpt_service import GPTService
from .shop_service import ShopService

__all__ = [
    "RecipeService",
    "GPTService",
    "ShopService",
]
