from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from datetime import date

from database.repositories.user_repo import user_repo
from services.summary_generator import summary_generator
from utils.date_parser import parse_date_input, format_date_range


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /summarize command - generate nutrition summary."""
    telegram_id = update.effective_user.id

    # Check if user is onboarded
    user = await user_repo.get_user(telegram_id)
    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please set up your profile first with /start"
        )
        return

    # Parse date argument
    date_arg = " ".join(context.args) if context.args else "today"
    start_date, end_date = parse_date_input(date_arg)

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
            await status_message.edit_text("Unable to generate summary.")
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
        await status_message.edit_text(
            "Sorry, couldn't generate the summary. Please try again."
        )
        raise


def get_summary_handler() -> CommandHandler:
    """Return the summary command handler."""
    return CommandHandler("summarize", summarize_command)
