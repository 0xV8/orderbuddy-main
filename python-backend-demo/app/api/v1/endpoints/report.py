"""Report API endpoints"""

from fastapi import APIRouter, Path
from loguru import logger
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from app.core.database import db

router = APIRouter()

# Tax rate constant (should match NestJS TAX_RATE config)
TAX_RATE = 0.08


def get_day_boundaries_utc(date_str: str, timezone_name: str):
    """
    Convert a date string and timezone to UTC start and end times.

    Args:
        date_str: ISO format date string (YYYY-MM-DD)
        timezone_name: IANA timezone name (e.g., 'America/New_York')

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC
    """
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        logger.warning(f"Invalid timezone {timezone_name}, using UTC")
        tz = ZoneInfo("UTC")

    # Parse and localize date
    local_date = datetime.fromisoformat(date_str).replace(tzinfo=tz)

    # Start of day
    start_local = local_date.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    # End of day
    end_local = local_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    return start_utc, end_utc


@router.get(
    "/order_history/{restaurant_id}/{location_id}/{date}",
    summary="Get order history for a specific date",
    description="Get all orders for a specific date using location timezone"
)
async def get_order_history(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    date: str = Path(..., description="Date in ISO format (YYYY-MM-DD)")
):
    """
    Get order history for a specific date.

    Returns all orders that occurred on the specified date in the location's timezone.
    """
    logger.info(f"GET /report/order_history/{restaurant_id}/{location_id}/{date}")

    try:
        locations_collection = db.db["locations"]
        orders_collection = db.db["orders"]

        # Get location timezone
        location = await locations_collection.find_one(
            {
                "_id": location_id,
                "restaurantId": restaurant_id
            },
            {"timezone": 1}
        )

        if not location:
            logger.warning(f"Location not found: {location_id}")
            return []

        timezone = location.get("timezone", "UTC")

        # Get UTC boundaries for the date
        start_utc, end_utc = get_day_boundaries_utc(date, timezone)

        # Query orders using startedAt field (like NestJS)
        cursor = orders_collection.find({
            "restaurantId": restaurant_id,
            "locationId": location_id,  # Use string directly
            "startedAt": {
                "$gte": start_utc,
                "$lt": end_utc
            }
        })

        orders = []
        async for order in cursor:
            order["_id"] = str(order["_id"])
            orders.append(order)

        logger.debug(f"Found {len(orders)} orders for {date} in {timezone}")

        # Return raw array like NestJS (no wrapper)
        return orders

    except Exception as e:
        logger.error(f"Error fetching order history: {e}")
        return []


@router.get(
    "/sales_summary/{restaurant_id}/{location_id}",
    summary="Get sales summary for last 7 days",
    description="Get daily sales summary for the last 7 days"
)
async def get_sales_summary(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    days: Optional[int] = 7
):
    """
    Get sales summary for the last N days (default 7).

    Returns daily aggregated sales with tax calculation.
    Fills missing dates with zero values.
    """
    logger.info(f"GET /report/sales_summary/{restaurant_id}/{location_id}")

    try:
        locations_collection = db.db["locations"]
        orders_collection = db.db["orders"]

        # Get location timezone
        location = await locations_collection.find_one(
            {"_id": location_id, "restaurantId": restaurant_id},
            {"timezone": 1}
        )

        timezone = location.get("timezone", "UTC") if location else "UTC"
        tz = ZoneInfo(timezone)

        # Calculate days ago in UTC
        now = datetime.now(tz=tz)
        days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
        days_ago_utc = days_ago.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

        # Aggregation pipeline (using endedAt for completed orders like NestJS)
        pipeline = [
            {
                "$match": {
                    "restaurantId": restaurant_id,
                    "locationId": location_id,  # Use string directly
                    "status": "order_delivered",  # OrderCompleted in NestJS
                    "endedAt": {"$gte": days_ago_utc}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$endedAt",
                            "timezone": timezone
                        }
                    },
                    "grossSalesCents": {"$sum": "$totalCents"}
                }
            },
            {
                "$addFields": {
                    "taxCents": {
                        "$multiply": [
                            {"$divide": ["$grossSalesCents", {"$add": [1, TAX_RATE]}]},
                            TAX_RATE
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "grossSales": {"$divide": ["$grossSalesCents", 100]},
                    "tax": {"$divide": ["$taxCents", 100]}
                }
            },
            {"$sort": {"date": 1}}
        ]

        sales_data = []
        async for doc in orders_collection.aggregate(pipeline):
            sales_data.append(doc)

        # Fill missing dates with zero values
        all_dates = {}
        current_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for i in range(days):
            date_key = (current_date - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            all_dates[date_key] = {
                "date": date_key,
                "grossSales": 0,
                "tax": 0
            }

        # Merge with actual data
        for day in sales_data:
            if day["date"] in all_dates:
                all_dates[day["date"]] = day

        # Return sorted by date with success wrapper
        result = sorted(all_dates.values(), key=lambda x: x["date"])

        logger.debug(f"Returning {len(result)} days of sales data")

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"Error fetching sales summary: {e}")
        return {
            "success": False,
            "data": []
        }


@router.get(
    "/sales_by_item/{restaurant_id}/{location_id}/{date}",
    summary="Get sales by menu item for a specific date",
    description="Get sales breakdown by menu item"
)
async def get_sales_by_item(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    date: str = Path(..., description="Date in ISO format (YYYY-MM-DD)")
):
    """
    Get sales by menu item for a specific date.

    Returns aggregated sales data showing which items were sold and revenue per item.
    """
    logger.info(f"GET /report/sales_by_item/{restaurant_id}/{location_id}/{date}")

    try:
        locations_collection = db.db["locations"]
        orders_collection = db.db["orders"]

        # Get location timezone
        location = await locations_collection.find_one(
            {"_id": location_id, "restaurantId": restaurant_id},
            {"timezone": 1}
        )

        timezone = location.get("timezone", "UTC") if location else "UTC"

        # Get UTC boundaries for the date
        start_utc, end_utc = get_day_boundaries_utc(date, timezone)

        # Aggregation pipeline with $unwind on items
        pipeline = [
            {
                "$match": {
                    "restaurantId": restaurant_id,
                    "locationId": location_id,  # Use string directly
                    "status": "order_delivered",  # OrderCompleted
                    "endedAt": {
                        "$gte": start_utc,
                        "$lte": end_utc
                    }
                }
            },
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.menuItemId",
                    "itemName": {"$first": "$items.name"},
                    "soldCount": {"$sum": 1},
                    "grossSalesCents": {"$sum": "$items.price"}
                }
            },
            {
                "$addFields": {
                    "grossSales": {"$divide": ["$grossSalesCents", 100]}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "menuItemId": "$_id",
                    "itemName": 1,
                    "soldCount": 1,
                    "grossSales": 1
                }
            },
            {"$sort": {"grossSales": -1}}
        ]

        sales_by_item = []
        async for doc in orders_collection.aggregate(pipeline):
            sales_by_item.append(doc)

        logger.debug(f"Found sales data for {len(sales_by_item)} items on {date}")

        return {
            "success": True,
            "data": sales_by_item
        }

    except Exception as e:
        logger.error(f"Error fetching sales by item: {e}")
        return {
            "success": False,
            "data": []
        }


@router.get(
    "/sales_by_origin/{restaurant_id}/{location_id}/{date}",
    summary="Get sales by origin for a specific date",
    description="Get sales breakdown by order origin (table, parking, etc.)"
)
async def get_sales_by_origin(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    date: str = Path(..., description="Date in ISO format (YYYY-MM-DD)")
):
    """
    Get sales by origin for a specific date.

    Returns aggregated sales data showing revenue per origin (tables, parking spots, etc.).
    SoldCount represents total items sold, not number of orders.
    """
    logger.info(f"GET /report/sales_by_origin/{restaurant_id}/{location_id}/{date}")

    try:
        locations_collection = db.db["locations"]
        orders_collection = db.db["orders"]

        # Get location timezone
        location = await locations_collection.find_one(
            {"_id": location_id, "restaurantId": restaurant_id},
            {"timezone": 1}
        )

        timezone = location.get("timezone", "UTC") if location else "UTC"

        # Get UTC boundaries for the date
        start_utc, end_utc = get_day_boundaries_utc(date, timezone)

        # Aggregation pipeline grouping by origin.id
        pipeline = [
            {
                "$match": {
                    "restaurantId": restaurant_id,
                    "locationId": location_id,  # Use string directly
                    "status": "order_delivered",  # OrderCompleted
                    "endedAt": {
                        "$gte": start_utc,
                        "$lte": end_utc
                    }
                }
            },
            {
                "$group": {
                    "_id": "$origin.id",
                    "name": {"$first": "$origin.name"},
                    "soldCount": {"$sum": {"$size": "$items"}},  # Total items, not orders
                    "grossSales": {"$sum": {"$divide": ["$totalCents", 100]}}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "originId": {"$toString": "$_id"},
                    "name": 1,
                    "soldCount": 1,
                    "grossSales": 1
                }
            },
            {"$sort": {"grossSales": -1}}
        ]

        sales_by_origin = []
        async for doc in orders_collection.aggregate(pipeline):
            sales_by_origin.append(doc)

        logger.debug(f"Found sales data for {len(sales_by_origin)} origins on {date}")

        return {
            "success": True,
            "data": sales_by_origin
        }

    except Exception as e:
        logger.error(f"Error fetching sales by origin: {e}")
        return {
            "success": False,
            "data": []
        }
