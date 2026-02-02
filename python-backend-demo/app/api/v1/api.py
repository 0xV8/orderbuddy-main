"""API v1 router aggregator"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    menu,
    order,
    restaurant,
    auth,
    order_app,
    payments,
    origins,
    stations,
    printers,
    campaign,
    report,
    users
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(order_app.router, prefix="/order-app", tags=["Order App - Core"])
api_router.include_router(menu.router, prefix="/order-app", tags=["Order App - Menu"])
api_router.include_router(order.router, prefix="/order-app", tags=["Order App - Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(restaurant.router, prefix="/restaurant", tags=["Restaurant Management"])
api_router.include_router(origins.router, prefix="/origins", tags=["Origins"])
api_router.include_router(stations.router, prefix="/stations", tags=["Stations"])
api_router.include_router(printers.router, prefix="/printers", tags=["Printers"])
api_router.include_router(campaign.router, prefix="/campaign", tags=["Campaigns"])
api_router.include_router(report.router, prefix="/report", tags=["Reports"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
