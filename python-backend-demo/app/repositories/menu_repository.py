"""Menu repository for database operations"""

from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger

from app.core.constants import Collections
from app.models.domain.menu import Menu


class MenuRepository:
    """Repository for menu data access"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[Collections.MENUS]

    async def find_by_id(
        self, restaurant_id: str, location_id: str, menu_id: str
    ) -> Optional[dict]:
        """Find menu by restaurant ID, location ID, and menu ID"""
        try:
            # Try as ObjectId first, then as string
            try:
                query_id = ObjectId(menu_id)
            except:
                query_id = menu_id

            menu = await self.collection.find_one(
                {
                    "_id": query_id,
                    "restaurantId": restaurant_id,
                    "locationId": location_id,
                }
            )

            if menu:
                menu["_id"] = str(menu["_id"])
                logger.debug(f"Found menu: {menu_id}")

            return menu
        except Exception as e:
            logger.error(f"Error finding menu {menu_id}: {e}")
            return None

    async def find_menus_by_location(
        self, restaurant_id: str, location_id: str
    ) -> List[dict]:
        """Find all menus for a location"""
        try:
            cursor = self.collection.find(
                {"restaurantId": restaurant_id, "locationId": location_id}
            )

            menus = []
            async for menu in cursor:
                menu["_id"] = str(menu["_id"])
                menus.append(menu)

            logger.debug(f"Found {len(menus)} menus for location {location_id}")
            return menus
        except Exception as e:
            logger.error(f"Error finding menus for location {location_id}: {e}")
            return []
