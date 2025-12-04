"""Profile API endpoints for updating user settings."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database.repositories.user_repo import user_repo
from services.calorie_calculator import get_macro_targets, calculate_daily_target
from constants import Goal, Sex, ActivityLevel
from .auth import TelegramUser, get_current_user

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    """Request model for updating profile settings."""
    # Profile info
    first_name: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    # Goal and calories
    goal: Optional[str] = None
    daily_calorie_target: Optional[int] = None
    # Macros
    protein_target: Optional[int] = None
    carbs_target: Optional[int] = None
    fat_target: Optional[int] = None
    # Notifications
    notifications_enabled: Optional[bool] = None
    reminder_hour: Optional[int] = None


class ProfileResponse(BaseModel):
    """Response model for profile data."""
    telegram_id: int
    first_name: Optional[str]
    weight: Optional[float]
    height: Optional[float]
    age: Optional[int]
    sex: Optional[str]
    activity_level: Optional[str]
    goal: Optional[str]
    daily_calorie_target: Optional[int]
    calorie_override: bool
    protein_target: Optional[int]
    carbs_target: Optional[int]
    fat_target: Optional[int]
    macro_override: bool
    notifications_enabled: bool
    reminder_hour: int


class ResetResponse(BaseModel):
    """Response for reset operations."""
    success: bool
    daily_calorie_target: Optional[int]
    protein_target: Optional[int]
    carbs_target: Optional[int]
    fat_target: Optional[int]


@router.put("/user/profile", response_model=ProfileResponse)
async def update_user_profile(
    request: UpdateProfileRequest,
    user: TelegramUser = Depends(get_current_user)
):
    """
    Update user profile settings.

    Allows updating goal, calorie target, and macro targets.
    Sets override flags when custom values are provided.
    """
    # Get current user
    current_user = await user_repo.get_user(user.id)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build update dict
    updates = {}

    # Handle profile info updates
    if request.first_name is not None:
        updates["first_name"] = request.first_name
    if request.weight is not None:
        if request.weight > 0:
            updates["weight"] = request.weight
    if request.height is not None:
        if request.height > 0:
            updates["height"] = request.height
    if request.age is not None:
        if 1 <= request.age <= 150:
            updates["age"] = request.age

    # Handle goal update
    if request.goal is not None:
        # Validate goal
        try:
            Goal(request.goal)
            updates["goal"] = request.goal
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid goal value")

    # Handle calorie target update
    if request.daily_calorie_target is not None:
        updates["daily_calorie_target"] = request.daily_calorie_target
        updates["calorie_override"] = 1

    # Handle macro targets update
    macro_fields = ["protein_target", "carbs_target", "fat_target"]
    macro_updates = {
        field: getattr(request, field)
        for field in macro_fields
        if getattr(request, field) is not None
    }

    if macro_updates:
        updates.update(macro_updates)
        updates["macro_override"] = 1

    # Handle notification settings
    if request.notifications_enabled is not None:
        updates["notifications_enabled"] = 1 if request.notifications_enabled else 0

    if request.reminder_hour is not None:
        # Validate hour is 0-23
        if 0 <= request.reminder_hour <= 23:
            updates["reminder_hour"] = request.reminder_hour

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Perform update
    updated_user = await user_repo.update_user(user.id, **updates)
    if not updated_user:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return ProfileResponse(
        telegram_id=updated_user.telegram_id,
        first_name=updated_user.first_name,
        weight=updated_user.weight,
        height=updated_user.height,
        age=updated_user.age,
        sex=updated_user.sex.value if updated_user.sex else None,
        activity_level=updated_user.activity_level.value if updated_user.activity_level else None,
        goal=updated_user.goal.value if updated_user.goal else None,
        daily_calorie_target=updated_user.daily_calorie_target,
        calorie_override=updated_user.calorie_override,
        protein_target=updated_user.protein_target,
        carbs_target=updated_user.carbs_target,
        fat_target=updated_user.fat_target,
        macro_override=updated_user.macro_override,
        notifications_enabled=updated_user.notifications_enabled,
        reminder_hour=updated_user.reminder_hour,
    )


@router.post("/user/profile/reset-macros", response_model=ResetResponse)
async def reset_macros_to_default(
    user: TelegramUser = Depends(get_current_user)
):
    """
    Reset macro targets to calculated defaults based on goal.

    Clears the macro_override flag and recalculates macros.
    """
    current_user = await user_repo.get_user(user.id)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate default macros from goal
    goal = current_user.goal or Goal.MAINTAIN
    daily_calories = current_user.daily_calorie_target or 2000

    macro_targets = get_macro_targets(daily_calories, goal)

    # Update user with calculated values and clear override
    updated_user = await user_repo.update_user(
        user.id,
        protein_target=macro_targets.protein_g,
        carbs_target=macro_targets.carbs_g,
        fat_target=macro_targets.fat_g,
        macro_override=0
    )

    return ResetResponse(
        success=True,
        daily_calorie_target=updated_user.daily_calorie_target if updated_user else daily_calories,
        protein_target=macro_targets.protein_g,
        carbs_target=macro_targets.carbs_g,
        fat_target=macro_targets.fat_g,
    )
