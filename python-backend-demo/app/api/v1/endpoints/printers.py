"""Printers API endpoints"""

from fastapi import APIRouter, Path
from loguru import logger

from app.core.database import db

router = APIRouter()


@router.get(
    "/{restaurant_id}/{location_id}",
    summary="Get printers for location",
    description="Get all printer configurations for a restaurant location"
)
async def get_printers(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """
    Get all printers for a restaurant location.

    Printers are stored as an embedded array in the location document.
    Returns an empty array if no printers are configured.
    """
    logger.info(f"GET /printers/{restaurant_id}/{location_id}")

    try:
        locations_collection = db.db["locations"]

        # Get location and extract printers array
        location = await locations_collection.find_one(
            {
                "restaurantId": restaurant_id,
                "_id": location_id
            },
            {"printers": 1}
        )

        printers = location.get("printers", []) if location else []

        # Convert ObjectId fields to strings in printers if needed
        for printer in printers:
            if "id" in printer:
                printer["id"] = str(printer["id"])

        logger.debug(f"Found {len(printers)} printers for {restaurant_id}/{location_id}")

        return {
            "data": printers
        }

    except Exception as e:
        logger.error(f"Error fetching printers: {e}")
        return {
            "data": []
        }
