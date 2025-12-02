from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from database.repositories.user_repo import user_repo
from services.calorie_calculator import calculate_daily_target, get_macro_targets
from utils.validators import validate_calories, validate_weight


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


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command - display user profile."""
    telegram_id = update.effective_user.id
    user = await user_repo.get_user(telegram_id)

    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "You haven't set up your profile yet.\n"
            "Use /start to begin."
        )
        return

    activity_labels = {
        "sedentary": "Sedentary",
        "lightly_active": "Lightly Active",
        "moderately_active": "Moderately Active",
        "very_active": "Very Active"
    }

    goal_labels = {
        "lose": "Lose Weight",
        "maintain": "Maintain Weight",
        "gain": "Gain Weight"
    }

    macros = get_macro_targets(user.daily_calorie_target, user.goal)

    profile_text = (
        "Your Profile:\n\n"
        f"Weight: {user.weight} kg\n"
        f"Height: {user.height} cm\n"
        f"Age: {user.age}\n"
        f"Sex: {user.sex.capitalize() if user.sex else 'Not set'}\n"
        f"Activity: {activity_labels.get(user.activity_level, user.activity_level)}\n"
        f"Goal: {goal_labels.get(user.goal, user.goal)}\n\n"
        f"Daily Calorie Target: {user.daily_calorie_target} kcal"
    )

    if user.calorie_override:
        profile_text += " (manually set)"

    profile_text += (
        f"\n\nRecommended Macros:\n"
        f"  Protein: {macros['protein_g']}g\n"
        f"  Carbs: {macros['carbs_g']}g\n"
        f"  Fat: {macros['fat_g']}g\n\n"
        "Use /setcalories to change target\n"
        "Use /setweight to update your weight"
    )

    await update.message.reply_text(profile_text, reply_markup=get_webapp_keyboard())


async def set_calories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setcalories command - override daily calorie target."""
    telegram_id = update.effective_user.id
    user = await user_repo.get_user(telegram_id)

    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please complete your profile setup first with /start"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide a calorie target.\n"
            "Example: /setcalories 2200"
        )
        return

    is_valid, calories, error = validate_calories(context.args[0])
    if not is_valid:
        await update.message.reply_text(error)
        return

    await user_repo.set_calorie_override(telegram_id, calories)

    await update.message.reply_text(
        f"Daily calorie target updated to {calories} kcal.\n\n"
        "This overrides the calculated value. To reset, update your "
        "weight or activity level via /start."
    )


async def set_weight_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setweight command - update weight and recalculate target."""
    telegram_id = update.effective_user.id
    user = await user_repo.get_user(telegram_id)

    if not user or not user.onboarding_complete:
        await update.message.reply_text(
            "Please complete your profile setup first with /start"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide your new weight in kg.\n"
            "Example: /setweight 75.5"
        )
        return

    is_valid, weight, error = validate_weight(context.args[0])
    if not is_valid:
        await update.message.reply_text(error)
        return

    old_weight = user.weight
    await user_repo.update_weight(telegram_id, weight)

    response = f"Weight updated: {old_weight} kg -> {weight} kg"

    # Recalculate target if not manually overridden
    if not user.calorie_override:
        new_target = calculate_daily_target(
            weight_kg=weight,
            height_cm=user.height,
            age=user.age,
            sex=user.sex,
            activity_level=user.activity_level,
            goal=user.goal
        )
        await user_repo.update_user(telegram_id, daily_calorie_target=new_target)
        response += f"\nNew calorie target: {new_target} kcal"
    else:
        response += f"\n(Calorie target unchanged at {user.daily_calorie_target} kcal - manually set)"

    await update.message.reply_text(response)


def get_profile_handlers() -> list[CommandHandler]:
    """Return all profile-related command handlers."""
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("setcalories", set_calories_command),
        CommandHandler("setweight", set_weight_command),
    ]
