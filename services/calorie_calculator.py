"""
Calorie and macro calculation service.

Implements Mifflin-St Jeor equation for BMR and TDEE calculations.
All constants are imported from the central constants module.
"""

from config import settings
from constants import (
    Sex,
    ActivityLevel,
    Goal,
    ACTIVITY_MULTIPLIERS,
    GOAL_ADJUSTMENTS,
    CALORIES_PER_GRAM_PROTEIN,
    CALORIES_PER_GRAM_CARBS,
    CALORIES_PER_GRAM_FAT,
)
from database.models import MacroTargets


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex
) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    Male:   BMR = (10 * weight) + (6.25 * height) - (5 * age) + 5
    Female: BMR = (10 * weight) + (6.25 * height) - (5 * age) - 161
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

    if sex == Sex.MALE:
        return base + 5
    else:
        return base - 161


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return bmr * multiplier


def calculate_daily_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
    activity_level: ActivityLevel,
    goal: Goal
) -> int:
    """
    Calculate daily calorie target based on all user factors.

    Returns a safe minimum based on sex (from settings, which defaults to constants).
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    adjusted = tdee + adjustment

    # Ensure minimum safe intake (use settings which can override constants)
    if sex == Sex.FEMALE:
        min_calories = settings.min_calories_female
    else:
        min_calories = settings.min_calories_male

    return max(int(adjusted), min_calories)


def get_macro_targets(daily_calories: int, goal: Goal) -> MacroTargets:
    """
    Calculate recommended macro split based on goal.

    Returns MacroTargets dataclass with protein, carbs, fat in grams.
    """
    if goal == Goal.LOSE:
        # Higher protein for muscle preservation
        protein_pct = 0.30
        carb_pct = 0.40
        fat_pct = 0.30
    elif goal == Goal.GAIN:
        # Balanced with slight carb emphasis
        protein_pct = 0.25
        carb_pct = 0.50
        fat_pct = 0.25
    else:  # Goal.MAINTAIN
        protein_pct = 0.25
        carb_pct = 0.45
        fat_pct = 0.30

    return MacroTargets(
        protein_g=int((daily_calories * protein_pct) / CALORIES_PER_GRAM_PROTEIN),
        carbs_g=int((daily_calories * carb_pct) / CALORIES_PER_GRAM_CARBS),
        fat_g=int((daily_calories * fat_pct) / CALORIES_PER_GRAM_FAT),
    )
