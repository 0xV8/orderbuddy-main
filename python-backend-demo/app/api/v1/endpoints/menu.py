"""Menu API endpoints"""

from fastapi import APIRouter, Depends, Path
from typing import List
from loguru import logger

from app.models.schemas.response import ApiResponse
from app.models.schemas.menu import MenuResponse, MenuSummaryResponse
from app.models.schemas.restaurant import (
    RestaurantOriginResponse,
    RestaurantResponse,
    LocationResponse,
)
from app.services.menu_service import MenuService
from app.services.restaurant_service import RestaurantService
from app.dependencies import get_menu_service, get_restaurant_service

router = APIRouter()


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/menus",
    response_model=ApiResponse[List[MenuSummaryResponse]],
    summary="Get all menus for a location",
    description="Retrieve all menus available for a specific restaurant location",
)
async def get_menus(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    service: MenuService = Depends(get_menu_service),
):
    """
    Get all menus for a location.

    This endpoint returns a list of menu summaries for the specified restaurant and location.
    Used in the Order App entry page to display available menus.

    **Parameters:**
    - **restaurant_id**: Unique identifier of the restaurant
    - **location_id**: Unique identifier of the location

    **Returns:**
    - List of menu summaries with basic information
    """
    logger.info(f"GET /menus - restaurant={restaurant_id}, location={location_id}")

    menus = await service.get_menus_by_location(restaurant_id, location_id)

    # Convert to summary response
    menu_summaries = [
        MenuSummaryResponse(
            id=menu["_id"],
            menuSlug=menu["menuSlug"],
            name=menu["name"],
            description=menu.get("description"),
            available=menu.get("available", True),
        )
        for menu in menus
    ]

    return ApiResponse(data=menu_summaries)


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}/menus/{menu_id}",
    response_model=ApiResponse[MenuResponse],
    summary="Get menu by ID",
    description="Retrieve complete menu details including categories and items",
)
async def get_menu(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    menu_id: str = Path(..., description="Menu ID"),
    service: MenuService = Depends(get_menu_service),
):
    """
    Get complete menu details.

    This endpoint returns the full menu with categories, items, modifiers, and pricing.
    Used in the Order App menu page for browsing and ordering.

    **Parameters:**
    - **restaurant_id**: Unique identifier of the restaurant
    - **location_id**: Unique identifier of the location
    - **menu_id**: Unique identifier of the menu

    **Returns:**
    - Complete menu details with categories and items

    **Example Response:**
    ```json
    {
      "data": {
        "_id": "60d5ec49f5b5c200123abc12",
        "restaurantId": "60d5ec49f5b5c200123abc10",
        "locationId": "60d5ec49f5b5c200123abc11",
        "menuSlug": "lunch-menu",
        "name": {
          "en": "Lunch Menu",
          "es": "Menú de Almuerzo",
          "pt": "Menu de Almoço"
        },
        "categories": [...],
        "items": [...],
        "salesTax": 0.08
      }
    }
    ```
    """
    logger.info(
        f"GET /menus/{menu_id} - restaurant={restaurant_id}, location={location_id}"
    )

    menu = await service.get_menu(restaurant_id, location_id, menu_id)

    return ApiResponse(data=MenuResponse(**menu))


@router.get(
    "/restaurants/origins/{origin_id}",
    response_model=ApiResponse[RestaurantOriginResponse],
    summary="Get restaurant by origin ID",
    description="Get restaurant and location information by origin ID (from QR code)",
)
async def get_restaurant_by_origin(
    origin_id: str = Path(..., description="Origin ID from QR code"),
    service: RestaurantService = Depends(get_restaurant_service),
):
    """
    Get restaurant and location by origin ID.

    This endpoint is called when a customer scans a QR code to start ordering.
    The origin ID is embedded in the QR code and maps to a specific restaurant and location.

    **Parameters:**
    - **origin_id**: Unique identifier from QR code (e.g., "table-1", "counter-a")

    **Returns:**
    - Restaurant and location mapping information
    """
    logger.info(f"GET /restaurants/origins/{origin_id}")

    origin = await service.get_by_origin(origin_id)

    return ApiResponse(data=RestaurantOriginResponse(**origin))


@router.get(
    "/restaurants/{restaurant_id}",
    response_model=ApiResponse[RestaurantResponse],
    summary="Get restaurant details",
    description="Get complete restaurant information",
)
async def get_restaurant(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    service: RestaurantService = Depends(get_restaurant_service),
):
    """
    Get restaurant details.

    This endpoint returns complete restaurant information including name, description,
    logo, and associated locations.

    **Parameters:**
    - **restaurant_id**: Unique identifier of the restaurant

    **Returns:**
    - Complete restaurant details
    """
    logger.info(f"GET /restaurants/{restaurant_id}")

    restaurant = await service.get_restaurant(restaurant_id)

    return ApiResponse(data=RestaurantResponse(**restaurant))


@router.get(
    "/restaurants/{restaurant_id}/locations/{location_id}",
    response_model=ApiResponse[LocationResponse],
    summary="Get location details",
    description="Get complete location information",
)
async def get_location(
    restaurant_id: str = Path(..., description="Restaurant ID"),
    location_id: str = Path(..., description="Location ID"),
    service: RestaurantService = Depends(get_restaurant_service),
):
    """
    Get location details.

    This endpoint returns complete location information including address,
    contact information, and operating details.

    **Parameters:**
    - **restaurant_id**: Unique identifier of the restaurant
    - **location_id**: Unique identifier of the location

    **Returns:**
    - Complete location details
    """
    logger.info(f"GET /restaurants/{restaurant_id}/locations/{location_id}")

    location = await service.get_location(restaurant_id, location_id)

    return ApiResponse(data=LocationResponse(**location))
