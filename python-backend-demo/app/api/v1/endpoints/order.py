"""Order API endpoints"""

from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional
from loguru import logger

from app.models.schemas.response import ApiResponse
from app.models.schemas.order import (
    CreateOrderRequest,
    PreviewOrderRequest,
    PreviewOrderResponse,
    OrderResponse,
    OrderStatusResponse,
    OrderConfirmationResponse,
    UpdateOrderStatusRequest,
    OrderStatus
)
from app.services.order_service import OrderService
from app.dependencies import get_order_service

router = APIRouter()


@router.post(
    "/cart/preview-order",
    response_model=ApiResponse[PreviewOrderResponse],
    summary="Preview order totals",
    description="Calculate order totals before placing the order"
)
async def preview_order(
    request: PreviewOrderRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Preview order totals including tax and discounts.

    This endpoint calculates the total cost of an order without actually creating it.
    Useful for displaying the final price to customers before they confirm.

    **Returns:**
    - Preview order ID
    - Subtotal, tax, and total amounts
    - Itemized list
    """
    logger.info(f"POST /cart/preview-order - restaurant={request.restaurantId}")

    preview = await service.create_preview_order(request)
    return ApiResponse(data=preview)


@router.post(
    "/orders",
    response_model=ApiResponse[OrderConfirmationResponse],
    summary="Create new order",
    description="Place a new order for a restaurant location"
)
async def create_order(
    request: CreateOrderRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Create a new order.

    This endpoint creates a new order in the system and returns confirmation details.
    The order starts in 'pending' status and can be updated by restaurant staff.

    **Parameters:**
    - Restaurant and location information
    - Customer information (name, phone)
    - Order items with quantities and modifiers
    - Payment information (optional)

    **Returns:**
    - Order ID for tracking
    - Creation timestamp
    - Initial status
    """
    logger.info(f"POST /orders - restaurant={request.restaurantId}, location={request.locationId}")

    confirmation = await service.create_order(request)
    return ApiResponse(data=confirmation)


@router.get(
    "/orders/{order_id}",
    response_model=ApiResponse[OrderResponse],
    summary="Get order details",
    description="Retrieve complete order information by order ID"
)
async def get_order(
    order_id: str = Path(..., description="Order ID"),
    service: OrderService = Depends(get_order_service)
):
    """
    Get complete order details.

    Retrieves all information about a specific order including items,
    customer info, pricing, and current status.

    **Parameters:**
    - **order_id**: Unique order identifier

    **Returns:**
    - Complete order information
    """
    logger.info(f"GET /orders/{order_id}")

    order = await service.get_order(order_id)
    return ApiResponse(data=order)


@router.get(
    "/orders/{order_id}/status",
    response_model=ApiResponse[OrderStatusResponse],
    summary="Get order status",
    description="Get current status of an order"
)
async def get_order_status(
    order_id: str = Path(..., description="Order ID"),
    service: OrderService = Depends(get_order_service)
):
    """
    Get order status.

    Returns the current status of an order without full order details.
    Useful for quick status checks.

    **Parameters:**
    - **order_id**: Unique order identifier

    **Returns:**
    - Current order status
    - Last update timestamp
    """
    logger.info(f"GET /orders/{order_id}/status")

    status = await service.get_order_status(order_id)
    return ApiResponse(data=status)


@router.patch(
    "/orders/status",
    response_model=ApiResponse[OrderStatusResponse],
    summary="Update order status",
    description="Update the status of an order (restaurant staff)"
)
async def update_order_status(
    request: UpdateOrderStatusRequest,
    service: OrderService = Depends(get_order_service)
):
    """
    Update order status.

    Allows restaurant staff to update the order status through various stages:
    - pending → accepted (order confirmed by restaurant)
    - accepted → ready (order is ready for pickup)
    - ready → picked_up (customer picked up order)

    Socket.IO events are automatically emitted to notify mobile app users.

    **Parameters:**
    - **orderId**: Order to update
    - **status**: New status
    - **estimatedMinutes**: Estimated prep time (optional, for accepted status)

    **Returns:**
    - Updated order status
    - Update timestamp
    """
    logger.info(f"PATCH /orders/status - order={request.orderId}, status={request.status}")

    status = await service.update_order_status(request)
    return ApiResponse(data=status)


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/orders",
    response_model=ApiResponse[List[OrderResponse]],
    summary="Get restaurant orders",
    description="Get all orders for a restaurant location"
)
async def get_restaurant_orders(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    service: OrderService = Depends(get_order_service)
):
    """
    Get orders for a restaurant location.

    Returns all orders for a specific restaurant location, optionally
    filtered by status. Sorted by creation time (newest first).

    **Parameters:**
    - **restaurant_id**: Restaurant identifier
    - **location_id**: Location identifier
    - **status**: Optional status filter

    **Returns:**
    - List of orders
    """
    logger.info(f"GET /restaurants/{restaurant_id}/locations/{location_id}/orders")

    orders = await service.get_restaurant_orders(restaurant_id, location_id, status)
    return ApiResponse(data=orders)


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/orders/today",
    response_model=ApiResponse[List[OrderResponse]],
    summary="Get today's orders",
    description="Get all orders for today for a restaurant location"
)
async def get_today_orders(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    service: OrderService = Depends(get_order_service)
):
    """
    Get today's orders.

    Returns all orders placed today for a specific restaurant location.
    Useful for daily reporting and kitchen display systems.

    **Parameters:**
    - **restaurant_id**: Restaurant identifier
    - **location_id**: Location identifier

    **Returns:**
    - List of today's orders
    """
    logger.info(f"GET /restaurants/{restaurant_id}/locations/{location_id}/orders/today")

    orders = await service.get_today_orders(restaurant_id, location_id)
    return ApiResponse(data=orders)
