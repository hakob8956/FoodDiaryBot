from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class User(BaseModel):
    """User profile model."""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[Literal["male", "female"]] = None
    activity_level: Optional[Literal["sedentary", "lightly_active", "moderately_active", "very_active"]] = None
    goal: Optional[Literal["lose", "maintain", "gain"]] = None
    daily_calorie_target: Optional[int] = None
    calorie_override: bool = False
    onboarding_complete: bool = False
    notifications_enabled: bool = True
    reminder_hour: int = 20
    last_reminder_sent: Optional[datetime] = None
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
    input_type: Literal["photo", "text", "photo_text"]
    raw_input: Optional[str] = None
    photo_file_id: Optional[str] = None
    analysis_json: str
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    confidence_score: float
