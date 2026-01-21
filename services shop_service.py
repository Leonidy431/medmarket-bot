"""
DietaryApp Services Module - Shop Service
=========================================
PEP8 Compliant Shop Location and Price Finding

Сервис для поиска магазинов и цен на ингредиенты.

Author: DietaryApp Team
License: MIT
"""

from typing import Dict, List, Optional, Tuple, Any

from loguru import logger

from config import settings

# ============================================================================
# МОКИ ДАННЫХ МАГАЗИНОВ
# ============================================================================

MOCK_SHOPS: List[Dict[str, Any]] = [
    {
        "id": "shop_001",
        "name": "Пятёрочка на Красной площади",
        "latitude": 55.7558,
        "longitude": 37.6173,
        "address": "Москва, Красная площадь, 1",
        "rating": 4.7,
        "working_hours": "08:00-23:00"
    },
    {
        "id": "shop_002",
        "name": "Магнит",
        "latitude": 55.7500,
        "longitude": 37.6200,
        "address": "Москва, Тверская, 15",
        "rating": 4.5,
        "working_hours": "07:00-23:00"
    },
    {
        "id": "shop_003",
        "name": "Дикси",
        "latitude": 55.7600,
        "longitude": 37.6100,
        "address": "Москва, Охотный ряд, 2",
        "rating": 4.3,
        "working_hours": "06:00-23:00"
    },
]

# Моки цен на ингредиенты в разных магазинах
MOCK_PRICES: Dict[str, Dict[str, float]] = {
    "shop_001": {
        "Куриное филе": 289,
        "Брокколи": 49,
        "Салат": 35,
        "Помидоры": 45,
        "Огурец": 15,
        "Оливковое масло": 320,
    },
    "shop_002": {
        "Куриное филе": 269,
        "Брокколи": 59,
        "Салат": 39,
        "Помидоры": 49,
        "Огурец": 18,
        "Оливковое масло": 299,
    },
    "shop_003": {
        "Куриное филе": 299,
        "Брокколи": 44,
        "Салат": 32,
        "Помидоры": 42,
        "Огурец": 12,
        "Оливковое масло": 340,
    },
}


# ============================================================================
# СЕРВИС МАГАЗИНОВ
# ============================================================================

class ShopService:
    """
    Сервис для работы с магазинами и ценами.

    Методы:
        find_nearby_shops: Найти магазины рядом по геолокации
        get_prices_for_recipe: Получить цены на ингредиенты рецепта
        calculate_recipe_cost: Рассчитать стоимость рецепта
    """

    @staticmethod
    def find_nearby_shops(
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Найти магазины рядом по геолокации.

        Args:
            latitude: Широта пользователя
            longitude: Долгота пользователя
            radius_km: Радиус поиска в км
            limit: Максимум результатов

        Returns:
            List[Dict]: Список магазинов с расстояниями
        """
        shops_with_distance = []

        for shop in MOCK_SHOPS:
            # Простое вычисление расстояния (Евклидова метрика)
            # В production используйте Haversine formula для точности
            distance = ShopService._calculate_distance(
                latitude,
                longitude,
                shop["latitude"],
                shop["longitude"]
            )

            if distance <= radius_km:
                shop_data = shop.copy()
                shop_data["distance_km"] = round(distance, 2)
                shops_with_distance.append(shop_data)

        # Сортируем по расстоянию
        shops_with_distance.sort(key=lambda x: x["distance_km"])

        logger.info(
            f"📍 Найдено {len(shops_with_distance)} магазинов "
            f"в радиусе {radius_km}км"
        )

        return shops_with_distance[:limit]

    @staticmethod
    def _calculate_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Вычисляет приблизительное расстояние между двумя точками.

        Args:
            lat1, lon1: Координаты первой точки
            lat2, lon2: Координаты второй точки

        Returns:
            float: Расстояние в км (приблизительно)
        """
        # Приблизительное преобразование градусов в км
        # 1 градус широты ≈ 111 км
        # 1 градус долготы ≈ 111 км * cos(широта)
        lat_diff = (lat2 - lat1) * 111
        lon_diff = (lon2 - lon1) * 111
        distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5
        return distance

    @staticmethod
    def get_prices_for_recipe(
        recipe_id: str,
        ingredients: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Получить цены на ингредиенты рецепта во всех магазинах.

        Args:
            recipe_id: ID рецепта
            ingredients: Список ингредиентов

        Returns:
            Dict: Цены по магазинам
        """
        prices_by_shop = {}

        for shop in MOCK_SHOPS:
            shop_prices = MOCK_PRICES.get(shop["id"], {})
            total_price = 0.0
            found_ingredients = 0

            for ingredient in ingredients:
                ingredient_name = ingredient.get("name", "")
                amount = ingredient.get("amount", 0)

                price_per_unit = shop_prices.get(ingredient_name)

                if price_per_unit:
                    total_price += price_per_unit
                    found_ingredients += 1

            prices_by_shop[shop["id"]] = {
                "shop_name": shop["name"],
                "total_price": total_price,
                "found_ingredients": found_ingredients,
                "total_ingredients": len(ingredients),
                "price_per_serving": round(
                    total_price / len(ingredients),
                    2
                ) if ingredients else 0,
                "address": shop["address"],
                "rating": shop["rating"],
            }

        return prices_by_shop

    @staticmethod
    def find_cheapest_shop(
        prices_by_shop: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Найти магазин с минимальной ценой.

        Args:
            prices_by_shop: Словарь цен по магазинам

        Returns:
            Dict: Информация о самом дешёвом магазине
        """
        if not prices_by_shop:
            return None

        cheapest = min(
            prices_by_shop.items(),
            key=lambda x: x[1]["total_price"]
        )

        shop_id, shop_data = cheapest
        shop_data["shop_id"] = shop_id

        logger.info(
            f"💰 Самый дешёвый магазин: {shop_data['shop_name']} "
            f"({shop_data['total_price']} ₽)"
        )

        return shop_data

    @staticmethod
    def calculate_recipe_cost(
        recipe: Dict[str, Any],
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Рассчитать полную стоимость рецепта с учётом магазинов.

        Args:
            recipe: Информация о рецепте
            latitude: Широта пользователя
            longitude: Долгота пользователя

        Returns:
            Dict: Информация о стоимости в разных магазинах
        """
        # Получаем цены
        prices = ShopService.get_prices_for_recipe(
            recipe["id"],
            recipe.get("ingredients", [])
        )

        # Находим самый дешёвый
        cheapest = ShopService.find_cheapest_shop(prices)

        # Находим ближайшие магазины
        nearby_shops = ShopService.find_nearby_shops(
            latitude,
            longitude,
            limit=3
        )

        return {
            "recipe_name": recipe.get("name", "Unknown"),
            "cheapest_shop": cheapest,
            "nearby_shops": nearby_shops,
            "all_prices": prices,
        }
