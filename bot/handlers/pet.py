"""
Pet command handler.

Handles /pet command to display pet status, achievements, and allow renaming.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.pet_service import pet_service
from constants import ACHIEVEMENTS

logger = logging.getLogger(__name__)


async def pet_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /pet command - show pet status.

    Usage:
      /pet - Show pet status
      /pet name <new_name> - Rename your pet
    """
    telegram_id = update.effective_user.id

    # Check for rename subcommand
    if context.args and len(context.args) >= 2 and context.args[0].lower() == "name":
        new_name = " ".join(context.args[1:])
        if len(new_name) > 20:
            await update.message.reply_text("Pet name must be 20 characters or less.")
            return

        from database.repositories.pet_repo import pet_repo
        await pet_repo.get_or_create_pet(telegram_id)
        await pet_repo.rename_pet(telegram_id, new_name)
        await update.message.reply_text(f"Your pet is now named \"{new_name}\"!")
        return

    try:
        pet_info = await pet_service.get_pet_info(telegram_id)

        # Format the message
        mood_emoji = {
            "stuffed": "🫃",
            "ecstatic": "🌟",
            "happy": "😊",
            "hungry": "😕",
            "starving": "😢",
        }

        streak_display = f"{pet_info.pet.current_streak} days"
        if pet_info.pet.current_streak > 0:
            streak_display += " 🔥"
        if pet_info.pet.best_streak > pet_info.pet.current_streak:
            streak_display += f" (Best: {pet_info.pet.best_streak})"

        # Progress bar for calories
        percent = pet_info.calories_percent
        bar_filled = min(10, percent // 10)
        bar_empty = 10 - bar_filled
        progress_bar = "█" * bar_filled + "░" * bar_empty

        # Warning for overeating
        percent_warning = ""
        if percent > 120:
            percent_warning = " ⚠️ Overeating!"

        message = f"""🐾 Meet {pet_info.pet.pet_name}!

```
{pet_info.ascii_art}
```

{mood_emoji.get(pet_info.mood.value, "")} Status: {pet_service.get_mood_text(pet_info.mood)}
📊 Today: {pet_info.calories_today}/{pet_info.calories_target} kcal ({percent}%){percent_warning}
    [{progress_bar}]
📈 Level: {pet_service.get_level_text(pet_info.level)} ({pet_info.pet.total_meals_logged} meals)
🔥 Streak: {streak_display}

{await pet_service.get_achievements_display(telegram_id)}

💡 Tip: Use /pet name <name> to rename your pet"""

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in pet command: {e}", exc_info=True)
        await update.message.reply_text("Sorry, couldn't load your pet. Try again later.")


def get_pet_handler() -> CommandHandler:
    """Return the pet command handler."""
    return CommandHandler("pet", pet_command)
