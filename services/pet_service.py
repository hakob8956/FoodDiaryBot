"""
Pet service.

Core logic for the Tamagotchi pet system including mood, level,
image URLs, and achievement checking.
"""

from datetime import date
from typing import Optional
from dataclasses import dataclass

from database.repositories.pet_repo import pet_repo
from database.repositories.food_log_repo import food_log_repo
from database.repositories.user_repo import user_repo
from database.models import PetStatus
from constants import (
    PetMood,
    PetLevel,
    PET_LEVEL_THRESHOLDS,
    PET_MOOD_STUFFED_MIN,
    PET_MOOD_ECSTATIC_MIN,
    PET_MOOD_HAPPY_MIN,
    PET_MOOD_HUNGRY_MIN,
    ACHIEVEMENTS,
    DEFAULT_CALORIE_TARGET,
)


@dataclass
class PetInfo:
    """Complete pet information for display."""
    pet: PetStatus
    level: PetLevel
    mood: PetMood
    image_url: str
    ascii_art: str  # Fallback for bot
    calories_percent: int
    calories_today: int
    calories_target: int
    new_achievements: list[str]  # Achievement IDs unlocked this session
    evolved: bool = False  # True if pet just evolved to a new level


class PetService:
    """Service for pet operations."""

    def get_level(self, total_meals: int) -> PetLevel:
        """Determine pet level based on total meals logged."""
        if total_meals >= PET_LEVEL_THRESHOLDS[PetLevel.ELDER]:
            return PetLevel.ELDER
        elif total_meals >= PET_LEVEL_THRESHOLDS[PetLevel.ADULT]:
            return PetLevel.ADULT
        elif total_meals >= PET_LEVEL_THRESHOLDS[PetLevel.TEEN]:
            return PetLevel.TEEN
        elif total_meals >= PET_LEVEL_THRESHOLDS[PetLevel.BABY]:
            return PetLevel.BABY
        else:
            return PetLevel.EGG

    def get_mood(self, calories_percent: int) -> PetMood:
        """Determine pet mood based on calorie goal percentage."""
        if calories_percent >= PET_MOOD_STUFFED_MIN:
            return PetMood.STUFFED
        elif calories_percent >= PET_MOOD_ECSTATIC_MIN:
            return PetMood.ECSTATIC
        elif calories_percent >= PET_MOOD_HAPPY_MIN:
            return PetMood.HAPPY
        elif calories_percent >= PET_MOOD_HUNGRY_MIN:
            return PetMood.HUNGRY
        else:
            return PetMood.STARVING

    def get_image_url(self, level: PetLevel, mood: PetMood) -> str:
        """Get image URL for pet based on level and mood."""
        if level == PetLevel.EGG:
            return "/pet/egg.png"
        return f"/pet/{level.value}-{mood.value}.png"

    def get_ascii(self, level: PetLevel, mood: PetMood) -> str:
        """Get ASCII art fallback for bot messages."""
        # ASCII art by level and mood
        ascii_art = {
            PetLevel.EGG: "  ___\n /   \\\n | ? |\n \\___/",
            PetLevel.BABY: {
                PetMood.STUFFED: "  ∩∩\n (×‿×)\n  <O>\n   ∧",
                PetMood.ECSTATIC: "  ∩∩\n (★‿★)\n  <|>\n   ∧",
                PetMood.HAPPY: "  ∩∩\n (°◡°)\n  <|>\n   ∧",
                PetMood.HUNGRY: "  ∩∩\n (°︿°)\n  <|>\n   ∧",
                PetMood.STARVING: "  ∩∩\n (;﹏;)\n  <|>\n   ∧",
            },
            PetLevel.TEEN: {
                PetMood.STUFFED: "  ∩∩\n (×‿×)\n /|O |\\\n  ∧  ∧",
                PetMood.ECSTATIC: "  ∩∩\n (★‿★)\n /|  |\\\n  ∧  ∧",
                PetMood.HAPPY: "  ∩∩\n (◕‿◕)\n /|  |\\\n  ∧  ∧",
                PetMood.HUNGRY: "  ∩∩\n (◕︿◕)\n /|  |\\\n  ∧  ∧",
                PetMood.STARVING: "  ∩∩\n (;﹏;)\n /|  |\\\n  ∧  ∧",
            },
            PetLevel.ADULT: {
                PetMood.STUFFED: "  ∩∩\n (×‿×)\n /|██|\\\n  ∧  ∧",
                PetMood.ECSTATIC: "  ∩∩\n (★‿★)\n /|██|\\\n  ∧  ∧",
                PetMood.HAPPY: "  ∩∩\n (◕‿◕)\n /|██|\\\n  ∧  ∧",
                PetMood.HUNGRY: "  ∩∩\n (◕︿◕)\n /|██|\\\n  ∧  ∧",
                PetMood.STARVING: "  ∩∩\n (;﹏;)\n /|██|\\\n  ∧  ∧",
            },
            PetLevel.ELDER: {
                PetMood.STUFFED: " ∩∩∩\n (×‿×)\n~/|██|\\~\n~~∧  ∧~~",
                PetMood.ECSTATIC: " ∩∩∩\n (★‿★)\n~/|██|\\~\n~~∧  ∧~~",
                PetMood.HAPPY: " ∩∩∩\n (◕‿◕)\n~/|██|\\~\n~~∧  ∧~~",
                PetMood.HUNGRY: " ∩∩∩\n (◕︿◕)\n~/|██|\\~\n~~∧  ∧~~",
                PetMood.STARVING: " ∩∩∩\n (;﹏;)\n~/|██|\\~\n~~∧  ∧~~",
            },
        }

        if level == PetLevel.EGG:
            return ascii_art[level]

        level_art = ascii_art.get(level, ascii_art[PetLevel.BABY])
        return level_art.get(mood, level_art.get(PetMood.HAPPY, ""))

    async def get_pet_info(self, telegram_id: int) -> PetInfo:
        """Get complete pet information for display."""
        pet = await pet_repo.get_or_create_pet(telegram_id)

        # Get user's calorie target
        user = await user_repo.get_user(telegram_id)
        calories_target = user.daily_calorie_target if user and user.daily_calorie_target else DEFAULT_CALORIE_TARGET

        # Get calories logged today
        today = date.today()
        daily_totals = await food_log_repo.get_daily_totals(telegram_id, today)
        calories_today = daily_totals.calories

        # Calculate percentage
        calories_percent = int((calories_today / calories_target) * 100) if calories_target > 0 else 0

        # Determine level and mood
        level = self.get_level(pet.total_meals_logged)
        mood = self.get_mood(calories_percent)
        image_url = self.get_image_url(level, mood)
        ascii_art = self.get_ascii(level, mood)

        return PetInfo(
            pet=pet,
            level=level,
            mood=mood,
            image_url=image_url,
            ascii_art=ascii_art,
            calories_percent=calories_percent,
            calories_today=calories_today,
            calories_target=calories_target,
            new_achievements=[],
        )

    async def feed_pet(self, telegram_id: int) -> PetInfo:
        """
        Feed the pet (called after logging food).

        Returns PetInfo with any newly unlocked achievements.
        """
        # Get current level before feeding
        pet_before = await pet_repo.get_or_create_pet(telegram_id)
        level_before = self.get_level(pet_before.total_meals_logged)

        # Feed the pet (increments meal count, updates streak)
        pet = await pet_repo.feed_pet(telegram_id)

        # Check for achievements
        new_achievements = await self._check_achievements(
            telegram_id, pet, level_before
        )

        # Get user's calorie target
        user = await user_repo.get_user(telegram_id)
        calories_target = user.daily_calorie_target if user and user.daily_calorie_target else DEFAULT_CALORIE_TARGET

        # Get updated info
        today = date.today()
        daily_totals = await food_log_repo.get_daily_totals(telegram_id, today)
        calories_today = daily_totals.calories

        # Calculate percentage
        calories_percent = int((calories_today / calories_target) * 100) if calories_target > 0 else 0

        level = self.get_level(pet.total_meals_logged)
        mood = self.get_mood(calories_percent)
        image_url = self.get_image_url(level, mood)
        ascii_art = self.get_ascii(level, mood)

        # Check if pet evolved
        evolved = level != level_before

        return PetInfo(
            pet=pet,
            level=level,
            mood=mood,
            image_url=image_url,
            ascii_art=ascii_art,
            calories_percent=calories_percent,
            calories_today=calories_today,
            calories_target=calories_target,
            new_achievements=new_achievements,
            evolved=evolved,
        )

    async def _check_achievements(
        self,
        telegram_id: int,
        pet: PetStatus,
        level_before: PetLevel
    ) -> list[str]:
        """Check and unlock any new achievements."""
        new_achievements = []
        level_after = self.get_level(pet.total_meals_logged)

        # Meal count achievements
        meal_achievements = [
            (1, "first_bite"),
            (10, "getting_started"),
            (100, "century_club"),
            (500, "dedicated"),
        ]

        for threshold, achievement_id in meal_achievements:
            if pet.total_meals_logged >= threshold:
                result = await pet_repo.unlock_achievement(telegram_id, achievement_id)
                if result:
                    new_achievements.append(achievement_id)

        # Streak achievements
        streak_achievements = [
            (7, "week_warrior"),
            (14, "fortnight_fighter"),
            (30, "month_master"),
        ]

        for threshold, achievement_id in streak_achievements:
            if pet.current_streak >= threshold:
                result = await pet_repo.unlock_achievement(telegram_id, achievement_id)
                if result:
                    new_achievements.append(achievement_id)

        # Evolution achievements
        evolution_achievements = [
            (PetLevel.EGG, PetLevel.BABY, "hatched"),
            (PetLevel.BABY, PetLevel.TEEN, "growing_up"),
            (PetLevel.TEEN, PetLevel.ADULT, "all_grown"),
            (PetLevel.ADULT, PetLevel.ELDER, "wise_one"),
        ]

        for from_level, to_level, achievement_id in evolution_achievements:
            if level_before == from_level and level_after == to_level:
                result = await pet_repo.unlock_achievement(telegram_id, achievement_id)
                if result:
                    new_achievements.append(achievement_id)

        return new_achievements

    async def get_achievements_display(self, telegram_id: int) -> str:
        """Get formatted achievements list for display."""
        unlocked = await pet_repo.get_achievements(telegram_id)
        unlocked_ids = {a.achievement_id for a in unlocked}

        lines = []
        for achievement_id, (name, desc, emoji) in ACHIEVEMENTS.items():
            if achievement_id in unlocked_ids:
                lines.append(f"  ✅ {emoji} {name}")
            else:
                lines.append(f"  🔒 {name}")

        unlocked_count = len(unlocked_ids)
        total_count = len(ACHIEVEMENTS)

        return f"🏆 Achievements: {unlocked_count}/{total_count}\n" + "\n".join(lines)

    def get_mood_text(self, mood: PetMood) -> str:
        """Get display text for mood."""
        mood_texts = {
            PetMood.STUFFED: "Stuffed",
            PetMood.ECSTATIC: "Ecstatic",
            PetMood.HAPPY: "Happy",
            PetMood.HUNGRY: "Hungry",
            PetMood.STARVING: "Starving",
        }
        return mood_texts.get(mood, "Unknown")

    def get_level_text(self, level: PetLevel) -> str:
        """Get display text for level."""
        level_texts = {
            PetLevel.EGG: "Egg",
            PetLevel.BABY: "Baby",
            PetLevel.TEEN: "Teen",
            PetLevel.ADULT: "Adult",
            PetLevel.ELDER: "Elder",
        }
        return level_texts.get(level, "Unknown")


# Singleton instance
pet_service = PetService()
