"""Order App API endpoints (for customer-facing order application)"""

from fastapi import APIRouter, Depends, Path
from loguru import logger
from app.repositories.restaurant_repository import RestaurantRepository
from app.dependencies import get_restaurant_repository
from app.core.database import db

router = APIRouter()


@router.get(
    "/restaurants/{restaurant_id}",
    summary="Get restaurant details (Order App)",
    description="Get restaurant information for the customer order app"
)
async def get_restaurant_for_order_app(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository)
):
    """Get restaurant details for order app"""
    logger.info(f"GET /order-app/restaurants/{restaurant_id}")

    try:
        # Get restaurant from database
        restaurant = await db.db.restaurants.find_one({"_id": restaurant_id})

        if not restaurant:
            return {
                "success": False,
                "message": "Restaurant not found",
                "data": None
            }

        # Transform for order app
        result = {
            "_id": restaurant["_id"],
            "name": restaurant.get("name", ""),
            "concept": restaurant.get("concept", ""),
            "logo": restaurant.get("logo", "")
        }

        return {
            "data": result,
            "success": True,
            "message": None
        }
    except Exception as e:
        logger.error(f"Error fetching restaurant: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}",
    summary="Get location details (Order App)",
    description="Get location information for the customer order app"
)
async def get_location_for_order_app(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """Get location details for order app"""
    logger.info(f"GET /order-app/restaurants/{restaurant_id}/locations/{location_id}")

    try:
        location = await db.db.locations.find_one({
            "_id": location_id,
            "restaurantId": restaurant_id
        })

        if not location:
            return {
                "success": False,
                "message": "Location not found",
                "data": None
            }

        # Transform for order app
        result = {
            "_id": location["_id"],
            "locationSlug": location.get("locationSlug", location["_id"]),
            "name": location.get("name", ""),
            "isActive": location.get("isActive", True),
            "acceptPayment": location.get("acceptPayment", False),
            "emergepayWalletsPublicId": location.get("emergepayWalletsPublicId", ""),
            "isOpen": location.get("isOpen", True)
        }

        return {
            "data": result,
            "success": True,
            "message": None
        }
    except Exception as e:
        logger.error(f"Error fetching location: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }


@router.get(
    "/restaurants/origins/{origin_id}",
    summary="Get origin details (Order App)",
    description="Get origin information for the customer order app"
)
async def get_origin_for_order_app(
    origin_id: str = Path(..., description="Origin ID (QR code, table number, etc.)")
):
    """Get origin details for order app"""
    logger.info(f"GET /order-app/restaurants/origins/{origin_id}")

    try:
        origin = await db.db.origins.find_one({"_id": origin_id})

        if not origin:
            return {
                "success": False,
                "message": "Origin not found",
                "data": None
            }

        # Transform for order app
        result = {
            "_id": origin["_id"],
            "label": origin.get("label", origin["_id"]),
            "restaurantId": origin.get("restaurantId", ""),
            "locationId": origin.get("locationId", ""),
            "type": origin.get("type", "")
        }

        return {
            "data": result,
            "success": True,
            "message": None
        }
    except Exception as e:
        logger.error(f"Error fetching origin: {e}")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
