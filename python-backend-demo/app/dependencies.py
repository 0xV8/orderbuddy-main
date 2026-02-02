"""Dependency injection"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends
from app.core.database import get_database
from app.repositories.menu_repository import MenuRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.restaurant_service import RestaurantService


def get_menu_repository() -> MenuRepository:
    """Get menu repository instance"""
    db = get_database()
    return MenuRepository(db)


def get_menu_service(
    repository: MenuRepository = Depends(get_menu_repository),
) -> MenuService:
    """Get menu service instance"""
    return MenuService(repository)


def get_order_repository() -> OrderRepository:
    """Get order repository instance"""
    db = get_database()
    return OrderRepository(db)


def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    menu_repo: MenuRepository = Depends(get_menu_repository),
) -> OrderService:
    """Get order service instance"""
    return OrderService(order_repo, menu_repo)


def get_restaurant_repository() -> RestaurantRepository:
    """Get restaurant repository instance"""
    db = get_database()
    return RestaurantRepository(db)


def get_restaurant_service(
    repository: RestaurantRepository = Depends(get_restaurant_repository),
) -> RestaurantService:
    """Get restaurant service instance"""
    return RestaurantService(repository)
