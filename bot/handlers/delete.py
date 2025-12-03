"""
Delete food log handler.

Handles /delete command for removing food log entries.
"""

import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.food_log_repo import food_log_repo
from database.models import User
from bot.messages import Messages
from bot.utils.decorators import require_onboarding


@require_onboarding
async def delete_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /delete command - delete a food log entry."""
    telegram_id = user.telegram_id

    # Check if ID was provided
    if context.args:
        try:
            log_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(Messages.DELETE_INVALID_ID)
            return

        # Try to delete
        deleted = await food_log_repo.delete_log(telegram_id, log_id)
        if deleted:
            await update.message.reply_text(
                Messages.DELETE_SUCCESS.format(entry_id=log_id)
            )
        else:
            await update.message.reply_text(
                Messages.DELETE_NOT_FOUND.format(entry_id=log_id)
            )
        return

    # No ID provided - show recent entries
    recent_logs = await food_log_repo.get_recent_logs(telegram_id, limit=5)

    if not recent_logs:
        await update.message.reply_text(Messages.DELETE_NO_LOGS)
        return

    lines = ["Recent entries:\n"]
    for log in recent_logs:
        # Parse the analysis to get food names
        try:
            analysis = json.loads(log.analysis_json)
            items = analysis.get("items", [])
            food_names = ", ".join(item["name"] for item in items[:2])
            if len(items) > 2:
                food_names += f" +{len(items) - 2} more"
        except (json.JSONDecodeError, KeyError):
            food_names = "Unknown"

        logged_time = log.logged_at.strftime("%m/%d %H:%M") if log.logged_at else "?"
        lines.append(
            f"#{log.id} - {food_names} ({log.total_calories} kcal) - {logged_time}"
        )

    lines.append("\nTo delete, use: /delete <id>")
    lines.append("Example: /delete 42")

    await update.message.reply_text("\n".join(lines))


def get_delete_handler() -> CommandHandler:
    """Return the delete command handler."""
    return CommandHandler("delete", delete_command)
