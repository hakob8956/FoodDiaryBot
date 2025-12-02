"""Calendar API endpoints."""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from database.repositories.food_log_repo import food_log_repo
from database.repositories.user_repo import user_repo
from .auth import TelegramUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class DayData(BaseModel):
    """Data for a single day."""
    date: str
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    meal_count: int
    status: str  # "under", "near", "over" based on target


class CalendarResponse(BaseModel):
    """Response for calendar data."""
    year: int
    month: int
    daily_target: Optional[int]
    days: list[DayData]


class FoodItem(BaseModel):
    """Individual food item."""
    name: str
    portion: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


class MealEntry(BaseModel):
    """A meal entry for a specific day."""
    id: int
    logged_at: str
    input_type: str
    items: list[FoodItem]
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float


class DayDetailResponse(BaseModel):
    """Detailed response for a specific day."""
    date: str
    daily_target: Optional[int]
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    meals: list[MealEntry]


def get_status(calories: int, target: Optional[int]) -> str:
    """Determine status based on calories vs target."""
    if not target:
        return "neutral"
    ratio = calories / target
    if ratio <= 0.9:
        return "under"
    elif ratio <= 1.1:
        return "near"
    else:
        return "over"


@router.get("/calendar", response_model=CalendarResponse)
async def get_calendar(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get calendar data for a month.

    Returns days with food logs and their status (under/near/over target).
    """
    # Default to current month
    today = date.today()
    year = year or today.year
    month = month or today.month

    # Get user profile for target
    user_profile = await user_repo.get_user(user.id)
    daily_target = user_profile.daily_calorie_target if user_profile else None

    # Calculate date range for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    # Get logs for the month
    logs = await food_log_repo.get_logs_by_date_range(
        user.id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

    # Aggregate by day
    daily_data: dict[str, dict] = {}
    for log in logs:
        day_str = log.logged_at.strftime("%Y-%m-%d") if log.logged_at else ""
        if not day_str:
            continue

        if day_str not in daily_data:
            daily_data[day_str] = {
                "calories": 0,
                "protein": 0.0,
                "carbs": 0.0,
                "fat": 0.0,
                "count": 0
            }

        daily_data[day_str]["calories"] += log.total_calories or 0
        daily_data[day_str]["protein"] += log.total_protein or 0.0
        daily_data[day_str]["carbs"] += log.total_carbs or 0.0
        daily_data[day_str]["fat"] += log.total_fat or 0.0
        daily_data[day_str]["count"] += 1

    # Build response
    days = []
    for day_str, data in sorted(daily_data.items()):
        days.append(DayData(
            date=day_str,
            total_calories=data["calories"],
            total_protein=data["protein"],
            total_carbs=data["carbs"],
            total_fat=data["fat"],
            meal_count=data["count"],
            status=get_status(data["calories"], daily_target)
        ))

    return CalendarResponse(
        year=year,
        month=month,
        daily_target=daily_target,
        days=days
    )


@router.get("/calendar/{day}", response_model=DayDetailResponse)
async def get_day_detail(
    day: str,
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get detailed food log for a specific day.

    Args:
        day: Date in YYYY-MM-DD format
    """
    try:
        target_date = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()

    # Get user profile for target
    user_profile = await user_repo.get_user(user.id)
    daily_target = user_profile.daily_calorie_target if user_profile else None

    # Get logs for the day
    logs = await food_log_repo.get_logs_by_date(user.id, target_date)

    # Build meal entries
    meals = []
    total_calories = 0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0

    for log in logs:
        # Parse food items from analysis_json
        items = []
        try:
            analysis = json.loads(log.analysis_json)
            for item in analysis.get("items", []):
                items.append(FoodItem(
                    name=item.get("name", "Unknown"),
                    portion=item.get("portion", ""),
                    calories=item.get("calories", 0),
                    protein_g=item.get("protein_g", 0.0),
                    carbs_g=item.get("carbs_g", 0.0),
                    fat_g=item.get("fat_g", 0.0)
                ))
        except (json.JSONDecodeError, KeyError):
            pass

        meals.append(MealEntry(
            id=log.id or 0,
            logged_at=log.logged_at.isoformat() if log.logged_at else "",
            input_type=log.input_type or "text",
            items=items,
            total_calories=log.total_calories or 0,
            total_protein=log.total_protein or 0.0,
            total_carbs=log.total_carbs or 0.0,
            total_fat=log.total_fat or 0.0
        ))

        total_calories += log.total_calories or 0
        total_protein += log.total_protein or 0.0
        total_carbs += log.total_carbs or 0.0
        total_fat += log.total_fat or 0.0

    return DayDetailResponse(
        date=day,
        daily_target=daily_target,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat,
        meals=meals
    )
