"""
Raw log export handler.

Handles /rawlog command for exporting food logs as JSON.
"""

import json
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.repositories.food_log_repo import food_log_repo
from database.models import User
from constants import TELEGRAM_SAFE_MESSAGE_CHARS
from bot.messages import Messages
from bot.utils.decorators import require_onboarding


@require_onboarding
async def rawlog_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /rawlog command - export raw JSON logs."""
    logs = await food_log_repo.get_all_logs_json(user.telegram_id)

    if not logs:
        await update.message.reply_text(Messages.RAWLOG_NO_DATA)
        return

    # Format as JSON
    json_output = json.dumps(logs, indent=2, ensure_ascii=False, default=str)

    # Check message length limit
    if len(json_output) <= TELEGRAM_SAFE_MESSAGE_CHARS:
        await update.message.reply_text(
            f"```json\n{json_output}\n```",
            parse_mode="Markdown"
        )
    else:
        # Send as file
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
