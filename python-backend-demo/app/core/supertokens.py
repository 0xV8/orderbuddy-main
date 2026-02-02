"""Supertokens configuration for authentication"""

from supertokens_python import init, InputAppInfo, SupertokensConfig
from supertokens_python.recipe import passwordless, session
from supertokens_python.recipe.passwordless import ContactPhoneOnlyConfig
from supertokens_python.ingredients.smsdelivery.types import SMSDeliveryConfig, SMSDeliveryInterface
from typing import Dict, Any
from loguru import logger


# Custom SMS delivery service (for development - just logs the code)
class CustomSMSDeliveryService(SMSDeliveryInterface):
    async def send_sms(
        self,
        template_vars: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> None:
        """Send SMS with login code (for development, just log it)"""
        phone_number = template_vars.get("phoneNumber", "Unknown")
        code_lifetime = template_vars.get("codeLifetime", 0)
        url_with_link_code = template_vars.get("urlWithLinkCode", "")
        user_input_code = template_vars.get("userInputCode", "")

        logger.info(f"=== SMS LOGIN CODE ===")
        logger.info(f"Phone: {phone_number}")
        logger.info(f"Code: {user_input_code}")
        logger.info(f"Valid for: {code_lifetime} milliseconds")
        logger.info(f"Magic Link: {url_with_link_code}")
        logger.info(f"=====================")


def init_supertokens(app_name: str, api_domain: str, website_domain: str):
    """Initialize Supertokens with passwordless and session recipes"""

    init(
        app_info=InputAppInfo(
            app_name=app_name,
            api_domain=api_domain,
            website_domain=website_domain,
            api_base_path="/login",
            website_base_path="/auth",
        ),
        supertokens_config=SupertokensConfig(
            # For development, we can run without a SuperTokens core
            # In production, you should set connection_uri to your SuperTokens core
            connection_uri="",
        ),
        framework="fastapi",
        recipe_list=[
            # Passwordless authentication (phone number based)
            passwordless.init(
                flow_type="USER_INPUT_CODE",  # User enters code sent via SMS
                contact_config=ContactPhoneOnlyConfig(),
                sms_delivery=SMSDeliveryConfig(
                    service=CustomSMSDeliveryService()
                ),
            ),
            # Session management
            session.init(
                cookie_domain="localhost",  # For development
                cookie_same_site="lax",
            ),
        ],
        mode="asgi",
    )

    logger.info("Supertokens initialized successfully")
