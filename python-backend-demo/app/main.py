"""FastAPI application entry point"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import socketio

from app.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.logging import setup_logging
from app.core.exceptions import AppException
from app.core.socketio import socket_app, sio
from app.api.v1.api import api_router


# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="REST API for OrderBuddy mobile and web clients",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["front-token", "st-access-token", "st-refresh-token"],  # Headers for auth
)


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(f"AppException: {exc.message} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"statusCode": exc.status_code, "message": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "statusCode": 500,
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# Include authentication router at /login (before API router for correct precedence)
from app.api.v1.endpoints import auth
app.include_router(auth.router, prefix="/login", tags=["Authentication"])

# Include restaurant management router at /restaurant (for manage app compatibility)
from app.api.v1.endpoints import restaurant
app.include_router(restaurant.router, prefix="/restaurant", tags=["Restaurant Management"])

# Include new routers at root level for manage app compatibility
from app.api.v1.endpoints import origins, stations, printers, campaign, report, users
app.include_router(origins.router, prefix="/origins", tags=["Origins"])
app.include_router(stations.router, prefix="/stations", tags=["Stations"])
app.include_router(printers.router, prefix="/printers", tags=["Printers"])
app.include_router(campaign.router, prefix="/campaign", tags=["Campaigns"])
app.include_router(report.router, prefix="/report", tags=["Reports"])
app.include_router(users.router, prefix="/users", tags=["Users"])

# Include API router (legacy v1 path)
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Socket.IO status endpoint
@app.get("/socket-status", tags=["Socket.IO"])
async def socket_status():
    """Socket.IO server status"""
    return {
        "status": "active",
        "endpoint": "/socket.io",
        "transport": "websocket, polling"
    }


# Wrap the FastAPI app with Socket.IO
app = socketio.ASGIApp(sio, other_asgi_app=app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
