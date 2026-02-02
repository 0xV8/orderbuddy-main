"""Order business logic service"""

from typing import Optional, List
from loguru import logger
from datetime import datetime
import uuid

from app.repositories.order_repository import OrderRepository
from app.repositories.menu_repository import MenuRepository
from app.core.exceptions import AppException
from app.models.schemas.order import (
    CreateOrderRequest,
    PreviewOrderRequest,
    PreviewOrderResponse,
    OrderResponse,
    OrderStatusResponse,
    OrderConfirmationResponse,
    UpdateOrderStatusRequest,
    OrderStatus,
    OrderItemResponse
)
from app.core.socketio import emit_order_accepted, emit_order_ready_for_pickup, emit_order_completed


class OrderService:
    """Service for order business logic"""

    def __init__(self, order_repo: OrderRepository, menu_repo: MenuRepository):
        self.order_repo = order_repo
        self.menu_repo = menu_repo

    async def create_preview_order(
        self,
        request: PreviewOrderRequest
    ) -> PreviewOrderResponse:
        """Create a preview order for price calculation"""
        try:
            # Get sales tax rate (default to 8% if menu not specified)
            sales_tax = 0.08

            if request.menuId:
                # Get menu to calculate sales tax
                menu = await self.menu_repo.find_by_id(
                    request.restaurantId,
                    request.locationId,
                    request.menuId
                )

                if menu:
                    sales_tax = menu.get("salesTax", 0.08)

            # Calculate totals
            subtotal_cents = 0
            for item in request.items:
                item_subtotal = item.price * item.quantity

                # Add variant pricing
                for variant in item.variants:
                    item_subtotal += variant.priceCents * item.quantity

                # Add modifier prices with free choices logic
                for modifier in item.modifiers:
                    selected_count = len(modifier.options)
                    free_choices = getattr(modifier, 'freeChoices', 0)
                    extra_choice_price = getattr(modifier, 'extraChoicePriceCents', 0)

                    if selected_count > free_choices:
                        # Only charge for choices beyond free limit
                        extra_count = selected_count - free_choices
                        item_subtotal += (extra_count * extra_choice_price) * item.quantity
                    # If selected_count <= free_choices, no extra charge

                subtotal_cents += item_subtotal

            # Calculate tax
            tax_cents = int(subtotal_cents * sales_tax)

            # Apply discount if provided
            discount_cents = 0
            if request.discount:
                discount_cents = request.discount.get("amountCents", 0)

            total_cents = subtotal_cents + tax_cents - discount_cents

            # Generate preview order ID
            preview_id = f"PREV-{uuid.uuid4().hex[:8].upper()}"

            # Save preview order to database
            preview_data = {
                "previewOrderId": preview_id,
                "restaurantId": request.restaurantId,
                "locationId": request.locationId,
                "locationSlug": request.locationSlug,
                "items": [item.model_dump() for item in request.items],
                "subtotalCents": subtotal_cents,
                "taxCents": tax_cents,
                "discountCents": discount_cents,
                "totalPriceCents": total_cents,
                "customer": request.customer.model_dump() if request.customer else None,
                "origin": request.origin.model_dump() if request.origin else None,
                "getSms": request.getSms,
                "discount": request.discount,
                "menuId": request.menuId,
            }

            await self.order_repo.save_preview_order(preview_data)

            logger.info(f"Created and saved preview order: {preview_id}")

            return PreviewOrderResponse(
                previewOrderId=preview_id,
                subtotalCents=subtotal_cents,
                taxCents=tax_cents,
                totalPriceCents=total_cents,
                items=request.items
            )

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error creating preview order: {e}")
            raise AppException(
                status_code=500,
                message="Failed to create preview order",
                detail=str(e)
            )

    async def create_order(
        self,
        request: CreateOrderRequest
    ) -> OrderConfirmationResponse:
        """Create a new order"""
        try:
            # Calculate order totals
            subtotal_cents = 0
            order_items = []

            for item in request.items:
                item_subtotal = item.price * item.quantity

                # Add variant pricing
                for variant in item.variants:
                    item_subtotal += variant.priceCents * item.quantity

                # Add modifier prices with free choices logic
                for modifier in item.modifiers:
                    selected_count = len(modifier.options)
                    free_choices = getattr(modifier, 'freeChoices', 0)
                    extra_choice_price = getattr(modifier, 'extraChoicePriceCents', 0)

                    if selected_count > free_choices:
                        # Only charge for choices beyond free limit
                        extra_count = selected_count - free_choices
                        item_subtotal += (extra_count * extra_choice_price) * item.quantity

                subtotal_cents += item_subtotal

                order_items.append({
                    "id": item.id,
                    "menuItemId": item.menuItemId,
                    "name": item.name,
                    "price": item.price,
                    "quantity": item.quantity,
                    "subtotalCents": item_subtotal,
                    "notes": item.notes,
                    "modifiers": [m.model_dump() for m in item.modifiers],
                    "variants": [v.model_dump() for v in item.variants] if item.variants else [],
                    "stationTags": item.stationTags,
                    "startedAt": None,
                    "completedAt": None
                })

            # Calculate tax (default 8% if not found)
            tax_cents = int(subtotal_cents * 0.08)
            total_cents = subtotal_cents + tax_cents

            # Apply discount if provided
            if request.discount:
                discount_amount = request.discount.get("amountCents", 0)
                total_cents -= discount_amount

            # Create order document
            order_data = {
                "restaurantId": request.restaurantId,
                "locationId": request.locationId,
                "locationSlug": request.locationSlug,
                "origin": request.origin.model_dump(),
                "customer": request.customer.model_dump(),
                "items": order_items,
                "subtotalCents": subtotal_cents,
                "taxCents": tax_cents,
                "totalCents": total_cents,
                "paymentId": request.paymentId,
                "transactionDetails": request.transactionDetails,
                "discount": request.discount,
            }

            # Save order to database
            order = await self.order_repo.create_order(order_data)

            logger.info(f"Order created: {order['orderId']}")

            return OrderConfirmationResponse(
                orderId=order["orderId"],
                createdAt=order["createdAt"],
                estimatedReadyAt=order.get("estimatedReadyAt"),
                status=OrderStatus.ORDER_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise AppException(
                status_code=500,
                message="Failed to create order",
                detail=str(e)
            )

    async def get_order(self, order_id: str) -> OrderResponse:
        """Get order by ID"""
        order = await self.order_repo.find_by_id(order_id)

        if not order:
            raise AppException(
                status_code=404,
                message="Order not found",
                detail=f"Order with ID '{order_id}' does not exist"
            )

        logger.info(f"Retrieved order: {order_id}")
        return OrderResponse(**order)

    async def get_order_status(self, order_id: str) -> OrderStatusResponse:
        """Get order status"""
        order = await self.order_repo.find_by_id(order_id)

        if not order:
            raise AppException(
                status_code=404,
                message="Order not found",
                detail=f"Order with ID '{order_id}' does not exist"
            )

        return OrderStatusResponse(
            orderId=order["orderId"],
            status=order["status"],
            updatedAt=order["updatedAt"],
            estimatedReadyAt=order.get("estimatedReadyAt")
        )

    async def update_order_status(
        self,
        request: UpdateOrderStatusRequest
    ) -> OrderStatusResponse:
        """Update order status"""
        try:
            # Get current order
            order = await self.order_repo.find_by_id(request.orderId)

            if not order:
                raise AppException(
                    status_code=404,
                    message="Order not found",
                    detail=f"Order with ID '{request.orderId}' does not exist"
                )

            # Update status in database
            updated_order = await self.order_repo.update_status(
                request.orderId,
                request.status,
                request.estimatedMinutes
            )

            if not updated_order:
                raise AppException(
                    status_code=500,
                    message="Failed to update order status"
                )

            # Emit Socket.IO events based on status change
            await self._emit_status_events(
                request.orderId,
                order["restaurantId"],
                request.status
            )

            logger.info(f"Updated order {request.orderId} status to {request.status}")

            return OrderStatusResponse(
                orderId=updated_order["orderId"],
                status=updated_order["status"],
                updatedAt=updated_order["updatedAt"],
                estimatedReadyAt=updated_order.get("estimatedReadyAt")
            )

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            raise AppException(
                status_code=500,
                message="Failed to update order status",
                detail=str(e)
            )

    async def _emit_status_events(
        self,
        order_id: str,
        restaurant_id: str,
        status: OrderStatus
    ):
        """Emit Socket.IO events based on order status"""
        try:
            event_data = {
                "timestamp": datetime.utcnow().isoformat()
            }

            if status == OrderStatus.ORDER_ACCEPTED:
                await emit_order_accepted(order_id, restaurant_id, event_data)
            elif status == OrderStatus.READY_FOR_PICKUP:
                await emit_order_ready_for_pickup(order_id, restaurant_id, event_data)
            elif status == OrderStatus.ORDER_DELIVERED:
                await emit_order_completed(order_id, restaurant_id, event_data)

        except Exception as e:
            logger.error(f"Error emitting Socket.IO event: {e}")
            # Don't fail the status update if Socket.IO fails

    async def get_restaurant_orders(
        self,
        restaurant_id: str,
        location_id: str,
        status: Optional[OrderStatus] = None
    ) -> List[OrderResponse]:
        """Get orders for a restaurant location"""
        orders = await self.order_repo.find_by_restaurant_and_location(
            restaurant_id,
            location_id,
            status
        )

        return [OrderResponse(**order) for order in orders]

    async def get_today_orders(
        self,
        restaurant_id: str,
        location_id: str
    ) -> List[OrderResponse]:
        """Get today's orders for a restaurant location"""
        orders = await self.order_repo.find_today_orders(
            restaurant_id,
            location_id
        )

        return [OrderResponse(**order) for order in orders]
