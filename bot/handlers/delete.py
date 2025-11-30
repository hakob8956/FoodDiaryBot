import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.user_repo import user_repo
from database.repositories.food_log_repo import food_log_repo


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete command - delete a food log entry."""
    telegram_id = update.effective_user.id

    # Check if user is onboarded
    user = await user_repo.get_user(telegram_id)
    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please set up your profile first with /start"
        )
        return

    # Check if ID was provided
    if context.args:
        try:
            log_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "Invalid ID. Use /delete <number> or just /delete to see recent entries."
            )
            return

        # Try to delete
        deleted = await food_log_repo.delete_log(telegram_id, log_id)
        if deleted:
            await update.message.reply_text(f"Entry #{log_id} deleted.")
        else:
            await update.message.reply_text(
                f"Entry #{log_id} not found or doesn't belong to you."
            )
        return

    # No ID provided - show recent entries
    recent_logs = await food_log_repo.get_recent_logs(telegram_id, limit=5)

    if not recent_logs:
        await update.message.reply_text("No food entries to delete.")
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
        except:
            food_names = "Unknown"

        logged_time = log.logged_at.strftime("%m/%d %H:%M") if log.logged_at else "?"
        lines.append(f"#{log.id} - {food_names} ({log.total_calories} kcal) - {logged_time}")

    lines.append("\nTo delete, use: /delete <id>")
    lines.append("Example: /delete 42")

    await update.message.reply_text("\n".join(lines))


def get_delete_handler() -> CommandHandler:
    """Return the delete command handler."""
    return CommandHandler("delete", delete_command)
