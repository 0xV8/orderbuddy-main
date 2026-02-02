"""Mock authentication endpoints for development (mimics Supertokens API)"""

from fastapi import APIRouter, Response, Request, Cookie
from pydantic import BaseModel
from typing import Optional
from loguru import logger
import uuid
import time
import json
import base64
from app.core.database import db

router = APIRouter()

# MongoDB collections for persistent storage
def get_auth_codes_collection():
    return db.db.auth_codes

def get_sessions_collection():
    return db.db.sessions


class CreateCodeRequest(BaseModel):
    """Request to create a passwordless login code"""
    phoneNumber: str


class ConsumeCodeRequest(BaseModel):
    """Request to consume/verify a passwordless login code"""
    deviceId: str
    preAuthSessionId: str
    userInputCode: Optional[str] = None
    linkCode: Optional[str] = None


class RefreshSessionRequest(BaseModel):
    """Request to refresh an authentication session"""
    refresh_token: Optional[str] = None


@router.post("/signinup/code")
async def create_passwordless_code(request: CreateCodeRequest):
    """
    Create a passwordless login code (mock for development).

    In production, this would send an SMS with the code.
    For development, we log the code to the console.
    """
    logger.info(f"POST /login/signinup/code - phone={request.phoneNumber}")

    # Generate a simple 6-digit code
    code = str(uuid.uuid4().int)[:6]
    pre_auth_session_id = str(uuid.uuid4())

    # Store the code in MongoDB (persists across server reloads)
    auth_codes_col = get_auth_codes_collection()
    await auth_codes_col.update_one(
        {"phoneNumber": request.phoneNumber},
        {
            "$set": {
                "code": code,
                "preAuthSessionId": pre_auth_session_id,
                "createdAt": time.time()
            }
        },
        upsert=True
    )

    logger.info(f"=== LOGIN CODE FOR {request.phoneNumber} ===")
    logger.info(f"Code: {code}")
    logger.info(f"PreAuthSessionId: {pre_auth_session_id}")
    logger.info(f"=====================================")

    # Also write to file for easy retrieval
    with open("/tmp/otp_latest.json", "w") as f:
        json.dump({
            "code": code,
            "phoneNumber": request.phoneNumber,
            "preAuthSessionId": pre_auth_session_id,
            "timestamp": time.time()
        }, f)

    return {
        "status": "OK",
        "deviceId": str(uuid.uuid4()),
        "preAuthSessionId": pre_auth_session_id,
        "flowType": "USER_INPUT_CODE"
    }


@router.post("/signinup/code/consume")
async def consume_passwordless_code(request: ConsumeCodeRequest, response: Response):
    """
    Consume/verify a passwordless login code (mock for development).

    Creates a session if the code is valid.
    """
    logger.info(f"POST /login/signinup/code/consume - preAuthSessionId={request.preAuthSessionId}")

    # Find the code by preAuthSessionId in MongoDB
    auth_codes_col = get_auth_codes_collection()
    stored_data = await auth_codes_col.find_one({"preAuthSessionId": request.preAuthSessionId})

    if not stored_data:
        logger.warning(f"No matching preAuthSessionId found for {request.preAuthSessionId}")
        return {
            "status": "RESTART_FLOW_ERROR"
        }

    logger.info(f"Found auth code for phone: {stored_data['phoneNumber']}")

    # Verify the code
    if request.userInputCode != stored_data["code"]:
        logger.warning(f"Incorrect code. Expected: {stored_data['code']}, Got: {request.userInputCode}")
        return {
            "status": "INCORRECT_USER_INPUT_CODE_ERROR",
            "failedCodeInputAttemptCount": 1,
            "maximumCodeInputAttempts": 5
        }

    # Create session
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # Store session in MongoDB
    sessions_col = get_sessions_collection()
    await sessions_col.update_one(
        {"sessionId": session_id},
        {
            "$set": {
                "userId": user_id,
                "phoneNumber": stored_data["phoneNumber"],
                "createdAt": time.time()
            }
        },
        upsert=True
    )

    # Remove the used code from MongoDB
    await auth_codes_col.delete_one({"preAuthSessionId": request.preAuthSessionId})

    # Create tokens
    access_token = f"access_{session_id}"
    refresh_token = f"refresh_{session_id}"

    # Create a proper front-token in Supertokens format (JSON structure)
    expiry_time = int(time.time() * 1000) + 3600000  # 1 hour from now
    front_token_data = {
        "uid": user_id,
        "ate": expiry_time,
        "up": {}
    }
    # Use compact JSON (no spaces) for SuperTokens compatibility
    front_token = base64.b64encode(json.dumps(front_token_data, separators=(',', ':')).encode()).decode()

    # Set session cookies (mimicking Supertokens)
    response.set_cookie(
        key="sAccessToken",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 hour
    )

    response.set_cookie(
        key="sRefreshToken",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400 * 30  # 30 days
    )

    # Also set front-token as cookie for Supertokens SDK
    # Must manually set to avoid quotes that break atob()
    response.headers.append(
        "Set-Cookie",
        f"sFrontToken={front_token}; Max-Age=3600; Path=/; SameSite=lax"
    )

    # Also set as headers for frontend JS access
    response.headers["st-access-token"] = access_token
    response.headers["st-refresh-token"] = refresh_token
    response.headers["front-token"] = front_token

    logger.info(f"Session created for {stored_data['phoneNumber']} - sessionId={session_id}")

    return {
        "status": "OK",
        "createdNewUser": True,
        "user": {
            "id": user_id,
            "phoneNumber": stored_data["phoneNumber"],
            "timeJoined": int(time.time() * 1000)
        },
        "session": {
            "handle": session_id,
            "userId": user_id,
            "userDataInJWT": {}
        }
    }


@router.post("/session/refresh")
async def refresh_session(
    response: Response,
    sRefreshToken: Optional[str] = Cookie(None)
):
    """
    Refresh an authentication session (mock for development).
    """
    logger.info(f"POST /login/session/refresh")

    if not sRefreshToken:
        return {
            "status": "UNAUTHORISED"
        }

    # Extract session_id from refresh token
    if sRefreshToken.startswith("refresh_"):
        session_id = sRefreshToken.replace("refresh_", "")

        # Find session in MongoDB
        sessions_col = get_sessions_collection()
        session_data = await sessions_col.find_one({"sessionId": session_id})

        if session_data:
            # Refresh the session
            access_token = f"access_{session_id}"
            refresh_token = f"refresh_{session_id}"

            response.set_cookie(
                key="sAccessToken",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=3600
            )

            # Create proper front-token for refresh in Supertokens format (JSON structure)
            expiry_time = int(time.time() * 1000) + 3600000  # 1 hour from now
            front_token_data = {
                "uid": session_data['userId'],
                "ate": expiry_time,
                "up": {}
            }
            # Use compact JSON (no spaces) for SuperTokens compatibility
            front_token = base64.b64encode(json.dumps(front_token_data, separators=(',', ':')).encode()).decode()

            response.headers["st-access-token"] = access_token
            response.headers["front-token"] = front_token

            logger.info(f"Session refreshed - sessionId={session_id}")

            return {
                "status": "OK"
            }

    return {
        "status": "UNAUTHORISED"
    }


@router.post("/signout")
async def signout(
    response: Response,
    sAccessToken: Optional[str] = Cookie(None)
):
    """
    Sign out and destroy session (mock for development).
    """
    logger.info(f"POST /login/signout")

    if sAccessToken and sAccessToken.startswith("access_"):
        session_id = sAccessToken.replace("access_", "")
        # Delete session from MongoDB
        sessions_col = get_sessions_collection()
        result = await sessions_col.delete_one({"sessionId": session_id})
        if result.deleted_count > 0:
            logger.info(f"Session destroyed - sessionId={session_id}")

    # Clear cookies
    response.delete_cookie("sAccessToken")
    response.delete_cookie("sRefreshToken")

    return {
        "status": "OK"
    }


@router.get("/session/verify")
async def verify_session(sAccessToken: Optional[str] = Cookie(None)):
    """
    Verify if a session is valid (mock for development).
    """
    logger.info(f"GET /login/session/verify")

    if not sAccessToken or not sAccessToken.startswith("access_"):
        return {
            "status": "UNAUTHORISED"
        }

    session_id = sAccessToken.replace("access_", "")

    if session_id in sessions:
        session_data = sessions[session_id]
        return {
            "status": "OK",
            "session": {
                "handle": session_id,
                "userId": session_data["userId"],
                "userDataInJWT": {}
            }
        }

    return {
        "status": "UNAUTHORISED"
    }
