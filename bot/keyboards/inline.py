"""
Inline keyboard builders.

Provides keyboard markup generators for inline button interactions.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from constants import Sex, ActivityLevel, Goal
from bot.labels import SEX_LABELS, ACTIVITY_LABELS_FULL, GOAL_LABELS


def get_sex_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting biological sex."""
    buttons = [[
        InlineKeyboardButton(
            SEX_LABELS[Sex.MALE],
            callback_data=f"sex:{Sex.MALE.value}"
        ),
        InlineKeyboardButton(
            SEX_LABELS[Sex.FEMALE],
            callback_data=f"sex:{Sex.FEMALE.value}"
        )
    ]]
    return InlineKeyboardMarkup(buttons)


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting activity level."""
    buttons = [
        [InlineKeyboardButton(
            ACTIVITY_LABELS_FULL[level],
            callback_data=f"activity:{level.value}"
        )]
        for level in ActivityLevel
    ]
    return InlineKeyboardMarkup(buttons)


def get_goal_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting fitness goal."""
    buttons = [
        [InlineKeyboardButton(
            GOAL_LABELS[goal],
            callback_data=f"goal:{goal.value}"
        )]
        for goal in Goal
    ]
    return InlineKeyboardMarkup(buttons)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for confirming profile setup."""
    buttons = [[
        InlineKeyboardButton("Confirm", callback_data="confirm:yes"),
        InlineKeyboardButton("Start Over", callback_data="confirm:no")
    ]]
    return InlineKeyboardMarkup(buttons)


def get_delete_confirmation_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    """Keyboard for confirming entry deletion."""
    buttons = [[
        InlineKeyboardButton(
            "Yes, delete",
            callback_data=f"delete_confirm:{entry_id}"
        ),
        InlineKeyboardButton(
            "Cancel",
            callback_data="delete_cancel"
        )
    ]]
    return InlineKeyboardMarkup(buttons)
