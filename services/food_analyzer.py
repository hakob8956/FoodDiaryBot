"""
Food analysis orchestration service.

Coordinates between OpenAI analysis and food log storage.
"""

import json
from typing import Optional
from datetime import date

from config import settings
from constants import InputType, Goal
from services.openai_service import openai_service
from services.calorie_calculator import get_macro_targets
from database.repositories.food_log_repo import food_log_repo
from database.repositories.user_repo import user_repo
from database.models import FoodLog


class FoodAnalyzer:
    """Orchestrates food analysis and logging."""

    async def analyze_and_log(
        self,
        telegram_id: int,
        text_description: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        photo_file_id: Optional[str] = None
    ) -> tuple[dict, FoodLog]:
        """
        Analyze food and create a log entry.

        Returns:
            Tuple of (analysis_result, food_log)
        """
        # Determine input type
        if image_bytes and text_description:
            input_type = InputType.PHOTO_TEXT
        elif image_bytes:
            input_type = InputType.PHOTO
        else:
            input_type = InputType.TEXT

        # Encode image if present
        image_base64 = None
        if image_bytes:
            image_base64 = await openai_service.encode_image_from_bytes(image_bytes)

        # Call OpenAI for analysis
        analysis = await openai_service.analyze_food(
            text_description=text_description,
            image_base64=image_base64
        )

        # Extract totals
        totals = analysis.get("totals", {})

        # Validate analysis - 0 calories usually means analysis failed
        if totals.get("calories", 0) == 0:
            raise ValueError("Could not analyze food - no nutritional data detected")

        # Create food log entry
        food_log = await food_log_repo.create_log(
            telegram_id=telegram_id,
            input_type=input_type,
            analysis_json=json.dumps(analysis),
            total_calories=totals.get("calories", 0),
            total_protein=totals.get("protein_g", 0),
            total_carbs=totals.get("carbs_g", 0),
            total_fat=totals.get("fat_g", 0),
            confidence_score=analysis.get("overall_confidence", 0.5),
            raw_input=text_description,
            photo_file_id=photo_file_id
        )

        return analysis, food_log

    async def get_daily_progress(self, telegram_id: int) -> Optional[dict]:
        """Get today's progress toward calorie goal."""
        user = await user_repo.get_user(telegram_id)
        if not user or not user.daily_calorie_target:
            return None

        today = date.today()
        totals = await food_log_repo.get_daily_totals(telegram_id, today)

        calories_consumed = totals.calories
        target = user.daily_calorie_target
        remaining = target - calories_consumed

        # Get macro targets based on user's goal
        macro_targets = None
        if user.goal:
            goal = Goal(user.goal) if isinstance(user.goal, str) else user.goal
            macro_targets = get_macro_targets(target, goal)

        return {
            "consumed": calories_consumed,
            "target": target,
            "remaining": remaining,
            "percentage": round((calories_consumed / target) * 100, 1) if target > 0 else 0,
            "protein": totals.protein,
            "carbs": totals.carbs,
            "fat": totals.fat,
            "meal_count": totals.meal_count,
            "protein_target": macro_targets.protein_g if macro_targets else None,
            "carbs_target": macro_targets.carbs_g if macro_targets else None,
            "fat_target": macro_targets.fat_g if macro_targets else None,
        }

    def _render_progress_bar(self, current: float, target: float, width: int = 6) -> str:
        """
        Render a text-based progress bar.

        Example output: "●●●●○○ 67g/100g"
        """
        if target <= 0:
            return f"{int(current)}g"

        ratio = min(current / target, 1.0)  # Cap at 100%
        filled = int(ratio * width)
        empty = width - filled

        bar = "●" * filled + "○" * empty
        return f"{bar} {int(current)}g/{int(target)}g"

    def format_log_response(
        self,
        analysis: dict,
        progress: Optional[dict] = None,
        entry_id: Optional[int] = None
    ) -> str:
        """Format a human-readable response for the user."""
        items = analysis.get("items", [])
        totals = analysis.get("totals", {})

        # Build item list
        item_names = [item["name"] for item in items[:3]]
        if len(items) > 3:
            item_names.append(f"+{len(items) - 3} more")

        food_list = ", ".join(item_names)
        calories = totals.get("calories", 0)
        protein = totals.get("protein_g", 0)

        response = f"Logged: {food_list}\n"
        response += f"~{calories} kcal | {protein}g protein"

        if progress:
            response += f"\n\nToday: {progress['consumed']}/{progress['target']} kcal"
            if progress['remaining'] > 0:
                response += f" ({progress['remaining']} remaining)"
            else:
                response += f" ({abs(progress['remaining'])} over target)"

            # Macro progress bars
            if progress.get('protein_target'):
                response += "\n\n"
                response += f"Protein: {self._render_progress_bar(progress['protein'], progress['protein_target'])}\n"
                response += f"Carbs:   {self._render_progress_bar(progress['carbs'], progress['carbs_target'])}\n"
                response += f"Fat:     {self._render_progress_bar(progress['fat'], progress['fat_target'])}"

        confidence = analysis.get("overall_confidence", 0)
        if confidence < settings.confidence_warning_threshold:
            response += "\n(estimate has higher uncertainty)"

        if entry_id:
            response += f"\n\n(Entry #{entry_id} - use /delete {entry_id} to remove)"

        return response


# Singleton instance
food_analyzer = FoodAnalyzer()
