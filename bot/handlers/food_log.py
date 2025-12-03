"""
Food logging handler.

Handles incoming food photos and text descriptions.
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from database.models import User
from services.food_analyzer import food_analyzer
from bot.messages import Messages
from bot.utils.decorators import require_onboarding


@require_onboarding
async def handle_food_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle incoming food photos or text descriptions."""
    # Extract message content
    message = update.message
    text_description = message.caption or message.text
    photo = message.photo[-1] if message.photo else None  # Get highest resolution

    # Must have at least a photo or text
    if not photo and not text_description:
        await update.message.reply_text(
            "Please send a photo of your food, a text description, or both."
        )
        return

    # Download photo if present
    image_bytes = None
    photo_file_id = None
    if photo:
        photo_file_id = photo.file_id
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

    # Send "analyzing" message
    status_message = await update.message.reply_text(Messages.ANALYZING_FOOD)

    try:
        # Analyze and log
        analysis, food_log = await food_analyzer.analyze_and_log(
            telegram_id=user.telegram_id,
            text_description=text_description,
            image_bytes=bytes(image_bytes) if image_bytes else None,
            photo_file_id=photo_file_id
        )

        # Get daily progress
        progress = await food_analyzer.get_daily_progress(user.telegram_id)

        # Format response with entry ID for easy deletion
        response = food_analyzer.format_log_response(
            analysis, progress, entry_id=food_log.id
        )

        await status_message.edit_text(response)

    except Exception as e:
        error_msg = Messages.ANALYSIS_ERROR
        if "json" in str(e).lower():
            error_msg += " (Analysis format error)"

        await status_message.edit_text(error_msg)
        raise  # Re-raise for logging


def get_food_log_handler() -> MessageHandler:
    """Return the food logging message handler."""
    # Handle photos (with or without caption) and text messages
    return MessageHandler(
        (filters.PHOTO | (filters.TEXT & ~filters.COMMAND)),
        handle_food_message
    )
