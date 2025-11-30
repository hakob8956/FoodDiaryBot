from typing import Literal


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "lightly_active": 1.375,
    "moderately_active": 1.55,
    "very_active": 1.725,
}

GOAL_ADJUSTMENTS = {
    "lose": -500,
    "maintain": 0,
    "gain": 300,
}


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"]
) -> float:
    """
    Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

    Male:   BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
    Female: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)

    if sex == "male":
        return base + 5
    else:
        return base - 161


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return bmr * multiplier


def calculate_daily_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Literal["male", "female"],
    activity_level: str,
    goal: Literal["lose", "maintain", "gain"]
) -> int:
    """
    Calculate daily calorie target based on all user factors.

    Returns a safe minimum of 1200 (female) or 1500 (male) calories.
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    adjusted = tdee + adjustment

    # Ensure minimum safe intake
    min_calories = 1200 if sex == "female" else 1500
    return max(int(adjusted), min_calories)


def get_macro_targets(daily_calories: int, goal: str) -> dict:
    """
    Calculate recommended macro split based on goal.

    Returns grams of protein, carbs, fat.
    """
    if goal == "lose":
        # Higher protein for muscle preservation
        protein_pct = 0.30
        carb_pct = 0.40
        fat_pct = 0.30
    elif goal == "gain":
        # Balanced with slight carb emphasis
        protein_pct = 0.25
        carb_pct = 0.50
        fat_pct = 0.25
    else:  # maintain
        protein_pct = 0.25
        carb_pct = 0.45
        fat_pct = 0.30

    return {
        "protein_g": int((daily_calories * protein_pct) / 4),
        "carbs_g": int((daily_calories * carb_pct) / 4),
        "fat_g": int((daily_calories * fat_pct) / 9),
    }
