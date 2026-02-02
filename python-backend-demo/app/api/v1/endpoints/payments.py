"""Payments API endpoints"""

from fastapi import APIRouter, Path, Body, Depends, HTTPException
from loguru import logger
from typing import Optional
import uuid

from app.repositories.order_repository import OrderRepository
from app.dependencies import get_order_repository

router = APIRouter()


@router.post(
    "/start-transaction/{restaurant_id}",
    summary="Start payment transaction",
    description="Initialize a payment transaction for the order"
)
async def start_transaction(
    restaurant_id: str = Path(..., description="Restaurant ID")
):
    """
    Start a payment transaction.

    Returns a transaction token for the payment processor.
    For testing/development, this returns a mock token.
    """
    logger.info(f"POST /payments/start-transaction/{restaurant_id}")

    # Generate a mock transaction token for development
    transaction_token = f"TXN-{uuid.uuid4().hex[:16].upper()}"

    return {
        "transactionToken": transaction_token,
        "externalTransactionId": f"EXT-{uuid.uuid4().hex[:12].upper()}"
    }


@router.post(
    "/complete-transaction",
    summary="Complete payment transaction",
    description="Complete a payment transaction and create the order"
)
async def complete_transaction(
    body: dict = Body(...),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    Complete a payment transaction.

    This endpoint processes the payment and creates the order in the system.
    For development, this uses mock payment processing.
    """
    logger.info("POST /payments/complete-transaction")

    preview_order_id = body.get("previewOrderId")
    transaction_token = body.get("transactionToken")

    if not preview_order_id or not transaction_token:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Retrieve preview order from database
    preview_order = await order_repo.find_preview_by_id(preview_order_id)

    if not preview_order:
        raise HTTPException(status_code=404, detail="Preview order not found")

    # Mock payment processing (always succeeds for development)
    payment_result = {
        "status": "Approved",
        "transactionId": f"PAY-{uuid.uuid4().hex[:12].upper()}",
        "message": "Payment processed successfully"
    }

    # Create confirmed order from preview data
    order_data = {
        "restaurantId": preview_order["restaurantId"],
        "locationId": preview_order["locationId"],
        "locationSlug": preview_order.get("locationSlug", ""),
        "origin": preview_order.get("origin", {}),
        "customer": preview_order.get("customer", {}),
        "items": preview_order["items"],
        "subtotalCents": preview_order["subtotalCents"],
        "taxCents": preview_order["taxCents"],
        "totalCents": preview_order["totalPriceCents"],
        "paymentId": payment_result["transactionId"],
        "transactionDetails": payment_result,
        "discount": preview_order.get("discount"),
    }

    order = await order_repo.create_order(order_data)

    # Delete preview order after successful conversion
    await order_repo.delete_preview_order(preview_order_id)

    logger.info(f"Created order {order['orderId']} from preview {preview_order_id} with payment")

    return {
        "transaction": {
            "resultMessage": payment_result["message"],
            "resultStatus": payment_result["status"]
        },
        "orderId": order["orderId"]
    }


@router.post(
    "/place-order-without-payment",
    summary="Place order without payment",
    description="Create an order without processing payment (for testing or pay-at-counter scenarios)"
)
async def place_order_without_payment(
    body: dict = Body(...),
    order_repo: OrderRepository = Depends(get_order_repository)
):
    """
    Place an order without payment.

    Useful for testing or scenarios where payment happens at the counter.
    """
    logger.info("POST /payments/place-order-without-payment")

    preview_order_id = body.get("previewOrderId")

    if not preview_order_id:
        raise HTTPException(status_code=400, detail="Preview order ID is required")

    # Retrieve preview order from database
    preview_order = await order_repo.find_preview_by_id(preview_order_id)

    if not preview_order:
        raise HTTPException(status_code=404, detail="Preview order not found")

    # Create confirmed order from preview data
    order_data = {
        "restaurantId": preview_order["restaurantId"],
        "locationId": preview_order["locationId"],
        "locationSlug": preview_order.get("locationSlug", ""),
        "origin": preview_order.get("origin", {}),
        "customer": preview_order.get("customer", {}),
        "items": preview_order["items"],
        "subtotalCents": preview_order["subtotalCents"],
        "taxCents": preview_order["taxCents"],
        "totalCents": preview_order["totalPriceCents"],
        "paymentId": None,
        "transactionDetails": {"paymentMethod": "cash"},
        "discount": preview_order.get("discount"),
    }

    order = await order_repo.create_order(order_data)

    # Delete preview order after successful conversion
    await order_repo.delete_preview_order(preview_order_id)

    logger.info(f"Created order {order['orderId']} from preview {preview_order_id}")

    return {
        "data": {
            "orderId": order["orderId"],
            "status": order["status"],
            "paymentStatus": "not_required"
        },
        "message": "Order placed successfully"
    }
