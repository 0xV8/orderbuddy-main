"""Integration tests for Menu API endpoints"""

import pytest
from httpx import AsyncClient
from bson import ObjectId

from app.core.constants import Collections


@pytest.mark.asyncio
async def test_get_menu_success(client: AsyncClient, test_db, sample_menu_data):
    """Test successful menu retrieval via API"""
    # Arrange: Insert test menu into database
    result = await test_db[Collections.MENUS].insert_one(sample_menu_data)
    menu_id = str(result.inserted_id)

    # Act: Call API endpoint
    response = await client.get(
        f"/api/v1/order-app/restaurants/{sample_menu_data['restaurantId']}/locations/{sample_menu_data['locationId']}/menus/{menu_id}"
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["_id"] == menu_id
    assert data["data"]["menuSlug"] == "lunch-menu"
    assert data["data"]["salesTax"] == 0.08
    assert len(data["data"]["categories"]) == 1
    assert len(data["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_get_menu_not_found(client: AsyncClient, test_db):
    """Test menu not found error"""
    # Act: Call API with non-existent menu ID
    fake_id = str(ObjectId())
    response = await client.get(
        f"/api/v1/order-app/restaurants/rest1/locations/loc1/menus/{fake_id}"
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert data["statusCode"] == 404
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_menus_by_location_success(client: AsyncClient, test_db, sample_menu_data):
    """Test successful retrieval of menus for a location"""
    # Arrange: Insert multiple menus
    menu1 = sample_menu_data.copy()
    menu1["menuSlug"] = "breakfast"
    menu1["name"]["en"] = "Breakfast Menu"

    menu2 = sample_menu_data.copy()
    menu2["menuSlug"] = "lunch"
    menu2["name"]["en"] = "Lunch Menu"

    await test_db[Collections.MENUS].insert_many([menu1, menu2])

    # Act: Call API endpoint
    response = await client.get(
        f"/api/v1/order-app/restaurants/{sample_menu_data['restaurantId']}/locations/{sample_menu_data['locationId']}/menus"
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2

    # Verify menu summaries
    menu_slugs = [menu["menuSlug"] for menu in data["data"]]
    assert "breakfast" in menu_slugs
    assert "lunch" in menu_slugs


@pytest.mark.asyncio
async def test_get_menus_empty_location(client: AsyncClient, test_db):
    """Test retrieval when location has no menus"""
    # Act: Call API for location with no menus
    response = await client.get(
        "/api/v1/order-app/restaurants/rest999/locations/loc999/menus"
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"] == []


@pytest.mark.asyncio
async def test_menu_response_structure(client: AsyncClient, test_db, sample_menu_data):
    """Test that response has correct structure"""
    # Arrange
    result = await test_db[Collections.MENUS].insert_one(sample_menu_data)
    menu_id = str(result.inserted_id)

    # Act
    response = await client.get(
        f"/api/v1/order-app/restaurants/{sample_menu_data['restaurantId']}/locations/{sample_menu_data['locationId']}/menus/{menu_id}"
    )

    # Assert structure
    assert response.status_code == 200
    data = response.json()["data"]

    # Verify required fields
    assert "_id" in data
    assert "restaurantId" in data
    assert "locationId" in data
    assert "menuSlug" in data
    assert "name" in data
    assert "categories" in data
    assert "items" in data
    assert "salesTax" in data

    # Verify multilingual structure
    assert "en" in data["name"]
    assert "es" in data["name"]
    assert "pt" in data["name"]

    # Verify category structure
    category = data["categories"][0]
    assert "id" in category
    assert "name" in category
    assert "sortOrder" in category

    # Verify item structure
    item = data["items"][0]
    assert "id" in item
    assert "name" in item
    assert "description" in item
    assert "priceCents" in item
    assert "categoryId" in item
    assert "modifiers" in item

    # Verify modifier structure
    modifier = item["modifiers"][0]
    assert "id" in modifier
    assert "name" in modifier
    assert "type" in modifier
    assert "required" in modifier
    assert "options" in modifier


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
