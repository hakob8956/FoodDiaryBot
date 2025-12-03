"""
Profile management handlers.

Handles /profile, /setcalories, and /setweight commands.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from constants import Sex, ActivityLevel, Goal
from database.repositories.user_repo import user_repo
from database.models import User
from services.calorie_calculator import calculate_daily_target, get_macro_targets
from utils.validators import validate_calories, validate_weight
from bot.messages import Messages
from bot.labels import get_activity_label, get_goal_label, get_sex_label
from bot.utils.decorators import require_onboarding


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


@require_onboarding
async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /profile command - display user profile."""
    # Get macro targets
    macros = get_macro_targets(user.daily_calorie_target, user.goal)

    # Build profile text
    sex_label = get_sex_label(user.sex) if user.sex else "Not set"
    activity_label = get_activity_label(user.activity_level) if user.activity_level else "Not set"
    goal_label = get_goal_label(user.goal) if user.goal else "Not set"

    profile_text = (
        "Your Profile:\n\n"
        f"Weight: {user.weight} kg\n"
        f"Height: {user.height} cm\n"
        f"Age: {user.age}\n"
        f"Sex: {sex_label}\n"
        f"Activity: {activity_label}\n"
        f"Goal: {goal_label}\n\n"
        f"Daily Calorie Target: {user.daily_calorie_target} kcal"
    )

    if user.calorie_override:
        profile_text += Messages.PROFILE_OVERRIDE_NOTE

    profile_text += (
        f"\n\nRecommended Macros:\n"
        f"  Protein: {macros.protein_g}g\n"
        f"  Carbs: {macros.carbs_g}g\n"
        f"  Fat: {macros.fat_g}g\n\n"
        "Use /setcalories to change target\n"
        "Use /setweight to update your weight"
    )

    await update.message.reply_text(profile_text, reply_markup=get_webapp_keyboard())


@require_onboarding
async def set_calories_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /setcalories command - override daily calorie target."""
    if not context.args:
        await update.message.reply_text(Messages.CALORIES_INVALID)
        return

    is_valid, calories, error = validate_calories(context.args[0])
    if not is_valid:
        await update.message.reply_text(error)
        return

    await user_repo.set_calorie_override(user.telegram_id, calories)

    await update.message.reply_text(
        Messages.CALORIES_UPDATED.format(calories=calories) +
        "\n\nThis overrides the calculated value. To reset, update your "
        "weight or activity level via /start."
    )


@require_onboarding
async def set_weight_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: User
) -> None:
    """Handle /setweight command - update weight and recalculate target."""
    if not context.args:
        await update.message.reply_text(Messages.WEIGHT_INVALID)
        return

    is_valid, weight, error = validate_weight(context.args[0])
    if not is_valid:
        await update.message.reply_text(error)
        return

    old_weight = user.weight
    await user_repo.update_weight(user.telegram_id, weight)

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
        await user_repo.update_user(user.telegram_id, daily_calorie_target=new_target)
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
