"""Campaign API endpoints"""

from fastapi import APIRouter, Path
from loguru import logger
from bson.objectid import ObjectId

from app.core.database import db

router = APIRouter()


@router.get(
    "/restaurant/{restaurant_id}/location/{location_id}",
    summary="Get campaigns for location",
    description="Get all promotional campaigns for a restaurant location"
)
async def get_campaigns(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """
    Get all campaigns for a restaurant location.

    Returns campaigns sorted by creation date (newest first).
    """
    logger.info(f"GET /campaign/restaurant/{restaurant_id}/location/{location_id}")

    try:
        campaigns_collection = db.db["campaigns"]

        query = {
            "restaurantId": restaurant_id,
            "locationId": location_id  # Use string directly
        }

        # Sort by createdAt descending
        cursor = campaigns_collection.find(query).sort("createdAt", -1)

        campaigns = []
        async for campaign in cursor:
            campaign["_id"] = str(campaign["_id"])
            campaigns.append(campaign)

        logger.debug(f"Found {len(campaigns)} campaigns for {restaurant_id}/{location_id}")

        return {
            "data": campaigns
        }

    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        return {
            "data": []
        }
