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


# Conversation states
WEIGHT, HEIGHT, AGE, SEX, ACTIVITY, GOAL, CONFIRM = range(7)


def get_webapp_keyboard():
    """Get keyboard with Mini App button if configured."""
    if not settings.webapp_url:
        return None

    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="Open Dashboard",
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
            f"Welcome back, {user.first_name}!\n\n"
            f"Your profile is already set up.\n"
            f"Daily target: {existing_user.daily_calorie_target} kcal\n\n"
            "Send a food photo or description to log a meal.\n"
            "Use /profile to view your stats or /help for commands.",
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
        f"Hi {user.first_name}! I'm FoodGPT, your nutrition tracking assistant.\n\n"
        "Let's set up your profile to calculate your daily calorie needs.\n\n"
        "What's your current weight in kg? (e.g., 75)"
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
        f"Weight: {weight} kg\n\n"
        "Now, what's your height in cm? (e.g., 175)"
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
        f"Height: {height} cm\n\n"
        "How old are you? (e.g., 28)"
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
        f"Age: {age}\n\n"
        "What's your biological sex? (This affects calorie calculations)",
        reply_markup=get_sex_keyboard()
    )
    return SEX


async def receive_sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process sex selection."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    sex = query.data.split(":")[1]

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["sex"] = sex
    state.current_step = "activity"
    await user_repo.save_onboarding_state(state)

    await query.edit_message_text(
        f"Sex: {sex.capitalize()}\n\n"
        "What's your typical activity level?",
        reply_markup=get_activity_keyboard()
    )
    return ACTIVITY


async def receive_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process activity level selection."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    activity = query.data.split(":")[1]

    activity_labels = {
        "sedentary": "Sedentary",
        "lightly_active": "Lightly Active",
        "moderately_active": "Moderately Active",
        "very_active": "Very Active"
    }

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["activity_level"] = activity
    state.current_step = "goal"
    await user_repo.save_onboarding_state(state)

    await query.edit_message_text(
        f"Activity Level: {activity_labels.get(activity, activity)}\n\n"
        "What's your goal?",
        reply_markup=get_goal_keyboard()
    )
    return GOAL


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process goal selection and show confirmation."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    goal = query.data.split(":")[1]

    goal_labels = {
        "lose": "Lose Weight",
        "maintain": "Maintain Weight",
        "gain": "Gain Weight"
    }

    state = await user_repo.get_onboarding_state(telegram_id)
    state.collected_data["goal"] = goal
    state.current_step = "confirm"
    await user_repo.save_onboarding_state(state)

    # Calculate target
    data = state.collected_data
    daily_target = calculate_daily_target(
        weight_kg=data["weight"],
        height_cm=data["height"],
        age=data["age"],
        sex=data["sex"],
        activity_level=data["activity_level"],
        goal=data["goal"]
    )
    state.collected_data["daily_target"] = daily_target
    await user_repo.save_onboarding_state(state)

    activity_labels = {
        "sedentary": "Sedentary",
        "lightly_active": "Lightly Active",
        "moderately_active": "Moderately Active",
        "very_active": "Very Active"
    }

    summary = (
        "Profile Summary:\n\n"
        f"Weight: {data['weight']} kg\n"
        f"Height: {data['height']} cm\n"
        f"Age: {data['age']}\n"
        f"Sex: {data['sex'].capitalize()}\n"
        f"Activity: {activity_labels.get(data['activity_level'], data['activity_level'])}\n"
        f"Goal: {goal_labels.get(goal, goal)}\n\n"
        f"Recommended Daily Calories: {daily_target} kcal\n\n"
        "Is this correct?"
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
        await query.edit_message_text(
            "Let's start over.\n\nWhat's your current weight in kg?"
        )
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
    await user_repo.clear_onboarding_state(telegram_id)

    await query.edit_message_text(
        f"Profile saved!\n\n"
        f"Your daily calorie target is {data['daily_target']} kcal.\n\n"
        "You can now:\n"
        "- Send a food photo to log a meal\n"
        "- Send a text description of what you ate\n"
        "- Use /summarize to see your nutrition summary\n"
        "- Use /profile to view your stats\n"
        "- Use /help for all commands"
    )

    # Send webapp button in separate message (WebApp buttons need a new message)
    webapp_keyboard = get_webapp_keyboard()
    if webapp_keyboard:
        await context.bot.send_message(
            chat_id=telegram_id,
            text="Open the dashboard to view your nutrition charts and calendar:",
            reply_markup=webapp_keyboard
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the onboarding process."""
    await update.message.reply_text(
        "Onboarding cancelled. Use /start to begin again."
    )
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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
