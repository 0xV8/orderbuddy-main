"""Menu domain model"""

from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}


class Multilingual(BaseModel):
    """Multilingual text support"""

    en: str
    es: str = ""
    pt: str = ""


class ModifierOption(BaseModel):
    """Modifier option model"""

    id: str
    name: Multilingual
    priceCents: int


class Modifier(BaseModel):
    """Modifier model"""

    id: str
    name: Multilingual
    type: str  # 'standard' | 'upsell'
    required: bool
    selectionMode: str  # 'single' | 'max' | 'multiple'
    maxChoices: int
    freeChoices: int
    extraChoicePriceCents: int
    options: List[ModifierOption] = []


class Variant(BaseModel):
    """Menu item variant"""

    id: str
    name: str
    priceCents: int
    default: bool = False


class MenuItem(BaseModel):
    """Menu item model"""

    id: str
    name: Multilingual
    description: Multilingual
    imageUrls: Optional[List[str]] = []
    categoryId: str
    priceCents: int
    makingCostCents: int
    isAvailable: bool = True
    stationTags: List[str] = []
    variants: List[Variant] = []
    modifiers: List[Modifier] = []


class Category(BaseModel):
    """Menu category model"""

    id: str
    name: Multilingual
    description: Multilingual
    sortOrder: int
    emoji: Optional[str] = None


class Menu(BaseModel):
    """Menu domain model"""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    restaurantId: str
    locationId: str
    menuSlug: str
    name: Multilingual
    categories: List[Category]
    items: List[MenuItem]
    salesTax: float

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
