"""Charts API endpoints."""
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


class CalorieDataPoint(BaseModel):
    """Data point for calorie chart."""
    date: str
    calories: int
    target: Optional[int]


class CaloriesChartResponse(BaseModel):
    """Response for calories chart."""
    daily_target: Optional[int]
    data: list[CalorieDataPoint]
    average: int
    total: int


class MacroDataPoint(BaseModel):
    """Data point for macro chart."""
    date: str
    protein: float
    carbs: float
    fat: float


class MacrosChartResponse(BaseModel):
    """Response for macros chart."""
    data: list[MacroDataPoint]
    averages: dict
    totals: dict


class TrendDataPoint(BaseModel):
    """Data point for trend chart with moving average."""
    date: str
    calories: int
    moving_avg: Optional[float]


class TrendChartResponse(BaseModel):
    """Response for trend chart."""
    daily_target: Optional[int]
    data: list[TrendDataPoint]


@router.get("/charts/calories", response_model=CaloriesChartResponse)
async def get_calories_chart(
    days: int = Query(default=7, ge=1, le=90),
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get calorie data for chart.

    Args:
        days: Number of days to include (1-90)
    """
    # Get user profile for target
    user_profile = await user_repo.get_user(user.id)
    daily_target = user_profile.daily_calorie_target if user_profile else None

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Get logs for the range
    logs = await food_log_repo.get_logs_by_date_range(
        user.id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

    # Aggregate by day
    daily_calories: dict[str, int] = {}
    for log in logs:
        if not log.logged_at:
            continue
        day_str = log.logged_at.strftime("%Y-%m-%d")
        daily_calories[day_str] = daily_calories.get(day_str, 0) + (log.total_calories or 0)

    # Build data points for all days in range (including zeros)
    data = []
    total = 0
    days_with_data = 0

    current = start_date
    while current <= end_date:
        day_str = current.strftime("%Y-%m-%d")
        calories = daily_calories.get(day_str, 0)

        data.append(CalorieDataPoint(
            date=day_str,
            calories=calories,
            target=daily_target
        ))

        if calories > 0:
            total += calories
            days_with_data += 1

        current += timedelta(days=1)

    average = total // days_with_data if days_with_data > 0 else 0

    return CaloriesChartResponse(
        daily_target=daily_target,
        data=data,
        average=average,
        total=total
    )


@router.get("/charts/macros", response_model=MacrosChartResponse)
async def get_macros_chart(
    days: int = Query(default=7, ge=1, le=90),
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get macro data for chart.

    Args:
        days: Number of days to include (1-90)
    """
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Get logs for the range
    logs = await food_log_repo.get_logs_by_date_range(
        user.id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

    # Aggregate by day
    daily_macros: dict[str, dict] = {}
    for log in logs:
        if not log.logged_at:
            continue
        day_str = log.logged_at.strftime("%Y-%m-%d")

        if day_str not in daily_macros:
            daily_macros[day_str] = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}

        daily_macros[day_str]["protein"] += log.total_protein or 0.0
        daily_macros[day_str]["carbs"] += log.total_carbs or 0.0
        daily_macros[day_str]["fat"] += log.total_fat or 0.0

    # Build data points
    data = []
    totals = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
    days_with_data = 0

    current = start_date
    while current <= end_date:
        day_str = current.strftime("%Y-%m-%d")
        macros = daily_macros.get(day_str, {"protein": 0.0, "carbs": 0.0, "fat": 0.0})

        data.append(MacroDataPoint(
            date=day_str,
            protein=round(macros["protein"], 1),
            carbs=round(macros["carbs"], 1),
            fat=round(macros["fat"], 1)
        ))

        if any(v > 0 for v in macros.values()):
            for key in totals:
                totals[key] += macros[key]
            days_with_data += 1

        current += timedelta(days=1)

    averages = {
        key: round(val / days_with_data, 1) if days_with_data > 0 else 0.0
        for key, val in totals.items()
    }
    totals = {key: round(val, 1) for key, val in totals.items()}

    return MacrosChartResponse(
        data=data,
        averages=averages,
        totals=totals
    )


@router.get("/charts/trend", response_model=TrendChartResponse)
async def get_trend_chart(
    days: int = Query(default=30, ge=7, le=90),
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get calorie trend data with 7-day moving average.

    Args:
        days: Number of days to include (7-90)
    """
    # Get user profile for target
    user_profile = await user_repo.get_user(user.id)
    daily_target = user_profile.daily_calorie_target if user_profile else None

    # Calculate date range (add 6 extra days for moving average calculation)
    end_date = date.today()
    start_date = end_date - timedelta(days=days + 5)

    # Get logs for the range
    logs = await food_log_repo.get_logs_by_date_range(
        user.id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time())
    )

    # Aggregate by day
    daily_calories: dict[str, int] = {}
    for log in logs:
        if not log.logged_at:
            continue
        day_str = log.logged_at.strftime("%Y-%m-%d")
        daily_calories[day_str] = daily_calories.get(day_str, 0) + (log.total_calories or 0)

    # Build all daily values
    all_values = []
    current = start_date
    while current <= end_date:
        day_str = current.strftime("%Y-%m-%d")
        all_values.append({
            "date": day_str,
            "calories": daily_calories.get(day_str, 0)
        })
        current += timedelta(days=1)

    # Calculate moving average and build response (only for requested days)
    data = []
    for i in range(6, len(all_values)):
        # 7-day moving average
        window = [all_values[j]["calories"] for j in range(i - 6, i + 1)]
        non_zero = [v for v in window if v > 0]
        moving_avg = sum(non_zero) / len(non_zero) if non_zero else None

        data.append(TrendDataPoint(
            date=all_values[i]["date"],
            calories=all_values[i]["calories"],
            moving_avg=round(moving_avg, 1) if moving_avg else None
        ))

    return TrendChartResponse(
        daily_target=daily_target,
        data=data
    )
