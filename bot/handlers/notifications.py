from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.user_repo import user_repo


async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /notifications command.

    Usage:
    - /notifications - Show current settings
    - /notifications on - Enable reminders
    - /notifications off - Disable reminders
    - /notifications time 20 - Set reminder hour (0-23)
    """
    telegram_id = update.effective_user.id

    # Check if user is onboarded
    user = await user_repo.get_user(telegram_id)
    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please set up your profile first with /start"
        )
        return

    args = context.args

    # No args - show current settings
    if not args:
        status = "enabled" if user.notifications_enabled else "disabled"
        hour_str = f"{user.reminder_hour:02d}:00"
        await update.message.reply_text(
            f"Notification Settings:\n\n"
            f"Daily reminders: {status}\n"
            f"Reminder time: {hour_str}\n\n"
            f"Commands:\n"
            f"/notifications on - Enable reminders\n"
            f"/notifications off - Disable reminders\n"
            f"/notifications time <hour> - Set time (0-23)"
        )
        return

    action = args[0].lower()

    # Enable notifications
    if action == "on":
        await user_repo.set_notifications_enabled(telegram_id, True)
        await update.message.reply_text(
            f"Daily reminders enabled!\n"
            f"You'll be reminded at {user.reminder_hour:02d}:00 if you haven't logged food."
        )
        return

    # Disable notifications
    if action == "off":
        await user_repo.set_notifications_enabled(telegram_id, False)
        await update.message.reply_text(
            "Daily reminders disabled.\n"
            "Use /notifications on to re-enable."
        )
        return

    # Set reminder time
    if action == "time":
        if len(args) < 2:
            await update.message.reply_text(
                "Please specify an hour (0-23).\n"
                "Example: /notifications time 20"
            )
            return

        try:
            hour = int(args[1])
            if not 0 <= hour <= 23:
                raise ValueError()

            await user_repo.set_reminder_hour(telegram_id, hour)
            await update.message.reply_text(
                f"Reminder time set to {hour:02d}:00"
            )

        except ValueError:
            await update.message.reply_text(
                "Invalid hour. Please use a number between 0 and 23.\n"
                "Example: /notifications time 20 (for 8 PM)"
            )
        return

    # Unknown action
    await update.message.reply_text(
        "Unknown option. Use:\n"
        "/notifications on\n"
        "/notifications off\n"
        "/notifications time <hour>"
    )


def get_notifications_handler() -> CommandHandler:
    """Return the notifications command handler."""
    return CommandHandler("notifications", notifications_command)
