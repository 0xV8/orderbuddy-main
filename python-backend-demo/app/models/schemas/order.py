"""Order API schemas"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enum - aligned with NestJS"""
    ORDER_CREATED = "order_created"
    ORDER_ACCEPTED = "order_accepted"
    READY_FOR_PICKUP = "ready_for_pickup"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"


class OriginInput(BaseModel):
    """Origin information"""
    id: str
    name: str


class CustomerInput(BaseModel):
    """Customer information"""
    name: str
    phone: str


class OrderItemModifierOption(BaseModel):
    """Order item modifier option"""
    id: str
    name: str
    priceCents: int


class OrderItemModifier(BaseModel):
    """Order item modifier"""
    id: str
    name: str
    options: List[OrderItemModifierOption] = []
    priceCents: Optional[int] = None  # Optional, calculated from options
    freeChoices: int = 0  # Number of free choices allowed
    extraChoicePriceCents: int = 0  # Price per extra choice beyond free limit


class OrderItemVariant(BaseModel):
    """Order item variant"""
    id: str
    name: str
    priceCents: int


class OrderItemInput(BaseModel):
    """Order item input"""
    id: str
    menuItemId: str
    name: str
    price: int
    quantity: int = 1
    notes: Optional[str] = None
    modifiers: List[OrderItemModifier] = []
    variants: List[OrderItemVariant] = []
    stationTags: List[str] = []


class CreateOrderRequest(BaseModel):
    """Create order request"""
    restaurantId: str
    locationId: str
    locationSlug: str
    origin: OriginInput
    customer: CustomerInput
    items: List[OrderItemInput]
    getSms: bool = False
    paymentId: Optional[str] = None
    transactionDetails: Optional[Any] = None
    discount: Optional[dict] = None


class PreviewOrderRequest(BaseModel):
    """Preview order request (for calculating totals)"""
    restaurantId: str
    locationId: str
    locationSlug: Optional[str] = None
    menuId: Optional[str] = None  # Optional, may not be known during preview
    origin: Optional[OriginInput] = None
    customer: Optional[CustomerInput] = None
    items: List[OrderItemInput]
    getSms: Optional[bool] = False
    discount: Optional[dict] = None


class PreviewOrderResponse(BaseModel):
    """Preview order response"""
    previewOrderId: str
    subtotalCents: int
    taxCents: int
    totalPriceCents: int
    items: List[OrderItemInput]


class OrderItemResponse(BaseModel):
    """Order item response"""
    id: str
    menuItemId: str
    name: str
    price: int
    quantity: int
    subtotalCents: int
    notes: Optional[str] = None
    modifiers: List[OrderItemModifier] = []
    variants: List[Any] = []
    stationTags: List[str] = []
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None


class OrderResponse(BaseModel):
    """Order response"""
    id: str = Field(..., alias="_id")
    orderId: str
    restaurantId: str
    locationId: str
    locationSlug: str
    origin: OriginInput
    customer: CustomerInput
    items: List[OrderItemResponse]
    status: OrderStatus
    subtotalCents: int
    taxCents: int
    totalCents: int
    paymentId: Optional[str] = None
    transactionDetails: Optional[Any] = None
    discount: Optional[dict] = None
    createdAt: datetime
    updatedAt: datetime
    estimatedReadyAt: Optional[datetime] = None
    readyAt: Optional[datetime] = None
    pickedUpAt: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class OrderStatusResponse(BaseModel):
    """Order status response"""
    orderId: str
    status: OrderStatus
    updatedAt: datetime
    estimatedReadyAt: Optional[datetime] = None


class OrderConfirmationResponse(BaseModel):
    """Order confirmation response"""
    orderId: str
    createdAt: datetime
    estimatedReadyAt: Optional[datetime] = None
    status: OrderStatus


class UpdateOrderStatusRequest(BaseModel):
    """Update order status request"""
    orderId: str
    status: OrderStatus
    estimatedMinutes: Optional[int] = None
