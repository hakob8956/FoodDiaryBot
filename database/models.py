"""
Database models and data classes.

Uses Pydantic for validation and dataclasses for simple data containers.
All enum types are imported from constants.py.
"""

from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from constants import (
    Sex,
    ActivityLevel,
    Goal,
    InputType,
    DEFAULT_REMINDER_HOUR,
    DB_DEFAULT_NOTIFICATIONS_ENABLED,
    DB_DEFAULT_CALORIE_OVERRIDE,
    DB_DEFAULT_ONBOARDING_COMPLETE,
    DB_DEFAULT_WEEKLY_SUMMARY_ENABLED,
)


# =============================================================================
# PYDANTIC MODELS (for database entities)
# =============================================================================

class User(BaseModel):
    """User profile model."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[Sex] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    daily_calorie_target: Optional[int] = None
    calorie_override: bool = DB_DEFAULT_CALORIE_OVERRIDE
    protein_target: Optional[int] = None
    carbs_target: Optional[int] = None
    fat_target: Optional[int] = None
    macro_override: bool = False
    onboarding_complete: bool = DB_DEFAULT_ONBOARDING_COMPLETE
    notifications_enabled: bool = DB_DEFAULT_NOTIFICATIONS_ENABLED
    reminder_hour: int = DEFAULT_REMINDER_HOUR
    last_reminder_sent: Optional[datetime] = None
    weekly_summary_enabled: bool = DB_DEFAULT_WEEKLY_SUMMARY_ENABLED
    last_weekly_summary_sent: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OnboardingState(BaseModel):
    """Tracks multi-step onboarding progress."""
    telegram_id: int
    current_step: str
    collected_data: dict = Field(default_factory=dict)
    updated_at: Optional[datetime] = None


class FoodItem(BaseModel):
    """Individual food item from analysis."""
    name: str
    portion: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


class FoodAnalysis(BaseModel):
    """Complete food analysis result from GPT-4o."""
    items: list[FoodItem]
    totals: dict
    overall_confidence: float
    notes: Optional[str] = None


class FoodLog(BaseModel):
    """Food log entry."""
    id: Optional[int] = None
    telegram_id: int
    logged_at: Optional[datetime] = None
    input_type: InputType
    raw_input: Optional[str] = None
    photo_file_id: Optional[str] = None
    analysis_json: str
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    confidence_score: float


# =============================================================================
# DATACLASSES (for aggregation results)
# =============================================================================

@dataclass
class DailyTotals:
    """Aggregated totals for a single day."""
    calories: int = 0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    meal_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyTotals':
        """Create from database row dict."""
        return cls(
            calories=int(data.get('calories', 0) or 0),
            protein=float(data.get('protein', 0) or 0),
            carbs=float(data.get('carbs', 0) or 0),
            fat=float(data.get('fat', 0) or 0),
            meal_count=int(data.get('meal_count', 0) or 0),
        )

    def to_dict(self) -> dict:
        """Convert to dict for API responses."""
        return {
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'meal_count': self.meal_count,
        }


@dataclass
class RangeTotals:
    """Aggregated totals for a date range."""
    calories: int = 0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    meal_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> 'RangeTotals':
        """Create from database row dict."""
        return cls(
            calories=int(data.get('calories', 0) or 0),
            protein=float(data.get('protein', 0) or 0),
            carbs=float(data.get('carbs', 0) or 0),
            fat=float(data.get('fat', 0) or 0),
            meal_count=int(data.get('meal_count', 0) or 0),
        )

    def to_dict(self) -> dict:
        """Convert to dict for API responses."""
        return {
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'meal_count': self.meal_count,
        }


@dataclass
class MacroTargets:
    """Daily macro nutrient targets."""
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dict for API responses."""
        return {
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fat_g': self.fat_g,
        }
