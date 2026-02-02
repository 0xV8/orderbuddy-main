"""Origins API endpoints"""

from fastapi import APIRouter, Path
from loguru import logger
from bson.objectid import ObjectId

from app.core.database import db

router = APIRouter()


@router.get(
    "/{restaurant_id}/{location_id}",
    summary="Get origins for location",
    description="Get all origin points (tables, parking spots, etc.) with QR code styling"
)
async def get_origins(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """
    Get all origins for a restaurant location.

    Returns QR code styling information and origin data including:
    - Tables
    - Parking spots
    - Campaign origins
    """
    logger.info(f"GET /origins/{restaurant_id}/{location_id}")

    try:
        locations_collection = db.db["locations"]
        origins_collection = db.db["origins"]

        # Get location for QR code styling
        location = await locations_collection.find_one(
            {
                "restaurantId": restaurant_id,
                "_id": location_id
            },
            {"qrCodeStyle": 1, "qrCodeImage": 1}
        )

        # Get all origins (locationId is stored as string)
        cursor = origins_collection.find(
            {
                "restaurantId": restaurant_id,
                "locationId": location_id  # Use string directly
            },
            {
                "_id": 1,
                "restaurantId": 1,
                "locationId": 1,
                "label": 1,
                "qrCodeId": 1,
                "qrCode": 1,
                "type": 1
            }
        )

        origin_data = []
        async for origin in cursor:
            origin["_id"] = str(origin["_id"])
            origin_data.append(origin)

        response = {
            "qrCodeStyle": location.get("qrCodeStyle") if location else None,
            "qrCodeImage": location.get("qrCodeImage") if location else None,
            "originData": origin_data
        }

        logger.debug(f"Found {len(origin_data)} origins for {restaurant_id}/{location_id}")

        return {
            "data": response
        }

    except Exception as e:
        logger.error(f"Error fetching origins: {e}")
        return {
            "data": {
                "qrCodeStyle": None,
                "qrCodeImage": None,
                "originData": []
            }
        }
