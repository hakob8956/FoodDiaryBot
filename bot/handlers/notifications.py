"""
Notification settings handler.

Handles /notifications command for managing reminder settings.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.user_repo import user_repo
from database.models import User
from constants import REMINDER_HOUR_MIN, REMINDER_HOUR_MAX
from bot.messages import Messages
from bot.utils.decorators import require_onboarding


@require_onboarding
async def notifications_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """
    Handle /notifications command.

    Usage:
    - /notifications - Show current settings
    - /notifications on - Enable daily reminders
    - /notifications off - Disable daily reminders
    - /notifications time 20 - Set reminder hour (0-23)
    - /notifications weeklysummary on - Enable weekly summaries
    - /notifications weeklysummary off - Disable weekly summaries
    """
    telegram_id = user.telegram_id
    args = context.args

    # No args - show current settings
    if not args:
        status = Messages.NOTIFICATIONS_ENABLED if user.notifications_enabled else Messages.NOTIFICATIONS_DISABLED
        weekly_status = Messages.NOTIFICATIONS_ENABLED if user.weekly_summary_enabled else Messages.NOTIFICATIONS_DISABLED
        await update.message.reply_text(
            Messages.NOTIFICATIONS_STATUS.format(
                status=status,
                hour=user.reminder_hour,
                weekly_status=weekly_status
            )
        )
        return

    action = args[0].lower()

    # Weekly summary toggle
    if action == "weeklysummary":
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /notifications weeklysummary on|off"
            )
            return

        subaction = args[1].lower()
        if subaction == "on":
            await user_repo.set_weekly_summary_enabled(telegram_id, True)
            await update.message.reply_text(Messages.WEEKLY_SUMMARY_ON)
        elif subaction == "off":
            await user_repo.set_weekly_summary_enabled(telegram_id, False)
            await update.message.reply_text(Messages.WEEKLY_SUMMARY_OFF)
        else:
            await update.message.reply_text(
                "Usage: /notifications weeklysummary on|off"
            )
        return

    # Enable notifications
    if action == "on":
        await user_repo.set_notifications_enabled(telegram_id, True)
        await update.message.reply_text(
            Messages.NOTIFICATIONS_ON.format(hour=user.reminder_hour)
        )
        return

    # Disable notifications
    if action == "off":
        await user_repo.set_notifications_enabled(telegram_id, False)
        await update.message.reply_text(Messages.NOTIFICATIONS_OFF)
        return

    # Set reminder time
    if action == "time":
        if len(args) < 2:
            await update.message.reply_text(Messages.NOTIFICATIONS_TIME_INVALID)
            return

        try:
            hour = int(args[1])
            if not REMINDER_HOUR_MIN <= hour <= REMINDER_HOUR_MAX:
                raise ValueError()

            await user_repo.set_reminder_hour(telegram_id, hour)
            await update.message.reply_text(
                Messages.NOTIFICATIONS_TIME_SET.format(hour=hour)
            )

        except ValueError:
            await update.message.reply_text(Messages.NOTIFICATIONS_TIME_INVALID)
        return

    # Unknown action
    await update.message.reply_text(
        "Unknown option. Use:\n"
        "/notifications on\n"
        "/notifications off\n"
        "/notifications time <hour>\n"
        "/notifications weeklysummary on|off"
    )


def get_notifications_handler() -> CommandHandler:
    """Return the notifications command handler."""
    return CommandHandler("notifications", notifications_command)
