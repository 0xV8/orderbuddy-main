"""Users API endpoints"""

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from loguru import logger
from datetime import datetime

from app.core.database import db

router = APIRouter()


class CreateUserRequest(BaseModel):
    """Create user request"""
    userId: str
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None
    createdAt: int  # Timestamp in milliseconds


class DeleteUserRequest(BaseModel):
    """Delete user request"""
    userId: str


@router.post(
    "/create-user",
    summary="Create or update user",
    description="Create a new user or update existing user's contact information"
)
async def create_user(user_info: CreateUserRequest):
    """
    Create or update a user.

    - If user exists, updates contact information if new method provided
    - If user doesn't exist, creates new user
    - At least one of email or phoneNumber must be provided
    """
    logger.info(f"POST /users/create-user - userId={user_info.userId}")

    try:
        # Validate that at least one contact method is provided
        if not user_info.email and not user_info.phoneNumber:
            raise HTTPException(
                status_code=400,
                detail="Either email or phone number is required"
            )

        users_collection = db.db["users"]

        # Check if user exists
        existing_user = await users_collection.find_one({"userId": user_info.userId})

        if existing_user:
            # Update existing user's contact info if new method provided
            update_data = {
                "updatedAt": datetime.utcnow()
            }

            if user_info.email and not existing_user.get("email"):
                update_data["email"] = user_info.email

            if user_info.phoneNumber and not existing_user.get("phoneNumber"):
                update_data["phoneNumber"] = user_info.phoneNumber

            await users_collection.update_one(
                {"userId": user_info.userId},
                {"$set": update_data}
            )

            user_id = str(existing_user["_id"])
            logger.debug(f"Updated existing user: {user_id}")

            return {"userId": user_id}

        # Create new user
        user_doc = {
            "restaurants": [],
            "userId": user_info.userId,
            "email": user_info.email,
            "phoneNumber": user_info.phoneNumber,
            "createdAt": datetime.fromtimestamp(user_info.createdAt / 1000.0),  # Convert ms to seconds
            "updatedAt": datetime.utcnow()
        }

        result = await users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)

        logger.debug(f"Created new user with ID: {user_id}")

        return {"userId": user_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )


@router.post(
    "/delete-user",
    summary="Delete user",
    description="Delete a user by userId"
)
async def delete_user(body: DeleteUserRequest):
    """
    Delete a user.

    Note: This only deletes from the local database.
    SuperTokens user deletion should be handled separately.
    """
    logger.info(f"POST /users/delete-user - userId={body.userId}")

    try:
        users_collection = db.db["users"]

        # Delete from database
        result = await users_collection.delete_one({"userId": body.userId})

        if result.deleted_count == 0:
            logger.warning(f"User not found for deletion: {body.userId}")

        logger.debug(f"Deleted user: {body.userId}")

        return "User deleted"

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user"
        )
