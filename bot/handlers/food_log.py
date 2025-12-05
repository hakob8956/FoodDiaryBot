"""
Food logging handler.

Handles incoming food photos and text descriptions.
"""

from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, MessageHandler, filters

from config import settings
from database.models import User
from services.food_analyzer import food_analyzer
from services.pet_service import pet_service
from bot.messages import Messages
from bot.utils.decorators import require_onboarding
from constants import ACHIEVEMENTS

# Project root for finding pet images
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _get_app_keyboard():
    """Get Mini App button for after meal logging."""
    if not settings.webapp_url:
        return None
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="📱 Open App",
            web_app=WebAppInfo(url=settings.webapp_url)
        )
    ]])


def _get_mood_emoji(mood_value: str) -> str:
    """Get emoji for mood."""
    mood_emojis = {
        "stuffed": "🫃",
        "ecstatic": "🌟",
        "happy": "😊",
        "hungry": "😕",
        "starving": "😢",
    }
    return mood_emojis.get(mood_value, "😊")


def _format_pet_text(pet_info) -> str:
    """Format pet status as text (for normal food logs)."""
    mood_text = pet_service.get_mood_text(pet_info.mood)
    mood_emoji = _get_mood_emoji(pet_info.mood.value)
    level_text = pet_service.get_level_text(pet_info.level)

    streak_text = ""
    if pet_info.pet.current_streak > 0:
        streak_text = f" | Streak: {pet_info.pet.current_streak}d 🔥"

    return f"🐾 {pet_info.pet.pet_name} is {mood_emoji} {mood_text}! ({pet_info.calories_percent}%)\n{level_text}{streak_text}"


def _format_pet_caption(pet_info) -> str:
    """Format pet caption for photo message (on evolution)."""
    mood_text = pet_service.get_mood_text(pet_info.mood)
    level_text = pet_service.get_level_text(pet_info.level)

    streak_text = ""
    if pet_info.pet.current_streak > 0:
        streak_text = f" | Streak: {pet_info.pet.current_streak}d 🔥"

    return f"🎉 {pet_info.pet.pet_name} evolved to {level_text}!\n{mood_text} ({pet_info.calories_percent}%){streak_text}"


def _get_pet_image_path(pet_info) -> Path:
    """Get the local file path for pet image."""
    # pet_info.image_url is like "/pet/baby-happy.png"
    image_path = PROJECT_ROOT / "webapp" / "frontend" / "public" / pet_info.image_url.lstrip("/")
    return image_path


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

        # Feed the pet and check for achievements
        pet_info = await pet_service.feed_pet(user.telegram_id)

        # Format response with entry ID for easy deletion
        response = food_analyzer.format_log_response(
            analysis, progress, entry_id=food_log.id
        )

        # Add pet status text
        pet_text = _format_pet_text(pet_info)
        response += f"\n\n{pet_text}"

        # Add achievements to text if any
        if pet_info.new_achievements:
            for achievement_id in pet_info.new_achievements:
                name, desc, emoji = ACHIEVEMENTS.get(
                    achievement_id, ("Achievement", "", "🏆")
                )
                response += f"\n\n🏆 New Achievement: {emoji} {name}!"

        # Delete status message and send new one with app button
        await status_message.delete()
        await update.message.reply_text(response, reply_markup=_get_app_keyboard())

        # Send photo only on evolution or first achievement
        if pet_info.evolved or pet_info.new_achievements:
            pet_image_path = _get_pet_image_path(pet_info)
            if pet_image_path.exists():
                caption = _format_pet_caption(pet_info) if pet_info.evolved else f"🏆 {pet_info.pet.pet_name} earned a new achievement!"
                with open(pet_image_path, "rb") as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption
                    )

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
