"""Pet API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.pet_service import pet_service
from constants import ACHIEVEMENTS
from .auth import TelegramUser, get_current_user

router = APIRouter()


class AchievementResponse(BaseModel):
    """Achievement data."""
    id: str
    name: str
    description: str
    emoji: str
    unlocked: bool


class PetResponse(BaseModel):
    """Pet status response."""
    name: str
    level: str
    level_name: str
    mood: str
    mood_name: str
    image_url: str
    ascii_art: str
    total_meals: int
    current_streak: int
    best_streak: int
    calories_today: int
    calories_target: int
    calories_percent: int
    achievements: List[AchievementResponse]
    unlocked_count: int
    total_achievements: int


@router.get("/pet", response_model=PetResponse)
async def get_pet(
    user: TelegramUser = Depends(get_current_user)
):
    """Get pet status and achievements."""
    pet_info = await pet_service.get_pet_info(user.id)

    # Get all achievements with unlock status
    from database.repositories.pet_repo import pet_repo
    unlocked = await pet_repo.get_achievements(user.id)
    unlocked_ids = {a.achievement_id for a in unlocked}

    achievements = []
    for achievement_id, (name, desc, emoji) in ACHIEVEMENTS.items():
        achievements.append(AchievementResponse(
            id=achievement_id,
            name=name,
            description=desc,
            emoji=emoji,
            unlocked=achievement_id in unlocked_ids
        ))

    return PetResponse(
        name=pet_info.pet.pet_name,
        level=pet_info.level.value,
        level_name=pet_service.get_level_text(pet_info.level),
        mood=pet_info.mood.value,
        mood_name=pet_service.get_mood_text(pet_info.mood),
        image_url=pet_info.image_url,
        ascii_art=pet_info.ascii_art,
        total_meals=pet_info.pet.total_meals_logged,
        current_streak=pet_info.pet.current_streak,
        best_streak=pet_info.pet.best_streak,
        calories_today=pet_info.calories_today,
        calories_target=pet_info.calories_target,
        calories_percent=pet_info.calories_percent,
        achievements=achievements,
        unlocked_count=len(unlocked_ids),
        total_achievements=len(ACHIEVEMENTS)
    )


class RenamePetRequest(BaseModel):
    """Request to rename pet."""
    name: str


class RenamePetResponse(BaseModel):
    """Response after renaming pet."""
    success: bool
    name: str


@router.post("/pet/rename", response_model=RenamePetResponse)
async def rename_pet(
    request: RenamePetRequest,
    user: TelegramUser = Depends(get_current_user)
):
    """Rename the pet."""
    from database.repositories.pet_repo import pet_repo

    # Validate name length
    if len(request.name) > 20 or len(request.name) < 1:
        return RenamePetResponse(success=False, name="")

    await pet_repo.get_or_create_pet(user.id)
    pet = await pet_repo.rename_pet(user.id, request.name)

    return RenamePetResponse(success=True, name=pet.pet_name)
