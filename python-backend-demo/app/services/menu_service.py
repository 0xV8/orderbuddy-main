"""Menu service for business logic"""

from typing import Optional, List
from loguru import logger

from app.repositories.menu_repository import MenuRepository
from app.core.exceptions import NotFoundException
from app.core.transformers import transform_menu, transform_menu_summary


class MenuService:
    """Service for menu business logic"""

    def __init__(self, repository: MenuRepository):
        self.repository = repository

    async def get_menu(
        self, restaurant_id: str, location_id: str, menu_id: str
    ) -> dict:
        """Get menu by ID with data transformation"""
        logger.info(
            f"Fetching menu: restaurant={restaurant_id}, location={location_id}, menu={menu_id}"
        )

        menu = await self.repository.find_by_id(restaurant_id, location_id, menu_id)

        if not menu:
            logger.warning(f"Menu not found: {menu_id}")
            raise NotFoundException("Menu", menu_id)

        # Transform menu data to expected format
        transformed_menu = transform_menu(menu)
        logger.debug("Menu data transformed to expected format")

        return transformed_menu

    async def get_menus_by_location(
        self, restaurant_id: str, location_id: str
    ) -> List[dict]:
        """Get all menus for a location with data transformation"""
        logger.info(
            f"Fetching menus for location: restaurant={restaurant_id}, location={location_id}"
        )

        menus = await self.repository.find_menus_by_location(restaurant_id, location_id)

        # Transform each menu summary to expected format
        transformed_menus = [transform_menu_summary(menu) for menu in menus]
        logger.debug(f"Transformed {len(transformed_menus)} menu summaries")

        return transformed_menus
