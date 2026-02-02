"""Application constants"""

# MongoDB Collections
class Collections:
    RESTAURANTS = "restaurants"
    LOCATIONS = "locations"
    MENUS = "menus"
    ORIGINS = "origins"
    STATIONS = "stations"
    ORDERS = "orders"
    ORDERS_PREVIEW = "orders_preview"
    USERS = "users"
    SUBSCRIPTIONS = "subscriptions"
    CAMPAIGNS = "campaigns"


# Order Status (aligned with NestJS)
class OrderStatus:
    ORDER_CREATED = "order_created"
    ORDER_ACCEPTED = "order_accepted"
    READY_FOR_PICKUP = "ready_for_pickup"
    ORDER_DELIVERED = "order_delivered"
    ORDER_CANCELLED = "order_cancelled"
