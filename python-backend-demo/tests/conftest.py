"""Pytest configuration and fixtures"""

import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator

from app.main import app
from app.core.database import db as database
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Test database fixture"""
    client = AsyncIOMotorClient(settings.DB_CONN_STRING)
    test_db = client[f"{settings.DB_NAME}_test"]

    # Override database
    database.db = test_db

    yield test_db

    # Cleanup: drop test database
    await client.drop_database(f"{settings.DB_NAME}_test")
    client.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def sample_menu_data():
    """Sample menu data for testing"""
    return {
        "restaurantId": "60d5ec49f5b5c200123abc10",
        "locationId": "60d5ec49f5b5c200123abc11",
        "menuSlug": "lunch-menu",
        "name": {
            "en": "Lunch Menu",
            "es": "Menú de Almuerzo",
            "pt": "Menu de Almoço"
        },
        "categories": [
            {
                "id": "cat1",
                "name": {
                    "en": "Appetizers",
                    "es": "Aperitivos",
                    "pt": "Aperitivos"
                },
                "description": {
                    "en": "Start your meal right",
                    "es": "Comienza tu comida bien",
                    "pt": "Comece sua refeição bem"
                },
                "sortOrder": 1,
                "emoji": "🍟"
            }
        ],
        "items": [
            {
                "id": "item1",
                "name": {
                    "en": "French Fries",
                    "es": "Papas Fritas",
                    "pt": "Batatas Fritas"
                },
                "description": {
                    "en": "Crispy golden fries",
                    "es": "Papas fritas doradas crujientes",
                    "pt": "Batatas fritas douradas crocantes"
                },
                "imageUrls": ["https://example.com/fries.jpg"],
                "categoryId": "cat1",
                "priceCents": 499,
                "makingCostCents": 200,
                "isAvailable": True,
                "stationTags": ["fry-station"],
                "variants": [],
                "modifiers": [
                    {
                        "id": "mod1",
                        "name": {
                            "en": "Size",
                            "es": "Tamaño",
                            "pt": "Tamanho"
                        },
                        "type": "standard",
                        "required": True,
                        "selectionMode": "single",
                        "maxChoices": 1,
                        "freeChoices": 0,
                        "extraChoicePriceCents": 0,
                        "options": [
                            {
                                "id": "opt1",
                                "name": {
                                    "en": "Small",
                                    "es": "Pequeño",
                                    "pt": "Pequeno"
                                },
                                "priceCents": 0
                            },
                            {
                                "id": "opt2",
                                "name": {
                                    "en": "Large",
                                    "es": "Grande",
                                    "pt": "Grande"
                                },
                                "priceCents": 200
                            }
                        ]
                    }
                ]
            }
        ],
        "salesTax": 0.08
    }
