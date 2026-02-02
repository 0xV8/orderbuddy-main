"""Restaurant and Location API schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MultilingualText(BaseModel):
    """Multilingual text"""
    en: str
    es: Optional[str] = ""
    pt: Optional[str] = ""


class RestaurantOriginResponse(BaseModel):
    """Restaurant origin response (for QR code entry)"""
    id: str = Field(..., alias="_id")
    label: str  # Changed from 'name' to 'label' per frontend schema
    restaurantId: str
    locationId: str
    type: Optional[str] = None

    model_config = {"populate_by_name": True}


class LocationResponse(BaseModel):
    """Location details response - matches NestJS return format"""
    id: str = Field(..., alias="_id")
    locationSlug: str
    name: str
    isActive: bool
    acceptPayment: bool
    emergepayWalletsPublicId: Optional[str] = None
    isOpen: bool

    model_config = {"populate_by_name": True}


class RestaurantResponse(BaseModel):
    """Restaurant details response - matches NestJS projection"""
    id: str = Field(..., alias="_id")
    name: str
    concept: str
    logo: Optional[str] = None

    model_config = {"populate_by_name": True}
