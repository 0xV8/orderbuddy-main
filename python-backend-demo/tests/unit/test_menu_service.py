"""Unit tests for MenuService"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.menu_service import MenuService
from app.core.exceptions import NotFoundException


@pytest.fixture
def mock_repository():
    """Mock menu repository"""
    return MagicMock()


@pytest.fixture
def menu_service(mock_repository):
    """Menu service with mocked repository"""
    return MenuService(mock_repository)


@pytest.mark.asyncio
async def test_get_menu_success(menu_service, mock_repository):
    """Test successful menu retrieval with data transformation"""
    # Arrange
    test_menu = {
        "_id": "60d5ec49f5b5c200123abc12",
        "restaurantId": "rest1",
        "locationId": "loc1",
        "menuSlug": "lunch",
        "name": {"en": "Lunch Menu", "es": "", "pt": ""},
        "categories": [],
        "items": [],
        "salesTax": 0.08
    }
    mock_repository.find_by_id = AsyncMock(return_value=test_menu)

    # Act
    result = await menu_service.get_menu("rest1", "loc1", "60d5ec49f5b5c200123abc12")

    # Assert - Check transformed data matches expected structure
    assert result["_id"] == "60d5ec49f5b5c200123abc12"
    assert result["restaurantId"] == "rest1"
    assert result["name"]["en"] == "Lunch Menu"
    mock_repository.find_by_id.assert_called_once_with("rest1", "loc1", "60d5ec49f5b5c200123abc12")


@pytest.mark.asyncio
async def test_get_menu_not_found(menu_service, mock_repository):
    """Test menu not found scenario"""
    # Arrange
    mock_repository.find_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await menu_service.get_menu("rest1", "loc1", "invalid_id")

    assert exc_info.value.status_code == 404
    assert "Menu not found" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_get_menus_by_location_success(menu_service, mock_repository):
    """Test successful retrieval of multiple menus with transformation"""
    # Arrange
    test_menus = [
        {"_id": "menu1", "menuSlug": "breakfast", "name": "Breakfast", "description": None},
        {"_id": "menu2", "menuSlug": "lunch", "name": "Lunch", "description": None}
    ]
    mock_repository.find_menus_by_location = AsyncMock(return_value=test_menus)

    # Act
    result = await menu_service.get_menus_by_location("rest1", "loc1")

    # Assert - Check transformed data
    assert len(result) == 2
    assert result[0]["_id"] == "menu1"
    assert result[0]["menuSlug"] == "breakfast"
    assert result[0]["name"]["en"] == "Breakfast"  # Transformed to multilingual
    assert result[1]["_id"] == "menu2"
    mock_repository.find_menus_by_location.assert_called_once_with("rest1", "loc1")


@pytest.mark.asyncio
async def test_get_menus_by_location_empty(menu_service, mock_repository):
    """Test retrieval when no menus exist"""
    # Arrange
    mock_repository.find_menus_by_location = AsyncMock(return_value=[])

    # Act
    result = await menu_service.get_menus_by_location("rest1", "loc1")

    # Assert
    assert result == []
    assert len(result) == 0
