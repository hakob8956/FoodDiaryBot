"""Debug commands for testing (remove in production)."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.feature_flags import feature_flags
from database.repositories.user_repo import user_repo
from database.repositories.food_log_repo import food_log_repo


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Debug command to check feature flags and user status.
    Usage: /debug
    """
    telegram_id = update.effective_user.id
    user = await user_repo.get_user(telegram_id)

    if not user:
        await update.message.reply_text("User not found in database")
        return

    # Check feature flags
    daily_reminder_flag = feature_flags.is_enabled("daily_reminder", user_id=telegram_id, default=False)
    has_logged = await food_log_repo.has_logged_today(telegram_id)

    debug_info = f"""Debug Info:

User ID: {telegram_id}
Onboarding complete: {user.onboarding_complete}

Notification Settings:
  notifications_enabled: {user.notifications_enabled}
  reminder_hour: {user.reminder_hour}
  last_reminder_sent: {user.last_reminder_sent}

Feature Flags:
  daily_reminder: {daily_reminder_flag}

Today's Status:
  has_logged_today: {has_logged}
"""
    await update.message.reply_text(debug_info)


def get_debug_handlers() -> list[CommandHandler]:
    """Return debug command handlers."""
    return [
        CommandHandler("debug", debug_command),
    ]
