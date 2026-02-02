"""Standard API response wrappers"""

from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""

    data: Optional[T] = None
    message: Optional[str] = None
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""

    statusCode: int
    message: str
    detail: Optional[str] = None
