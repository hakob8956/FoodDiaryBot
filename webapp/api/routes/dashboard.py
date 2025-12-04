"""Dashboard API endpoints."""
import json
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database.repositories.food_log_repo import food_log_repo
from database.repositories.user_repo import user_repo
from services.calorie_calculator import get_macro_targets
from constants import Goal
from .auth import TelegramUser, get_current_user

router = APIRouter()


class MacroProgress(BaseModel):
    """Macro nutrient progress."""
    current: float
    target: int
    label: str


class MealItem(BaseModel):
    """A single meal entry."""
    id: int
    time: str
    foods: List[str]
    calories: int
    protein: float
    carbs: float
    fat: float


class TodayResponse(BaseModel):
    """Response for today's dashboard data."""
    calories_eaten: int
    calories_target: int
    calories_remaining: int
    protein: MacroProgress
    carbs: MacroProgress
    fat: MacroProgress
    meal_count: int
    meals: List[MealItem]


@router.get("/dashboard/today", response_model=TodayResponse)
async def get_today_dashboard(
    user: TelegramUser = Depends(get_current_user)
):
    """
    Get today's dashboard data including calories and macro progress.
    """
    # Get user profile
    user_profile = await user_repo.get_user(user.id)
    daily_target = user_profile.daily_calorie_target if user_profile else 2000

    # Get macro targets - use custom if override is set, otherwise calculate from goal
    if user_profile and user_profile.macro_override and all([
        user_profile.protein_target,
        user_profile.carbs_target,
        user_profile.fat_target
    ]):
        # Use custom macro targets
        protein_target = user_profile.protein_target
        carbs_target = user_profile.carbs_target
        fat_target = user_profile.fat_target
    else:
        # Calculate from goal
        goal = Goal.MAINTAIN  # Default
        if user_profile and user_profile.goal:
            try:
                goal = Goal(user_profile.goal)
            except ValueError:
                pass

        macro_targets = get_macro_targets(daily_target, goal)
        protein_target = macro_targets.protein_g
        carbs_target = macro_targets.carbs_g
        fat_target = macro_targets.fat_g

    # Get today's totals and logs
    today = date.today()
    totals = await food_log_repo.get_daily_totals(user.id, today)
    logs = await food_log_repo.get_logs_by_date(user.id, today)

    calories_eaten = totals.calories
    remaining = daily_target - calories_eaten

    # Build meal list
    meals = []
    for log in logs:
        # Parse the analysis JSON to get food names
        foods = []
        try:
            analysis = json.loads(log.analysis_json) if log.analysis_json else {}
            items = analysis.get("items", [])
            foods = [item.get("name", "Unknown food") for item in items]
        except (json.JSONDecodeError, TypeError):
            foods = ["Unknown food"]

        meals.append(MealItem(
            id=log.id,
            time=log.logged_at.strftime("%H:%M") if log.logged_at else "",
            foods=foods,
            calories=log.total_calories,
            protein=round(log.total_protein, 1),
            carbs=round(log.total_carbs, 1),
            fat=round(log.total_fat, 1)
        ))

    return TodayResponse(
        calories_eaten=calories_eaten,
        calories_target=daily_target,
        calories_remaining=max(0, remaining),
        protein=MacroProgress(
            current=round(totals.protein, 1),
            target=protein_target,
            label="Protein"
        ),
        carbs=MacroProgress(
            current=round(totals.carbs, 1),
            target=carbs_target,
            label="Carbs"
        ),
        fat=MacroProgress(
            current=round(totals.fat, 1),
            target=fat_target,
            label="Fat"
        ),
        meal_count=totals.meal_count,
        meals=meals
    )
