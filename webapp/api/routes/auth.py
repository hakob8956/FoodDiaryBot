"""Telegram Mini App authentication."""
import hashlib
import hmac
import json
import logging
from typing import Optional
from urllib.parse import parse_qs, unquote

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TelegramUser(BaseModel):
    """Telegram user data from initData."""
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None


def validate_telegram_init_data(init_data: str) -> TelegramUser:
    """
    Validate Telegram WebApp initData and extract user info.

    Args:
        init_data: The initData string from Telegram WebApp

    Returns:
        TelegramUser with validated user data

    Raises:
        ValueError: If validation fails
    """
    if not init_data:
        raise ValueError("initData is required")

    # Parse the init data
    try:
        parsed = {}
        for item in init_data.split("&"):
            if "=" in item:
                key, value = item.split("=", 1)
                parsed[key] = unquote(value)
    except Exception as e:
        raise ValueError(f"Failed to parse initData: {e}")

    # Extract hash
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("Hash not found in initData")

    # Create data check string (sorted alphabetically)
    data_check_arr = [f"{k}={v}" for k, v in sorted(parsed.items())]
    data_check_string = "\n".join(data_check_arr)

    # Compute expected hash
    secret_key = hmac.new(
        b"WebAppData",
        settings.telegram_token.encode(),
        hashlib.sha256
    ).digest()

    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # Validate hash
    if not hmac.compare_digest(received_hash, expected_hash):
        raise ValueError("Invalid initData hash")

    # Parse user data
    user_data_str = parsed.get("user")
    if not user_data_str:
        raise ValueError("User data not found in initData")

    try:
        user_data = json.loads(user_data_str)
        return TelegramUser(**user_data)
    except Exception as e:
        raise ValueError(f"Failed to parse user data: {e}")


async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> TelegramUser:
    """
    Dependency to get the current authenticated Telegram user.

    Args:
        x_telegram_init_data: The initData from Telegram WebApp header

    Returns:
        TelegramUser with validated user data

    Raises:
        HTTPException: If authentication fails
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="X-Telegram-Init-Data header is required"
        )

    try:
        return validate_telegram_init_data(x_telegram_init_data)
    except ValueError as e:
        logger.warning(f"Auth validation failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me")
async def get_me(user: TelegramUser = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "id": user.id,
        "first_name": user.first_name,
        "username": user.username,
    }
