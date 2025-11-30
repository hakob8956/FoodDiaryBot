import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.user_repo import user_repo
from database.repositories.food_log_repo import food_log_repo


async def rawlog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rawlog command - export raw JSON logs."""
    telegram_id = update.effective_user.id

    # Check if user is onboarded
    user = await user_repo.get_user(telegram_id)
    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please set up your profile first with /start"
        )
        return

    logs = await food_log_repo.get_all_logs_json(telegram_id)

    if not logs:
        await update.message.reply_text("No food logs found.")
        return

    # Format as JSON
    json_output = json.dumps(logs, indent=2, ensure_ascii=False, default=str)

    # Telegram has a 4096 character limit per message
    if len(json_output) <= 4000:
        await update.message.reply_text(f"```json\n{json_output}\n```", parse_mode="Markdown")
    else:
        # Send as file
        from io import BytesIO
        file_content = BytesIO(json_output.encode("utf-8"))
        file_content.name = "food_logs.json"
        await update.message.reply_document(
            document=file_content,
            filename="food_logs.json",
            caption=f"Your complete food log ({len(logs)} entries)"
        )


def get_rawlog_handler() -> CommandHandler:
    """Return the rawlog command handler."""
    return CommandHandler("rawlog", rawlog_command)
