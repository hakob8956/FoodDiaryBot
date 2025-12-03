"""
Summary generation handler.

Handles /summarize command for nutrition summaries.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.models import User
from services.summary_generator import summary_generator
from utils.date_parser import parse_date_input, format_date_range
from bot.messages import Messages
from bot.utils.decorators import require_onboarding


@require_onboarding
async def summarize_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /summarize command - generate nutrition summary."""
    telegram_id = user.telegram_id

    # Parse date argument
    date_arg = " ".join(context.args) if context.args else "today"

    try:
        start_date, end_date = parse_date_input(date_arg)
    except (ValueError, TypeError):
        await update.message.reply_text(Messages.SUMMARY_PARSE_ERROR)
        return

    # Send status message
    status_message = await update.message.reply_text(
        f"Generating summary for {format_date_range(start_date, end_date)}..."
    )

    try:
        summary = await summary_generator.generate_summary(
            telegram_id=telegram_id,
            start_date=start_date,
            end_date=end_date
        )

        if not summary:
            await status_message.edit_text(Messages.UNKNOWN_ERROR)
            return

        if summary["totals"]["meals_logged"] == 0:
            await status_message.edit_text(
                f"No food logged for {format_date_range(start_date, end_date)}.\n\n"
                "Send a photo or description of your food to start tracking!"
            )
            return

        response = summary_generator.format_summary_response(summary)
        await status_message.edit_text(response)

    except Exception as e:
        await status_message.edit_text(Messages.UNKNOWN_ERROR)
        raise


def get_summary_handler() -> CommandHandler:
    """Return the summary command handler."""
    return CommandHandler("summarize", summarize_command)
