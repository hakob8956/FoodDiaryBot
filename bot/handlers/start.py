"""
Start and onboarding handler.

Handles /start command and multi-step onboarding conversation.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from config import settings
from constants import Sex, ActivityLevel, Goal
from database.repositories.user_repo import user_repo
from database.models import OnboardingState
from services.calorie_calculator import calculate_daily_target
from utils.validators import validate_weight, validate_height, validate_age
from bot.keyboards.inline import (
    get_sex_keyboard,
    get_activity_keyboard,
    get_goal_keyboard,
    get_confirmation_keyboard
)
from bot.messages import Messages
from bot.labels import get_activity_label, get_goal_label, get_sex_label


# Conversation states
WEIGHT, HEIGHT, AGE, SEX, ACTIVITY, GOAL, CONFIRM, PET_NAME = range(8)


def get_webapp_keyboard():
    """Get keyboard with Mini App button if configured."""
    if not settings.webapp_url:
        return None

    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text=Messages.WEBAPP_BUTTON_TEXT,
            web_app=WebAppInfo(url=settings.webapp_url)
        )
    ]])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - begin onboarding."""
    user = update.effective_user
    telegram_id = user.id

    # Create or update user
    await user_repo.create_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name
    )

    # Check if already onboarded
    existing_user = await user_repo.get_user(telegram_id)
    if existing_user and existing_user.onboarding_complete:
        await update.message.reply_text(
            Messages.WELCOME_BACK.format(
                first_name=user.first_name,
                daily_target=existing_user.daily_calorie_target
            ),
            reply_markup=get_webapp_keyboard()
        )
        return ConversationHandler.END

    # Initialize onboarding state
    state = OnboardingState(
        telegram_id=telegram_id,
        current_step="weight",
        collected_data={}
    )
    await user_repo.save_onboarding_state(state)

    await update.message.reply_text(
        Messages.ONBOARDING_START.format(first_name=user.first_name)
    )
    return WEIGHT


async def receive_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process weight input."""
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    is_valid, weight, error = validate_weight(text)
    if not is_valid:
        await update.message.reply_text(error)
        return WEIGHT

    # Save to state
    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["weight"] = weight
    state.current_step = "height"
    await user_repo.save_onboarding_state(state)

    await update.message.reply_text(
        Messages.ONBOARDING_WEIGHT_CONFIRM.format(weight=weight)
    )
    return HEIGHT


async def receive_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process height input."""
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    is_valid, height, error = validate_height(text)
    if not is_valid:
        await update.message.reply_text(error)
        return HEIGHT

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["height"] = height
    state.current_step = "age"
    await user_repo.save_onboarding_state(state)

    await update.message.reply_text(
        Messages.ONBOARDING_HEIGHT_CONFIRM.format(height=height)
    )
    return AGE


async def receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process age input."""
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    is_valid, age, error = validate_age(text)
    if not is_valid:
        await update.message.reply_text(error)
        return AGE

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["age"] = age
    state.current_step = "sex"
    await user_repo.save_onboarding_state(state)

    await update.message.reply_text(
        Messages.ONBOARDING_AGE_CONFIRM.format(age=age),
        reply_markup=get_sex_keyboard()
    )
    return SEX


async def receive_sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process sex selection."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    sex_value = query.data.split(":")[1]
    sex = Sex(sex_value)

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["sex"] = sex_value
    state.current_step = "activity"
    await user_repo.save_onboarding_state(state)

    await query.edit_message_text(
        Messages.ONBOARDING_SEX_CONFIRM.format(sex=get_sex_label(sex)),
        reply_markup=get_activity_keyboard()
    )
    return ACTIVITY


async def receive_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process activity level selection."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    activity_value = query.data.split(":")[1]
    activity = ActivityLevel(activity_value)

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["activity_level"] = activity_value
    state.current_step = "goal"
    await user_repo.save_onboarding_state(state)

    await query.edit_message_text(
        Messages.ONBOARDING_ACTIVITY_CONFIRM.format(
            activity=get_activity_label(activity)
        ),
        reply_markup=get_goal_keyboard()
    )
    return GOAL


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process goal selection and show confirmation."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    goal_value = query.data.split(":")[1]
    goal = Goal(goal_value)

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["goal"] = goal_value
    state.current_step = "confirm"
    await user_repo.save_onboarding_state(state)

    # Calculate target
    data = state.collected_data
    daily_target = calculate_daily_target(
        weight_kg=data["weight"],
        height_cm=data["height"],
        age=data["age"],
        sex=Sex(data["sex"]),
        activity_level=ActivityLevel(data["activity_level"]),
        goal=goal
    )
    state.collected_data["daily_target"] = daily_target
    await user_repo.save_onboarding_state(state)

    summary = Messages.ONBOARDING_SUMMARY.format(
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        sex=get_sex_label(Sex(data["sex"])),
        activity=get_activity_label(ActivityLevel(data["activity_level"])),
        goal=get_goal_label(goal),
        daily_target=daily_target
    )

    await query.edit_message_text(summary, reply_markup=get_confirmation_keyboard())
    return CONFIRM


async def confirm_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle profile confirmation."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    choice = query.data.split(":")[1]

    if choice == "no":
        # Start over
        state = OnboardingState(
            telegram_id=telegram_id,
            current_step="weight",
            collected_data={}
        )
        await user_repo.save_onboarding_state(state)
        await query.edit_message_text(Messages.ONBOARDING_RESTART)
        return WEIGHT

    # Save profile
    state = await user_repo.get_onboarding_state(telegram_id)
    data = state.collected_data

    await user_repo.update_user(
        telegram_id,
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        sex=data["sex"],
        activity_level=data["activity_level"],
        goal=data["goal"]
    )
    await user_repo.set_onboarding_complete(telegram_id, data["daily_target"])

    await query.edit_message_text(
        "Profile saved! Your daily target is {daily_target} kcal.\n\n"
        "🐾 One more thing! Let's name your pet companion.\n\n"
        "Your pet will react to your eating habits and grow as you log meals!\n\n"
        "What would you like to name your pet? (or send 'skip' to use default name 'Nibbles')".format(
            daily_target=data["daily_target"]
        )
    )
    return PET_NAME


async def receive_pet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process pet name input."""
    from database.repositories.pet_repo import pet_repo
    from pathlib import Path

    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    # Get or create pet
    pet = await pet_repo.get_or_create_pet(telegram_id)

    # Set pet name
    if text.lower() != "skip" and len(text) <= 20 and len(text) >= 1:
        await pet_repo.rename_pet(telegram_id, text)
        pet_name = text
    else:
        pet_name = pet.pet_name  # Default "Nibbles"

    # Clear onboarding state
    await user_repo.clear_onboarding_state(telegram_id)

    # Send pet photo with welcome message
    from services.pet_service import pet_service
    pet_info = await pet_service.get_pet_info(telegram_id)

    PROJECT_ROOT = Path(__file__).parent.parent.parent
    image_path = PROJECT_ROOT / "webapp" / "frontend" / "public" / pet_info.image_url.lstrip("/")

    caption = (
        f"🎉 Meet {pet_name}!\n\n"
        f"Your pet starts as an Egg and will hatch after 2 meals!\n\n"
        f"Just send a food photo or text to log meals.\n"
        f"{pet_name} will react to your eating habits! 🚀"
    )

    if image_path.exists():
        with open(image_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=caption)
    else:
        await update.message.reply_text(caption)

    # Send webapp button
    webapp_keyboard = get_webapp_keyboard()
    if webapp_keyboard:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=Messages.WEBAPP_PROMPT,
            reply_markup=webapp_keyboard
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the onboarding process."""
    await update.message.reply_text(Messages.ONBOARDING_CANCELLED)
    return ConversationHandler.END


def get_start_conversation_handler() -> ConversationHandler:
    """Create and return the start conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_height)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_age)],
            SEX: [CallbackQueryHandler(receive_sex, pattern="^sex:")],
            ACTIVITY: [CallbackQueryHandler(receive_activity, pattern="^activity:")],
            GOAL: [CallbackQueryHandler(receive_goal, pattern="^goal:")],
            CONFIRM: [CallbackQueryHandler(confirm_profile, pattern="^confirm:")],
            PET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pet_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
