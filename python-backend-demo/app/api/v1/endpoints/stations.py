"""Stations API endpoints"""

from fastapi import APIRouter, Path, HTTPException
from loguru import logger
from bson.objectid import ObjectId

from app.core.database import db

router = APIRouter()


@router.get(
    "/{restaurant_id}/{location_id}",
    summary="Get stations for location",
    description="Get all kitchen stations for a restaurant location"
)
async def get_stations(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """
    Get all kitchen stations for a restaurant location.

    Returns station information including names and associated tags.
    """
    logger.info(f"GET /stations/{restaurant_id}/{location_id}")

    try:
        stations_collection = db.db["stations"]

        query = {
            "restaurantId": restaurant_id,
            "locationId": location_id  # Use string directly
        }

        projection = {
            "_id": 1,
            "restaurantId": 1,
            "locationId": 1,
            "name": 1,
            "tags": 1
        }

        cursor = stations_collection.find(query, projection)
        stations = []

        async for station in cursor:
            station["_id"] = str(station["_id"])
            stations.append(station)

        if not stations:
            raise HTTPException(
                status_code=404,
                detail=f"No stations found for restaurant {restaurant_id} at location {location_id}"
            )

        logger.debug(f"Found {len(stations)} stations for {restaurant_id}/{location_id}")

        return {
            "data": stations
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
