import json
from datetime import date, timedelta
from typing import Optional

from database.repositories.food_log_repo import food_log_repo
from database.repositories.user_repo import user_repo


class SummaryGenerator:
    """Generates nutrition summaries and insights."""

    async def generate_summary(
        self,
        telegram_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        """Generate a comprehensive summary for a date range."""
        user = await user_repo.get_user(telegram_id)
        if not user:
            return None

        # Get all logs in range
        logs = await food_log_repo.get_logs_by_date_range(telegram_id, start_date, end_date)
        totals = await food_log_repo.get_range_totals(telegram_id, start_date, end_date)

        num_days = (end_date - start_date).days + 1

        # Calculate averages
        avg_calories = totals["calories"] / num_days if num_days > 0 else 0
        avg_protein = totals["protein"] / num_days if num_days > 0 else 0
        avg_carbs = totals["carbs"] / num_days if num_days > 0 else 0
        avg_fat = totals["fat"] / num_days if num_days > 0 else 0

        # Target comparison
        daily_target = user.daily_calorie_target or 2000
        target_diff = avg_calories - daily_target
        adherence_pct = (avg_calories / daily_target * 100) if daily_target > 0 else 0

        # Extract all food items
        all_foods = []
        for log in logs:
            analysis = json.loads(log.analysis_json)
            for item in analysis.get("items", []):
                all_foods.append(item["name"].lower())

        # Find common foods
        food_counts = {}
        for food in all_foods:
            food_counts[food] = food_counts.get(food, 0) + 1
        common_foods = sorted(food_counts.items(), key=lambda x: -x[1])[:5]

        # Generate insights
        insights = self._generate_insights(
            avg_calories, daily_target, avg_protein, avg_carbs, avg_fat,
            totals["meal_count"], num_days, common_foods
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": num_days
            },
            "totals": {
                "calories": int(totals["calories"]),
                "protein_g": round(totals["protein"], 1),
                "carbs_g": round(totals["carbs"], 1),
                "fat_g": round(totals["fat"], 1),
                "meals_logged": totals["meal_count"]
            },
            "averages": {
                "daily_calories": int(avg_calories),
                "daily_protein_g": round(avg_protein, 1),
                "daily_carbs_g": round(avg_carbs, 1),
                "daily_fat_g": round(avg_fat, 1)
            },
            "target_comparison": {
                "daily_target": daily_target,
                "avg_vs_target": int(target_diff),
                "adherence_percentage": round(adherence_pct, 1)
            },
            "common_foods": [f[0] for f in common_foods],
            "insights": insights
        }

    def _generate_insights(
        self,
        avg_cal: float,
        target: int,
        avg_protein: float,
        avg_carbs: float,
        avg_fat: float,
        meal_count: int,
        num_days: int,
        common_foods: list
    ) -> dict:
        """Generate personalized insights based on data."""
        positives = []
        improvements = []
        advice = []

        # Calorie analysis
        diff_pct = ((avg_cal - target) / target * 100) if target > 0 else 0

        if -10 <= diff_pct <= 10:
            positives.append("Great calorie control! You're staying close to your target.")
        elif diff_pct > 10:
            improvements.append(f"You're averaging {int(avg_cal - target)} kcal over your target.")
            advice.append("Consider smaller portions or lighter snacks between meals.")
        elif diff_pct < -10:
            if diff_pct < -20:
                improvements.append("You may be under-eating. Ensure you're getting enough fuel.")
            else:
                positives.append("You're in a good calorie deficit for your goals.")

        # Protein analysis
        protein_per_kg = avg_protein / 70  # Assume ~70kg for general advice
        if protein_per_kg >= 1.6:
            positives.append(f"Excellent protein intake at {int(avg_protein)}g/day!")
        elif protein_per_kg < 1.0:
            improvements.append(f"Protein is a bit low at {int(avg_protein)}g/day.")
            advice.append("Try adding eggs, Greek yogurt, or lean meat to boost protein.")

        # Macro balance
        total_cals = (avg_protein * 4) + (avg_carbs * 4) + (avg_fat * 9)
        if total_cals > 0:
            fat_pct = (avg_fat * 9 / total_cals) * 100
            if fat_pct > 40:
                improvements.append("Fat intake is on the higher side.")
                advice.append("Consider swapping fried foods for grilled alternatives.")

        # Consistency
        avg_meals = meal_count / num_days if num_days > 0 else 0
        if avg_meals >= 3:
            positives.append(f"Good logging consistency with {round(avg_meals, 1)} meals/day tracked.")
        elif avg_meals < 2:
            improvements.append("You might be missing some meals in your logs.")
            advice.append("Try to log everything you eat for more accurate tracking.")

        return {
            "positive_notes": positives,
            "improvements": improvements,
            "advice": advice
        }

    def format_summary_response(self, summary: dict) -> str:
        """Format summary as human-readable text."""
        period = summary["period"]
        avgs = summary["averages"]
        target = summary["target_comparison"]
        insights = summary["insights"]

        lines = [
            f"Summary: {period['start']} to {period['end']} ({period['days']} days)",
            "",
            f"Daily Average: {avgs['daily_calories']} kcal",
            f"  Protein: {avgs['daily_protein_g']}g | Carbs: {avgs['daily_carbs_g']}g | Fat: {avgs['daily_fat_g']}g",
            "",
            f"Target: {target['daily_target']} kcal/day",
            f"Adherence: {target['adherence_percentage']}%",
        ]

        if summary["common_foods"]:
            lines.append(f"\nCommon foods: {', '.join(summary['common_foods'][:5])}")

        if insights["positive_notes"]:
            lines.append("\nWhat's going well:")
            for note in insights["positive_notes"]:
                lines.append(f"  + {note}")

        if insights["improvements"]:
            lines.append("\nAreas to improve:")
            for note in insights["improvements"]:
                lines.append(f"  - {note}")

        if insights["advice"]:
            lines.append("\nSuggestions:")
            for tip in insights["advice"]:
                lines.append(f"  > {tip}")

        return "\n".join(lines)


# Singleton instance
summary_generator = SummaryGenerator()
