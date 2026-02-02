"""Restaurant repository for database operations"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from loguru import logger


class RestaurantRepository:
    """Repository for restaurant and location data access"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.restaurants_collection = db["restaurants"]
        self.locations_collection = db["locations"]
        self.origins_collection = db["origins"]  # Use actual 'origins' collection, not 'restaurant_origins'

    async def find_by_origin(self, origin_id: str) -> Optional[dict]:
        """Find restaurant and location by origin ID (QR code scan)

        Args:
            origin_id: The origin identifier from QR code

        Returns:
            Origin document with restaurant and location IDs, or None
        """
        try:
            # Query by _id since that's how origins are stored in the actual collection
            origin = await self.origins_collection.find_one({"_id": origin_id})

            if origin:
                origin["_id"] = str(origin["_id"])
                logger.debug(f"Found origin: {origin_id}")
            else:
                logger.warning(f"Origin not found: {origin_id}")

            return origin
        except Exception as e:
            logger.error(f"Error finding origin {origin_id}: {e}")
            return None

    async def find_all(self) -> list[dict]:
        """Find all restaurants

        Returns:
            List of all restaurant documents
        """
        try:
            restaurants = []
            cursor = self.restaurants_collection.find({})
            async for restaurant in cursor:
                restaurant["_id"] = str(restaurant["_id"])
                restaurants.append(restaurant)

            logger.debug(f"Found {len(restaurants)} restaurants")
            return restaurants
        except Exception as e:
            logger.error(f"Error finding all restaurants: {e}")
            return []

    async def find_restaurant_by_id(self, restaurant_id: str) -> Optional[dict]:
        """Find restaurant by restaurant ID

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            Restaurant document, or None
        """
        try:
            # Query by _id as that's the primary identifier
            restaurant = await self.restaurants_collection.find_one(
                {"_id": restaurant_id}
            )

            if restaurant:
                restaurant["_id"] = str(restaurant["_id"])
                logger.debug(f"Found restaurant: {restaurant_id}")
            else:
                logger.warning(f"Restaurant not found: {restaurant_id}")

            return restaurant
        except Exception as e:
            logger.error(f"Error finding restaurant {restaurant_id}: {e}")
            return None

    async def find_location_by_id(
        self, restaurant_id: str, location_id: str
    ) -> Optional[dict]:
        """Find location by restaurant ID and location ID

        Args:
            restaurant_id: The restaurant identifier
            location_id: The location identifier

        Returns:
            Location document, or None
        """
        try:
            # Try with string _id first
            location = await self.locations_collection.find_one({
                "_id": location_id
            })

            # If not found and location_id looks like an ObjectId, try with ObjectId
            if not location and ObjectId.is_valid(location_id):
                try:
                    location = await self.locations_collection.find_one({
                        "_id": ObjectId(location_id)
                    })
                except Exception:
                    pass

            if location:
                location["_id"] = str(location["_id"])
                logger.debug(f"Found location: {location_id}")
            else:
                logger.warning(f"Location not found: {location_id}")

            return location
        except Exception as e:
            logger.error(f"Error finding location {location_id}: {e}")
            return None

    async def find_locations_by_restaurant(self, restaurant_id: str) -> list[dict]:
        """Find all locations for a restaurant

        Args:
            restaurant_id: The restaurant identifier

        Returns:
            List of location documents
        """
        try:
            locations = []
            cursor = self.locations_collection.find({"restaurantId": restaurant_id})
            async for location in cursor:
                location["_id"] = str(location["_id"])
                locations.append(location)

            logger.debug(f"Found {len(locations)} locations for restaurant {restaurant_id}")
            return locations
        except Exception as e:
            logger.error(f"Error finding locations for restaurant {restaurant_id}: {e}")
            return []
