"""Menu API schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MultilingualResponse(BaseModel):
    """Multilingual text response"""

    en: str
    es: Optional[str] = ""
    pt: Optional[str] = ""


class ModifierOptionResponse(BaseModel):
    """Modifier option response"""

    id: str
    name: MultilingualResponse
    priceCents: int = 0


class ModifierResponse(BaseModel):
    """Modifier response"""

    id: str
    name: MultilingualResponse
    type: Optional[str] = None
    required: bool = False
    selectionMode: Optional[str] = None
    maxChoices: Optional[int] = None
    freeChoices: Optional[int] = None
    extraChoicePriceCents: Optional[int] = None
    options: List[ModifierOptionResponse] = []


class VariantResponse(BaseModel):
    """Variant response"""

    id: str
    name: str  # Changed from MultilingualResponse to str per frontend schema
    priceCents: int
    default: bool = False


class MenuItemResponse(BaseModel):
    """Menu item response"""

    id: str
    name: MultilingualResponse
    description: MultilingualResponse
    imageUrls: Optional[List[str]] = []
    categoryId: str
    priceCents: int
    makingCostCents: Optional[int] = 0
    isAvailable: bool = True
    stationTags: List[str] = []
    variants: List[VariantResponse] = []
    modifiers: List[ModifierResponse] = []


class CategoryResponse(BaseModel):
    """Category response"""

    id: str
    name: MultilingualResponse
    description: Optional[MultilingualResponse] = None
    sortOrder: int
    emoji: Optional[str] = None


class MenuResponse(BaseModel):
    """Menu response"""

    id: str = Field(..., alias="_id")
    restaurantId: str
    locationId: str
    menuSlug: str
    name: MultilingualResponse
    categories: List[CategoryResponse]
    items: List[MenuItemResponse]
    salesTax: float

    model_config = {"populate_by_name": True}


class MenuSummaryResponse(BaseModel):
    """Menu summary response (for list view)"""

    id: str = Field(..., alias="_id")
    menuSlug: str
    name: MultilingualResponse
    description: Optional[MultilingualResponse] = None
    available: bool = True

    model_config = {"populate_by_name": True}
