"""Socket.IO configuration and setup"""

import socketio
from loguru import logger
from app.config import settings

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        settings.STORE_ENDPOINT,
        settings.API_ENDPOINT,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
    ],
    logger=False,
    engineio_logger=False,
)

socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Socket.IO client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Socket.IO client disconnected: {sid}")


@sio.event
async def order_joined(sid, data):
    """
    Handle order_joined event from mobile app
    Client joins a room for the specific order to receive updates
    """
    order_id = data.get('orderId')
    if order_id:
        await sio.enter_room(sid, order_id)
        logger.info(f"Client {sid} joined order room: {order_id}")

        await sio.emit('order_joined_ack', {
            'orderId': order_id,
            'success': True
        }, room=sid)
    else:
        logger.warning(f"Client {sid} tried to join order without orderId")


@sio.event
async def store_joined(sid, data):
    """
    Handle store_joined event from dashboard/store apps
    """
    restaurant_id = data.get('restaurantId')
    location_id = data.get('locationId')

    if restaurant_id:
        await sio.enter_room(sid, restaurant_id)
        logger.info(f"Store client {sid} joined restaurant room: {restaurant_id}")

    if location_id:
        location_room = f"{restaurant_id}_{location_id}"
        await sio.enter_room(sid, location_room)
        logger.info(f"Store client {sid} joined location room: {location_room}")


async def emit_order_completed(order_id: str, restaurant_id: str, data: dict):
    """
    Broadcast order_completed event to order room and restaurant room
    """
    logger.info(f"Broadcasting order_completed for order: {order_id}")

    # Emit to order room (mobile app clients)
    await sio.emit('order_completed', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=order_id)

    # Emit to restaurant room (store/dashboard clients)
    await sio.emit('order_completed', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=restaurant_id)


async def emit_order_ready_for_pickup(order_id: str, restaurant_id: str, data: dict):
    """
    Broadcast order_ready_for_pickup event to order room and restaurant room
    """
    logger.info(f"Broadcasting order_ready_for_pickup for order: {order_id}")

    # Emit to order room (mobile app clients)
    await sio.emit('order_ready_for_pickup', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=order_id)

    # Emit to restaurant room (store/dashboard clients)
    await sio.emit('order_ready_for_pickup', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=restaurant_id)


async def emit_order_accepted(order_id: str, restaurant_id: str, data: dict):
    """
    Broadcast order_accepted event
    """
    logger.info(f"Broadcasting order_accepted for order: {order_id}")

    await sio.emit('order_accepted', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=order_id)

    await sio.emit('order_accepted', {
        'orderId': order_id,
        'restaurantId': restaurant_id,
        **data
    }, room=restaurant_id)
