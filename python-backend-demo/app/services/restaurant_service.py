"""Restaurant service for business logic"""

from typing import Optional
from loguru import logger

from app.repositories.restaurant_repository import RestaurantRepository
from app.core.exceptions import NotFoundException
from app.core.transformers import to_multilingual


class RestaurantService:
    """Service for restaurant and location business logic"""

    def __init__(self, repository: RestaurantRepository):
        self.repository = repository

    async def get_by_origin(self, origin_id: str) -> dict:
        """Get restaurant and location info by origin ID

        Args:
            origin_id: The origin identifier from QR code

        Returns:
            Origin information with restaurant and location IDs

        Raises:
            NotFoundException: If origin not found
        """
        logger.info(f"Fetching restaurant by origin: {origin_id}")

        origin = await self.repository.find_by_origin(origin_id)

        if not origin:
            logger.warning(f"Origin not found: {origin_id}")
            raise NotFoundException("Origin", origin_id)

        return origin

    async def get_restaurant(self, restaurant_id: str) -> dict:
        """Get restaurant details

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            Restaurant details matching NestJS format

        Raises:
            NotFoundException: If restaurant not found
        """
        logger.info(f"Fetching restaurant: {restaurant_id}")

        restaurant = await self.repository.find_restaurant_by_id(restaurant_id)

        if not restaurant:
            logger.warning(f"Restaurant not found: {restaurant_id}")
            raise NotFoundException("Restaurant", restaurant_id)

        # Match NestJS projection: { _id: 1, name: 1, concept: 1, logo: 1 }
        # Handle both 'logo' and 'logoUrl' fields for compatibility
        logo_value = restaurant.get("logo") or restaurant.get("logoUrl")

        transformed_restaurant = {
            "_id": restaurant.get("_id", ""),
            "name": restaurant.get("name", ""),
            "concept": restaurant.get("concept", ""),
            "logo": logo_value,
        }

        logger.debug("Restaurant data transformed to match NestJS format")
        return transformed_restaurant

    async def get_location(self, restaurant_id: str, location_id: str) -> dict:
        """Get location details

        Args:
            restaurant_id: The restaurant identifier
            location_id: The location identifier

        Returns:
            Location details matching NestJS format

        Raises:
            NotFoundException: If location not found
        """
        logger.info(f"Fetching location: restaurant={restaurant_id}, location={location_id}")

        location = await self.repository.find_location_by_id(restaurant_id, location_id)

        if not location:
            logger.warning(f"Location not found: {location_id}")
            raise NotFoundException("Location", location_id)

        # Match NestJS format - use nested payment structure
        payment = location.get("payment", {})
        accept_payment = payment.get("acceptPayment", False)
        wallet_id = payment.get("emergepayWalletsPublicId")

        # Calculate isOpen from workingHours like NestJS does
        # For now, simplified - check if any day is open
        working_hours = location.get("workingHours", [])
        is_open = any(day.get("isOpen", False) for day in working_hours) if working_hours else True

        # Return only the fields NestJS returns
        transformed_location = {
            "_id": str(location.get("_id", "")),
            "locationSlug": location.get("locationSlug", ""),
            "name": location.get("name", ""),
            "isActive": location.get("isActive", True),
            "acceptPayment": accept_payment,
            "emergepayWalletsPublicId": wallet_id,
            "isOpen": is_open,
        }

        logger.debug("Location data transformed to match NestJS format")
        return transformed_location
