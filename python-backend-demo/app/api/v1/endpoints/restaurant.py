"""Restaurant API endpoints (compatible with mobile app)"""

from fastapi import APIRouter, Depends, Path, Query, Request, Header
from typing import List, Optional
from loguru import logger
from datetime import datetime
import uuid
from pydantic import BaseModel

from app.models.schemas.response import ApiResponse
from app.models.schemas.order import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService
from app.dependencies import get_order_repository, get_order_service

router = APIRouter()

from app.repositories.restaurant_repository import RestaurantRepository
from app.dependencies import get_restaurant_repository
from app.core.database import db
from bson.objectid import ObjectId


class OrderStatusUpdateRequest(BaseModel):
    """Order status update request from mobile app"""
    orderId: str
    orderStatus: str


class MultilingualText(BaseModel):
    """Multilingual text with en, es, pt support"""
    en: str
    es: Optional[str] = None
    pt: Optional[str] = None


@router.post(
    "/create/{user_id}",
    summary="Create restaurant",
    description="Create a new restaurant for a user"
)
async def create_restaurant(
    user_id: str = Path(..., description="User ID")
):
    """
    Create a new restaurant.

    TODO: Implement actual restaurant creation.
    """
    logger.info(f"POST /restaurant/create/{user_id}")
    return {
        "data": {
            "_id": str(uuid.uuid4()),
            "name": "New Restaurant",
            "concept": "Restaurant",
            "logo": ""
        },
        "message": "Restaurant created"
    }


@router.post(
    "/{restaurant_id}/location/create",
    summary="Create location",
    description="Create a new location for a restaurant"
)
async def create_location(
    restaurant_id: str = Path(..., description="Restaurant ID")
):
    """
    Create a new location for a restaurant.

    TODO: Implement actual location creation.
    """
    logger.info(f"POST /restaurant/{restaurant_id}/location/create")
    return {
        "data": {
            "_id": str(uuid.uuid4()),
            "restaurantId": restaurant_id,
            "name": "New Location",
            "address": {}
        },
        "message": "Location created"
    }


@router.get(
    "/restaurants/{restaurant_id}/locations",
    summary="Get locations for restaurant",
    description="Get all locations for a restaurant"
)
async def get_locations_by_restaurant(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository)
):
    """
    Get all locations for a restaurant.
    """
    logger.info(f"GET /restaurant/restaurants/{restaurant_id}/locations")

    # Fetch real locations from database
    locations = await restaurant_repo.find_locations_by_restaurant(restaurant_id)

    # Transform locations to match expected format
    result = [{
        "_id": loc["_id"],
        "restaurantId": loc.get("restaurantId", restaurant_id),
        "name": loc.get("name", ""),
        "address": loc.get("address", ""),
        "locationSlug": loc.get("locationSlug", ""),
        "isMobile": loc.get("isMobile", False),
        "isActive": loc.get("isActive", True),
        "isOpen": loc.get("isOpen", True),
        "alertNumbers": loc.get("alertNumbers", []),
        "contact": loc.get("contact", {}),
        "workingHours": loc.get("workingHours", []),
        "timezone": loc.get("timezone", "")
    } for loc in locations]

    return {
        "data": result,
        "message": None
    }


@router.get(
    "/{user_id}",
    summary="Get restaurants for user",
    description="Get all restaurants associated with a user"
)
async def get_restaurants_by_user(
    user_id: str = Path(..., description="User ID"),
    restaurant_repo: RestaurantRepository = Depends(get_restaurant_repository)
):
    """
    Get all restaurants for a user.

    For now, returns all restaurants in the system.
    TODO: Implement proper user-restaurant relationship.
    """
    logger.info(f"GET /restaurant/{user_id}")

    # Get all restaurants (simplified for now)
    restaurants = await restaurant_repo.find_all()

    # Transform to match frontend expectation
    result = [{
        "_id": r["_id"],
        "name": r.get("name", ""),
        "concept": r.get("concept", ""),
        "logo": r.get("logo", "")
    } for r in restaurants]

    return {
        "data": result,
        "message": None
    }


@router.get(
    "/orders/today/{restaurant_id}/{location_id}",
    summary="Get today's orders (Restaurant App)",
    description="Get today's orders in format expected by restaurant management app"
)
async def get_today_orders_restaurant(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    Get today's orders for restaurant dashboard.

    Returns orders in the format expected by the mobile restaurant management app:
    - _id (MongoDB ID)
    - orderCode (order identifier)
    - restaurant (restaurant ID)
    - meta.correlationId
    - items with priceCents (not price)
    - totalPriceCents (not totalCents)
    - startedAt timestamp
    """
    logger.info(f"GET /restaurant/orders/today/{restaurant_id}/{location_id}")

    # Get today's orders from repository
    orders = await order_repo.find_today_orders(restaurant_id, location_id)

    # Transform orders to match mobile app format
    transformed_orders = []
    for order in orders:
        # Transform items to use priceCents instead of price
        transformed_items = []
        for item in order.get("items", []):
            transformed_item = {
                "id": item.get("id"),
                "menuItemId": item.get("menuItemId"),
                "name": item.get("name"),
                "priceCents": item.get("price", 0),  # Convert price to priceCents
                "notes": item.get("notes"),
                "modifiers": item.get("modifiers", []),
                "variants": item.get("variants", []),
                "stationTags": item.get("stationTags", []),
                "startedAt": item.get("startedAt"),
                "completedAt": item.get("completedAt")
            }
            transformed_items.append(transformed_item)

        # Build transformed order in mobile app format
        transformed_order = {
            "_id": order.get("_id"),
            "orderCode": order.get("orderId"),  # Mobile app uses orderCode
            "paymentId": order.get("paymentId", ""),
            "restaurant": order.get("restaurantId"),  # Mobile app uses restaurant
            "meta": {
                "correlationId": str(uuid.uuid4())  # Generate correlation ID
            },
            "customer": order.get("customer", {}),
            "origin": order.get("origin", {}),
            "items": transformed_items,
            "startedAt": order.get("createdAt"),  # Use createdAt as startedAt
            "totalPriceCents": order.get("totalCents", 0),  # Mobile app uses totalPriceCents
            "getSms": False,
            "status": order.get("status"),
            "endedAt": order.get("pickedUpAt")  # Optional end time
        }
        transformed_orders.append(transformed_order)

    logger.debug(f"Returning {len(transformed_orders)} orders for today")
    return transformed_orders


@router.get(
    "/orders/{restaurant_id}/{location_id}/{order_id}",
    summary="Get single order (Restaurant App)",
    description="Get single order in format expected by restaurant management app"
)
async def get_single_order_restaurant(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    order_id: str = Path(..., description="Order ID"),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    Get a single order for restaurant dashboard.

    Returns order in the format expected by the mobile restaurant management app.
    """
    logger.info(f"GET /restaurant/orders/{restaurant_id}/{location_id}/{order_id}")

    # Get order from repository
    order = await order_repo.find_by_id(order_id)

    if not order:
        return {"error": "Order not found"}, 404

    # Transform items to use priceCents instead of price
    transformed_items = []
    for item in order.get("items", []):
        transformed_item = {
            "id": item.get("id"),
            "menuItemId": item.get("menuItemId"),
            "name": item.get("name"),
            "priceCents": item.get("price", 0),
            "notes": item.get("notes"),
            "modifiers": item.get("modifiers", []),
            "variants": item.get("variants", []),
            "stationTags": item.get("stationTags", []),
            "startedAt": item.get("startedAt"),
            "completedAt": item.get("completedAt")
        }
        transformed_items.append(transformed_item)

    # Build transformed order
    transformed_order = {
        "_id": order.get("_id"),
        "orderCode": order.get("orderId"),
        "paymentId": order.get("paymentId", ""),
        "restaurant": order.get("restaurantId"),
        "meta": {
            "correlationId": str(uuid.uuid4())
        },
        "customer": order.get("customer", {}),
        "origin": order.get("origin", {}),
        "items": transformed_items,
        "startedAt": order.get("createdAt"),
        "totalPriceCents": order.get("totalCents", 0),
        "getSms": False,
        "status": order.get("status"),
        "endedAt": order.get("pickedUpAt")
    }

    return {
        "data": transformed_order
    }


@router.post(
    "/order-status/",
    summary="Update order status (Restaurant App)",
    description="Update order status from restaurant management app"
)
async def update_order_status_restaurant(
    request: OrderStatusUpdateRequest,
    order_service: OrderService = Depends(get_order_service),
    x_request_id: Optional[str] = Header(None, alias="X-Request-Id")
):
    """
    Update order status from restaurant dashboard.

    This endpoint accepts status updates in the format expected by the mobile app
    and converts them to the internal format.

    Status mapping:
    - OrderCreated -> pending
    - OrderAccepted -> accepted
    - ReadyForPickup -> ready
    - OrderCompleted -> picked_up
    """
    logger.info(f"POST /restaurant/order-status - order={request.orderId}, status={request.orderStatus}")

    # Map mobile app status names to internal OrderStatus enum
    status_mapping = {
        "OrderCreated": OrderStatus.ORDER_CREATED,
        "OrderAccepted": OrderStatus.ORDER_ACCEPTED,
        "ReadyForPickup": OrderStatus.READY_FOR_PICKUP,
        "OrderCompleted": OrderStatus.ORDER_DELIVERED
    }

    internal_status = status_mapping.get(request.orderStatus, OrderStatus.PENDING)

    # Use the existing order service to update status
    from app.models.schemas.order import UpdateOrderStatusRequest
    update_request = UpdateOrderStatusRequest(
        orderId=request.orderId,
        status=internal_status,
        estimatedMinutes=None
    )

    result = await order_service.update_order_status(update_request)

    # Return in format expected by mobile app
    return {
        "success": True,
        "orderId": result.orderId,
        "status": request.orderStatus  # Return the mobile app status format
    }


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/menus",
    summary="Get menus for location",
    description="Get all menus for a specific restaurant location"
)
async def get_menus_for_location(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID")
):
    """
    Get all menus for a restaurant location.

    Returns menu summaries with basic information.
    """
    logger.info(f"GET /restaurant/restaurants/{restaurant_id}/locations/{location_id}/menus")

    try:
        menus_collection = db.db["menus"]

        # In this database, locationId is stored as string, not ObjectId
        query = {
            "restaurantId": restaurant_id,
            "locationId": location_id  # Use string directly
        }

        projection = {
            "_id": 1,
            "menuSlug": 1,
            "name": 1,
            "available": 1
        }

        cursor = menus_collection.find(query, projection)
        menus = []

        async for menu in cursor:
            menu["_id"] = str(menu["_id"])
            menus.append(menu)

        logger.debug(f"Found {len(menus)} menus for {restaurant_id}/{location_id}")

        return {
            "data": menus
        }

    except Exception as e:
        logger.error(f"Error fetching menus: {e}")
        return {
            "data": []
        }


class MenuCreateRequest(BaseModel):
    """Request body for creating a new menu"""
    menuSlug: str
    name: MultilingualText
    salesTax: Optional[float] = 10.25
    available: Optional[bool] = True


@router.post(
    "/restaurants/{restaurant_id}/locations/{location_id}/menu",
    summary="Create new menu",
    description="Create a new menu for a restaurant location"
)
async def create_menu(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    menu_data: MenuCreateRequest = None
):
    """
    Create a new menu for a restaurant location.

    Returns the created menu ID.
    """
    logger.info(f"POST /restaurant/restaurants/{restaurant_id}/locations/{location_id}/menu")

    try:
        menus_collection = db.db["menus"]

        # Generate new menu ID
        new_menu_id = f"{restaurant_id}_menu_{menu_data.menuSlug}"

        # Check if menu with this ID already exists
        existing = await menus_collection.find_one({"_id": new_menu_id})
        if existing:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail=f"Menu with slug '{menu_data.menuSlug}' already exists"
            )

        # Create menu document
        menu_doc = {
            "_id": new_menu_id,
            "restaurantId": restaurant_id,
            "locationId": location_id,
            "menuSlug": menu_data.menuSlug,
            "name": menu_data.name.model_dump(),
            "salesTax": menu_data.salesTax,
            "available": menu_data.available,
            "categories": [],
            "items": [],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await menus_collection.insert_one(menu_doc)

        logger.info(f"Created new menu: {new_menu_id}")

        return {
            "data": {
                "_id": new_menu_id,
                "menuSlug": menu_data.menuSlug,
                "name": menu_data.name.model_dump(),
                "available": menu_data.available
            }
        }

    except Exception as e:
        logger.error(f"Error creating menu: {e}")
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create menu: {str(e)}"
        )


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/menus/{menu_id}",
    summary="Get specific menu with categories",
    description="Get full menu details including categories and items"
)
async def get_menu_by_id(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    menu_id: str = Path(..., description="Menu ID")
):
    """
    Get a specific menu with all its categories and items.

    Returns the complete menu document including categories, items, modifiers, etc.
    """
    logger.info(f"GET /restaurant/restaurants/{restaurant_id}/locations/{location_id}/menus/{menu_id}")

    try:
        menus_collection = db.db["menus"]

        # Query by _id (menu_id is stored as string in this database)
        menu = await menus_collection.find_one({
            "_id": menu_id,
            "restaurantId": restaurant_id,
            "locationId": location_id
        })

        if not menu:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Menu not found for restaurant: {restaurant_id}, location: {location_id}, menu: {menu_id}"
            )

        logger.debug(f"Found menu: {menu_id}")

        return {
            "data": menu
        }

    except Exception as e:
        logger.error(f"Error fetching menu by ID: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Menu not found")


# Category Management Models
class CreateUpdateCategoryRequest(BaseModel):
    """Request body for creating or updating a category"""
    id: Optional[str] = None  # If present = UPDATE, else = CREATE
    name: MultilingualText
    description: MultilingualText
    sortOrder: int
    emoji: Optional[str] = None


@router.post(
    "/{restaurant_id}/location/{location_id}/menu/{menu_id}/category",
    summary="Create or update a menu category",
    description="Create a new category or update an existing one. If 'id' field is provided: UPDATE, else: CREATE (new ID auto-generated)"
)
async def upsert_category(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    menu_id: str = Path(..., description="Menu ID"),
    category_data: CreateUpdateCategoryRequest = None
):
    """
    Upsert (create or update) a menu category.

    - If 'id' field is provided in request body: UPDATE operation
    - If 'id' field is NOT provided: CREATE operation (new ID auto-generated)
    - Sort order is auto-calculated on creation if not provided
    """
    logger.info(f"POST /{restaurant_id}/location/{location_id}/menu/{menu_id}/category")

    try:
        menus_collection = db.db["menus"]

        # Check if menu exists
        menu = await menus_collection.find_one({
            "_id": menu_id,
            "restaurantId": restaurant_id,
            "locationId": location_id
        })

        if not menu:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Menu not found: {menu_id}"
            )

        # Prepare category document
        category_doc = {
            'name': category_data.name.model_dump(),
            'description': category_data.description.model_dump(),
            'sortOrder': category_data.sortOrder,
        }

        if category_data.emoji:
            category_doc['emoji'] = category_data.emoji

        if category_data.id:
            # UPDATE existing category
            category_doc['id'] = category_data.id

            result = await menus_collection.update_one(
                {
                    '_id': menu_id,
                    'restaurantId': restaurant_id,
                    'locationId': location_id,
                    'categories.id': category_data.id
                },
                {
                    '$set': {
                        'categories.$': category_doc
                    }
                }
            )

            if result.matched_count == 0:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=404,
                    detail=f"Category not found: {category_data.id}"
                )

            logger.info(f"Updated category: {category_data.id}")
        else:
            # CREATE new category
            # Generate new ObjectId for category
            new_category_id = str(ObjectId())
            category_doc['id'] = new_category_id

            # Auto-calculate sort order if needed
            categories = menu.get('categories', [])
            if category_data.sortOrder == 0:
                category_doc['sortOrder'] = len(categories) + 1

            result = await menus_collection.update_one(
                {
                    '_id': menu_id,
                    'restaurantId': restaurant_id,
                    'locationId': location_id
                },
                {
                    '$push': {
                        'categories': category_doc
                    }
                }
            )

            logger.info(f"Created new category with ID: {new_category_id}")

        return {
            "data": True
        }

    except Exception as e:
        logger.error(f"Error upserting category: {e}")
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upsert category: {str(e)}"
        )
