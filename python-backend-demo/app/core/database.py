"""Database connection and management"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from loguru import logger


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo() -> None:
    """Connect to MongoDB"""
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.DB_CONN_STRING)
    db.db = db.client[settings.DB_NAME]

    # Test connection
    try:
        await db.client.admin.command("ping")
        logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """Close MongoDB connection"""
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection"""
    return db.db
