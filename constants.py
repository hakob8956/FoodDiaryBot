"""
Project-wide constants and enums.

All magic values, thresholds, and enum definitions should be defined here
to avoid hardcoding values throughout the codebase.
"""

from enum import Enum


# =============================================================================
# USER ENUMS
# =============================================================================

class Sex(str, Enum):
    """Biological sex for calorie calculations."""
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Physical activity level for TDEE calculations."""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"


class Goal(str, Enum):
    """Weight management goal."""
    LOSE = "lose"
    MAINTAIN = "maintain"
    GAIN = "gain"
    GAIN_MUSCLES = "gain_muscles"


class InputType(str, Enum):
    """Food log input type."""
    PHOTO = "photo"
    TEXT = "text"
    PHOTO_TEXT = "photo_text"
    VOICE = "voice"


# =============================================================================
# CALORIE CALCULATION
# =============================================================================

# Activity level multipliers for TDEE calculation (Mifflin-St Jeor)
ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
}

# Calorie adjustments based on weight goal
GOAL_ADJUSTMENTS: dict[Goal, int] = {
    Goal.LOSE: -500,
    Goal.MAINTAIN: 0,
    Goal.GAIN: 300,
    Goal.GAIN_MUSCLES: 300,
}

# Minimum safe daily calorie intake
MIN_CALORIES_FEMALE = 1200
MIN_CALORIES_MALE = 1500

# Default calorie target when user hasn't set one
DEFAULT_CALORIE_TARGET = 2000


# =============================================================================
# MACRO PERCENTAGES
# =============================================================================

# Default macro split percentages
MACRO_PROTEIN_PCT_MIN = 0.25
MACRO_PROTEIN_PCT_MAX = 0.30
MACRO_CARBS_PCT_MIN = 0.40
MACRO_CARBS_PCT_MAX = 0.50
MACRO_FAT_PCT_MIN = 0.25
MACRO_FAT_PCT_MAX = 0.30

# Calories per gram of each macro
CALORIES_PER_GRAM_PROTEIN = 4
CALORIES_PER_GRAM_CARBS = 4
CALORIES_PER_GRAM_FAT = 9


# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

# Confidence score thresholds for food analysis
CONFIDENCE_WARNING_THRESHOLD = 0.7  # Below this, show uncertainty warning
CONFIDENCE_HIGH = 0.9  # Above this, considered high confidence


# =============================================================================
# REMINDERS
# =============================================================================

# Default reminder hour (24-hour format)
DEFAULT_REMINDER_HOUR = 20

# Valid hour range for reminders
REMINDER_HOUR_MIN = 0
REMINDER_HOUR_MAX = 23


# =============================================================================
# SUMMARY ANALYSIS
# =============================================================================

# Adherence to calorie target thresholds (percentage)
ADHERENCE_TOLERANCE_PCT = 10  # Within ±10% is "on target"
ADHERENCE_SEVERE_PCT = 20  # Beyond ±20% is "significantly off"

# Number of common foods to show in summaries
COMMON_FOODS_LIMIT = 5

# Minimum meals per day for consistency advice
MIN_MEALS_PER_DAY = 3

# Assumed weight for protein per kg calculations when weight unknown
ASSUMED_WEIGHT_KG = 70


# =============================================================================
# JOB SCHEDULING
# =============================================================================

# Reminder check interval in seconds (1 hour)
REMINDER_CHECK_INTERVAL_SECONDS = 3600

# Delay before first reminder check (60 seconds)
REMINDER_FIRST_RUN_DELAY_SECONDS = 60


# =============================================================================
# TELEGRAM LIMITS
# =============================================================================

# Maximum characters in a Telegram message
TELEGRAM_MESSAGE_MAX_CHARS = 4096

# Safe limit for JSON exports (leaving room for formatting)
TELEGRAM_SAFE_MESSAGE_CHARS = 4000


# =============================================================================
# WEEKLY SUMMARY
# =============================================================================

# Day of week for weekly summary (0 = Monday)
WEEKLY_SUMMARY_DAY = 0

# Hour to send weekly summary (9 AM)
WEEKLY_SUMMARY_HOUR = 9


# =============================================================================
# DATABASE DEFAULTS
# =============================================================================

# Default values for database columns
DB_DEFAULT_NOTIFICATIONS_ENABLED = True
DB_DEFAULT_CALORIE_OVERRIDE = False
DB_DEFAULT_ONBOARDING_COMPLETE = False
DB_DEFAULT_WEEKLY_SUMMARY_ENABLED = True


# =============================================================================
# PET SYSTEM (TAMAGOTCHI)
# =============================================================================

class PetMood(str, Enum):
    """Pet mood states based on daily calorie goal percentage."""
    STARVING = "starving"    # 0% - nothing logged
    HUNGRY = "hungry"        # 1-49% - under half
    HAPPY = "happy"          # 50-99% - good progress
    ECSTATIC = "ecstatic"    # 100-120% - hit target
    STUFFED = "stuffed"      # 121%+ - overeaten


class PetLevel(str, Enum):
    """Pet evolution levels based on total meals logged."""
    EGG = "egg"          # 0-1 meals
    BABY = "baby"        # 2-50 meals
    TEEN = "teen"        # 51-150 meals
    ADULT = "adult"      # 151-500 meals
    ELDER = "elder"      # 501+ meals


# Thresholds for pet levels (total meals required)
PET_LEVEL_THRESHOLDS = {
    PetLevel.EGG: 0,
    PetLevel.BABY: 2,
    PetLevel.TEEN: 51,
    PetLevel.ADULT: 151,
    PetLevel.ELDER: 501,
}

# Thresholds for mood (percentage of daily calorie goal)
PET_MOOD_STUFFED_MIN = 121   # 121%+ = stuffed (overeaten)
PET_MOOD_ECSTATIC_MIN = 100  # 100-120% = ecstatic (hit target)
PET_MOOD_HAPPY_MIN = 50      # 50-99% = happy (good progress)
PET_MOOD_HUNGRY_MIN = 1      # 1-49% = hungry (under half)
# 0% = starving (nothing logged)

# Default pet name
DEFAULT_PET_NAME = "Nibbles"


# =============================================================================
# ACHIEVEMENTS
# =============================================================================

# Achievement definitions: id -> (name, description, emoji)
ACHIEVEMENTS = {
    # Milestone achievements
    "first_bite": ("First Bite", "Log your first meal", "🍽️"),
    "getting_started": ("Getting Started", "Log 10 meals", "🌱"),
    "century_club": ("Century Club", "Log 100 meals", "💯"),
    "dedicated": ("Dedicated", "Log 500 meals", "🏅"),

    # Streak achievements
    "week_warrior": ("Week Warrior", "7-day logging streak", "🔥"),
    "fortnight_fighter": ("Fortnight Fighter", "14-day logging streak", "⚡"),
    "month_master": ("Month Master", "30-day logging streak", "👑"),

    # Evolution achievements
    "hatched": ("Hatched!", "Your pet evolved from Egg to Baby", "🐣"),
    "growing_up": ("Growing Up", "Your pet evolved to Teen", "🌟"),
    "all_grown": ("All Grown Up", "Your pet evolved to Adult", "💪"),
    "wise_one": ("The Wise One", "Your pet evolved to Elder", "🧙"),
}
