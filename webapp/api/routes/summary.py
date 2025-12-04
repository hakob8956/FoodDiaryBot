"""Summary API endpoints."""
import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from database.repositories.user_repo import user_repo
from services.summary_generator import summary_generator
from .auth import TelegramUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class Totals(BaseModel):
    """Total nutrition values."""
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    meals_logged: int


class Averages(BaseModel):
    """Average daily values."""
    daily_calories: int
    daily_protein_g: float
    daily_carbs_g: float
    daily_fat_g: float


class TargetComparison(BaseModel):
    """Comparison to daily target."""
    daily_target: Optional[int]
    avg_vs_target: int
    adherence_percentage: float


class Insights(BaseModel):
    """AI-generated insights."""
    positive_notes: list[str]
    improvements: list[str]
    advice: list[str]


class UserProfile(BaseModel):
    """User profile summary."""
    telegram_id: int
    first_name: Optional[str]
    weight: Optional[float]
    height: Optional[float]
    age: Optional[int]
    goal: Optional[str]
    daily_calorie_target: Optional[int]
    protein_target: Optional[int]
    carbs_target: Optional[int]
    fat_target: Optional[int]
    macro_override: bool
    notifications_enabled: bool
    reminder_hour: int


class SummaryResponse(BaseModel):
    """Complete summary response."""
    period: dict
    totals: Totals
    averages: Averages
    target_comparison: TargetComparison
    common_foods: list[str]
    insights: Insights


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    days: int = Query(default=7, ge=1, le=90),
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get nutrition summary with insights.

    Args:
        days: Number of days to include (1-90)
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Use existing summary generator
    summary = await summary_generator.generate_summary(
        telegram_id=user.id,
        start_date=start_date,
        end_date=end_date
    )

    return SummaryResponse(
        period={
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        totals=Totals(
            calories=summary.get("totals", {}).get("calories", 0),
            protein_g=summary.get("totals", {}).get("protein_g", 0.0),
            carbs_g=summary.get("totals", {}).get("carbs_g", 0.0),
            fat_g=summary.get("totals", {}).get("fat_g", 0.0),
            meals_logged=summary.get("totals", {}).get("meals_logged", 0)
        ),
        averages=Averages(
            daily_calories=summary.get("averages", {}).get("daily_calories", 0),
            daily_protein_g=summary.get("averages", {}).get("daily_protein_g", 0.0),
            daily_carbs_g=summary.get("averages", {}).get("daily_carbs_g", 0.0),
            daily_fat_g=summary.get("averages", {}).get("daily_fat_g", 0.0)
        ),
        target_comparison=TargetComparison(
            daily_target=summary.get("target_comparison", {}).get("daily_target"),
            avg_vs_target=summary.get("target_comparison", {}).get("avg_vs_target", 0),
            adherence_percentage=summary.get("target_comparison", {}).get("adherence_percentage", 0.0)
        ),
        common_foods=summary.get("common_foods", []),
        insights=Insights(
            positive_notes=summary.get("insights", {}).get("positive_notes", []),
            improvements=summary.get("insights", {}).get("improvements", []),
            advice=summary.get("insights", {}).get("advice", [])
        )
    )


@router.get("/user/profile", response_model=UserProfile)
async def get_user_profile(
    user: TelegramUser = Depends(get_current_user)
):
    """Get current user's profile."""
    profile = await user_repo.get_user(user.id)

    if not profile:
        return UserProfile(
            telegram_id=user.id,
            first_name=user.first_name,
            weight=None,
            height=None,
            age=None,
            goal=None,
            daily_calorie_target=None,
            protein_target=None,
            carbs_target=None,
            fat_target=None,
            macro_override=False,
            notifications_enabled=True,
            reminder_hour=20
        )

    return UserProfile(
        telegram_id=profile.telegram_id,
        first_name=profile.first_name,
        weight=profile.weight,
        height=profile.height,
        age=profile.age,
        goal=profile.goal.value if profile.goal else None,
        daily_calorie_target=profile.daily_calorie_target,
        protein_target=profile.protein_target,
        carbs_target=profile.carbs_target,
        fat_target=profile.fat_target,
        macro_override=profile.macro_override,
        notifications_enabled=profile.notifications_enabled,
        reminder_hour=profile.reminder_hour
    )
