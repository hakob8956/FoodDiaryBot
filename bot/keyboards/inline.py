from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_sex_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting biological sex."""
    buttons = [
        [
            InlineKeyboardButton("Male", callback_data="sex:male"),
            InlineKeyboardButton("Female", callback_data="sex:female")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting activity level."""
    buttons = [
        [InlineKeyboardButton("Sedentary (little/no exercise)", callback_data="activity:sedentary")],
        [InlineKeyboardButton("Lightly Active (1-3 days/week)", callback_data="activity:lightly_active")],
        [InlineKeyboardButton("Moderately Active (3-5 days/week)", callback_data="activity:moderately_active")],
        [InlineKeyboardButton("Very Active (6-7 days/week)", callback_data="activity:very_active")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_goal_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting fitness goal."""
    buttons = [
        [InlineKeyboardButton("Lose Weight", callback_data="goal:lose")],
        [InlineKeyboardButton("Maintain Weight", callback_data="goal:maintain")],
        [InlineKeyboardButton("Gain Weight", callback_data="goal:gain")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for confirming profile setup."""
    buttons = [
        [
            InlineKeyboardButton("Confirm", callback_data="confirm:yes"),
            InlineKeyboardButton("Start Over", callback_data="confirm:no")
        ]
    ]
    return InlineKeyboardMarkup(buttons)
