"""Order repository for database operations"""

from typing import Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger
import uuid

from app.core.constants import Collections
from app.models.schemas.order import OrderStatus


class OrderRepository:
    """Repository for order data access"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db[Collections.ORDERS]
        self.preview_collection = db[Collections.ORDERS_PREVIEW]

    async def create_order(self, order_data: dict) -> dict:
        """Create a new order"""
        try:
            # Generate unique order ID
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

            order_doc = {
                **order_data,
                "orderId": order_id,
                "status": OrderStatus.ORDER_CREATED,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
            }

            result = await self.collection.insert_one(order_doc)
            order_doc["_id"] = str(result.inserted_id)

            logger.info(f"Created order: {order_id}")
            return order_doc

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    async def find_by_id(self, order_id: str) -> Optional[dict]:
        """Find order by ID"""
        try:
            order = await self.collection.find_one({"orderId": order_id})

            if order:
                order["_id"] = str(order["_id"])
                logger.debug(f"Found order: {order_id}")

            return order

        except Exception as e:
            logger.error(f"Error finding order {order_id}: {e}")
            return None

    async def update_status(
        self,
        order_id: str,
        status: OrderStatus,
        estimated_minutes: Optional[int] = None
    ) -> Optional[dict]:
        """Update order status"""
        try:
            update_data = {
                "status": status,
                "updatedAt": datetime.utcnow(),
            }

            # Set timestamps based on status
            if status == OrderStatus.ACCEPTED and estimated_minutes:
                update_data["estimatedReadyAt"] = datetime.utcnow()
                # Add estimated minutes logic here if needed
            elif status == OrderStatus.READY:
                update_data["readyAt"] = datetime.utcnow()
            elif status == OrderStatus.PICKED_UP:
                update_data["pickedUpAt"] = datetime.utcnow()

            result = await self.collection.find_one_and_update(
                {"orderId": order_id},
                {"$set": update_data},
                return_document=True
            )

            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"Updated order {order_id} status to {status}")

            return result

        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            return None

    async def find_by_restaurant_and_location(
        self,
        restaurant_id: str,
        location_id: str,
        status: Optional[OrderStatus] = None
    ) -> List[dict]:
        """Find orders by restaurant and location"""
        try:
            query = {
                "restaurantId": restaurant_id,
                "locationId": location_id
            }

            if status:
                query["status"] = status

            cursor = self.collection.find(query).sort("createdAt", -1)

            orders = []
            async for order in cursor:
                order["_id"] = str(order["_id"])
                orders.append(order)

            logger.debug(f"Found {len(orders)} orders for restaurant {restaurant_id}, location {location_id}")
            return orders

        except Exception as e:
            logger.error(f"Error finding orders: {e}")
            return []

    async def find_today_orders(
        self,
        restaurant_id: str,
        location_id: str
    ) -> List[dict]:
        """Find today's orders for a restaurant location (timezone-aware)"""
        try:
            # Get location to retrieve timezone
            from app.core.database import db
            location = await db.db.locations.find_one({
                "_id": location_id,
                "restaurantId": restaurant_id
            })

            if not location:
                logger.error(f"Location not found: {location_id}")
                return []

            # Get location timezone (default to UTC if not set)
            from zoneinfo import ZoneInfo
            from datetime import date, time

            tz_name = location.get("timezone", "UTC")
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                logger.warning(f"Invalid timezone {tz_name}, using UTC")
                tz = ZoneInfo("UTC")

            # Calculate today's date range in location timezone
            now_local = datetime.now(tz)
            today_start_local = datetime.combine(now_local.date(), time.min).replace(tzinfo=tz)
            today_end_local = datetime.combine(now_local.date(), time.max).replace(tzinfo=tz)

            # Convert to UTC for database query
            today_start_utc = today_start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            today_end_utc = today_end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            logger.debug(f"Querying orders for {tz_name}: {today_start_local} to {today_end_local}")

            query = {
                "restaurantId": restaurant_id,
                "locationId": location_id,
                "createdAt": {
                    "$gte": today_start_utc,
                    "$lte": today_end_utc
                }
            }

            cursor = self.collection.find(query).sort("createdAt", -1)

            orders = []
            async for order in cursor:
                order["_id"] = str(order["_id"])
                orders.append(order)

            logger.debug(f"Found {len(orders)} orders today for {restaurant_id}/{location_id}")
            return orders

        except Exception as e:
            logger.error(f"Error finding today's orders: {e}")
            return []

    async def save_preview_order(self, preview_data: dict) -> dict:
        """Save preview order to temporary collection"""
        try:
            preview_data["createdAt"] = datetime.utcnow()
            result = await self.preview_collection.insert_one(preview_data)
            preview_data["_id"] = str(result.inserted_id)

            logger.info(f"Saved preview order: {preview_data['previewOrderId']}")
            return preview_data

        except Exception as e:
            logger.error(f"Error saving preview order: {e}")
            raise

    async def find_preview_by_id(self, preview_id: str) -> Optional[dict]:
        """Find preview order by ID"""
        try:
            preview = await self.preview_collection.find_one({"previewOrderId": preview_id})

            if preview:
                preview["_id"] = str(preview["_id"])
                logger.debug(f"Found preview order: {preview_id}")
            else:
                logger.warning(f"Preview order not found: {preview_id}")

            return preview

        except Exception as e:
            logger.error(f"Error finding preview order {preview_id}: {e}")
            return None

    async def delete_preview_order(self, preview_id: str):
        """Delete preview order after conversion to real order"""
        try:
            result = await self.preview_collection.delete_one({"previewOrderId": preview_id})

            if result.deleted_count > 0:
                logger.info(f"Deleted preview order: {preview_id}")
            else:
                logger.warning(f"Preview order not found for deletion: {preview_id}")

        except Exception as e:
            logger.error(f"Error deleting preview order {preview_id}: {e}")
