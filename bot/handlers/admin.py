"""
Admin command handlers.

Provides admin-only commands like broadcast messaging and testing.
"""

import logging
from datetime import date, timedelta

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from database.repositories.user_repo import user_repo
from database.repositories.pet_repo import pet_repo
from services.summary_generator import summary_generator
from services.reminder_service import generate_reminder_for_user
from constants import PetLevel, PET_LEVEL_THRESHOLDS

logger = logging.getLogger(__name__)


async def broadcast_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /broadcast command - send message to all users.

    Usage: /broadcast <message>
    Only works for admin user.
    Preserves newlines and formatting.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    # Get full message text after /broadcast command
    full_text = update.message.text or ""

    # Remove the /broadcast command prefix
    if full_text.startswith("/broadcast"):
        message = full_text[len("/broadcast"):].strip()
    else:
        message = ""

    if not message:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    # Get all users
    users = await user_repo.get_all_users()

    if not users:
        await update.message.reply_text("No users found.")
        return

    # Send to all users
    success_count = 0
    failed_count = 0

    await update.message.reply_text(f"Sending to {len(users)} users...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=message
            )
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {user.telegram_id}: {e}")
            failed_count += 1

    await update.message.reply_text(
        f"Broadcast complete.\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {failed_count}"
    )


async def adminhelp_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /adminhelp command - show admin commands.

    Usage: /adminhelp
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    help_text = """🔐 Admin Commands

/stats
  Show bot usage statistics
  (users, food logs, activity)

/broadcast <message>
  Send a message to all users
  Supports multi-line messages

/testweekly
  Test weekly summary generation
  Sends your last 7 days summary

/testreminder
  Test AI-generated reminder message
  Based on your last 7 days food log

/setpet <level> [mood]
  Change pet level and mood for testing
  Levels: egg, baby, teen, adult, elder
  Moods: starving, hungry, happy, ecstatic, stuffed

/adminhelp
  Show this help message"""

    await update.message.reply_text(help_text)


async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /stats command - show usage statistics.

    Usage: /stats
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    try:
        stats = await user_repo.get_stats()

        message = f"""📊 Bot Statistics

👥 Users
  Total: {stats['total_users']}
  Active (7d): {stats['active_users_7d']}

📝 Food Logs
  Total: {stats['total_logs']}
  Today: {stats['logs_today']}
  This week: {stats['logs_week']}"""

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text(f"Error: {e}")


async def testweekly_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /testweekly command - send weekly summary to admin for testing.

    Usage: /testweekly
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    await update.message.reply_text("Generating weekly summary...")

    try:
        # Get last 7 days
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=6)  # 7 days total

        # Generate summary for admin
        summary = await summary_generator.generate_summary(
            telegram_id=update.effective_user.id,
            start_date=start_date,
            end_date=end_date
        )

        if not summary or summary["totals"]["meals_logged"] == 0:
            await update.message.reply_text("No data found for the last 7 days.")
            return

        # Format the summary
        formatted = summary_generator.format_summary_response(summary)
        message = (
            "📊 Weekly Nutrition Summary (TEST)\n\n"
            f"{formatted}\n\n"
            "(Use /notifications weeklysummary off to disable)"
        )

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error generating test weekly summary: {e}")
        await update.message.reply_text(f"Error: {e}")


async def testreminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /testreminder command - test AI-generated reminder message.

    Usage: /testreminder
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    await update.message.reply_text("Generating AI reminder...")

    try:
        message = await generate_reminder_for_user(update.effective_user.id)
        await update.message.reply_text(f"🧪 Test Reminder:\n\n{message}")

    except Exception as e:
        logger.error(f"Error generating test reminder: {e}")
        await update.message.reply_text(f"Error: {e}")


async def setpet_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /setpet command - change pet level and mood for testing.

    Usage: /setpet <level> [mood]
    Levels: egg, baby, teen, adult, elder
    Moods: starving, hungry, happy, ecstatic, stuffed
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    valid_levels = ["egg", "baby", "teen", "adult", "elder"]
    valid_moods = ["starving", "hungry", "happy", "ecstatic", "stuffed"]

    # Mood to calorie percentage mapping
    mood_calories = {
        "starving": 0,      # 0%
        "hungry": 25,       # 25% (1-49%)
        "happy": 75,        # 75% (50-99%)
        "ecstatic": 100,    # 100% (100-120%)
        "stuffed": 150,     # 150% (121%+)
    }

    if not context.args:
        await update.message.reply_text(
            "Usage: /setpet <level> [mood]\n\n"
            "Levels:\n"
            "  egg - 0 meals\n"
            "  baby - 2 meals\n"
            "  teen - 51 meals\n"
            "  adult - 151 meals\n"
            "  elder - 501 meals\n\n"
            "Moods (optional):\n"
            "  starving - 0% calories\n"
            "  hungry - 25% calories\n"
            "  happy - 75% calories\n"
            "  ecstatic - 100% calories\n"
            "  stuffed - 150% calories"
        )
        return

    level_name = context.args[0].lower()
    if level_name not in valid_levels:
        await update.message.reply_text(f"Invalid level. Choose: {', '.join(valid_levels)}")
        return

    level = PetLevel(level_name)
    meals = PET_LEVEL_THRESHOLDS[level]

    # Check for mood argument
    mood_name = None
    calories_set = None
    if len(context.args) >= 2:
        mood_name = context.args[1].lower()
        if mood_name not in valid_moods:
            await update.message.reply_text(f"Invalid mood. Choose: {', '.join(valid_moods)}")
            return

        # Calculate calories to set based on user's target
        from database.repositories.user_repo import user_repo
        from database.repositories.food_log_repo import food_log_repo
        from constants import DEFAULT_CALORIE_TARGET

        user = await user_repo.get_user(update.effective_user.id)
        target = user.daily_calorie_target if user and user.daily_calorie_target else DEFAULT_CALORIE_TARGET
        calories_set = int(target * mood_calories[mood_name] / 100)

        # Set today's calories by adjusting food logs
        await food_log_repo.set_daily_calories(update.effective_user.id, calories_set)

    try:
        await pet_repo.set_meals(update.effective_user.id, meals)
        response = f"✅ Pet set to {level_name.title()}! (meals: {meals})"
        if mood_name:
            response += f"\n✅ Mood set to {mood_name.title()}! (calories: {calories_set})"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error setting pet: {e}")
        await update.message.reply_text(f"Error: {e}")


def get_admin_handlers() -> list[CommandHandler]:
    """Return all admin command handlers."""
    return [
        CommandHandler("adminhelp", adminhelp_command),
        CommandHandler("stats", stats_command),
        CommandHandler("broadcast", broadcast_command),
        CommandHandler("testweekly", testweekly_command),
        CommandHandler("testreminder", testreminder_command),
        CommandHandler("setpet", setpet_command),
    ]


# Keep for backwards compatibility
def get_admin_handler() -> CommandHandler:
    """Return the broadcast command handler."""
    return CommandHandler("broadcast", broadcast_command)
