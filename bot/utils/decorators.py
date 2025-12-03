"""
Bot handler decorators.

Provides reusable decorators for common handler functionality.
"""

from functools import wraps
from typing import Callable, Optional

from telegram import Update
from telegram.ext import ContextTypes

from database.repositories.user_repo import user_repo
from database.models import User
from bot.messages import Messages


def require_onboarding(func: Callable) -> Callable:
    """
    Decorator to ensure user has completed onboarding before accessing a handler.

    Automatically loads the user from the database and passes it to the handler
    via the `user` keyword argument.

    Usage:
        @require_onboarding
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
            # user is guaranteed to be onboarded
            ...
    """
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs
    ):
        telegram_id = update.effective_user.id
        user = await user_repo.get_user(telegram_id)

        if not user or not user.onboarding_complete:
            if update.message:
                await update.message.reply_text(Messages.ONBOARDING_REQUIRED)
            elif update.callback_query:
                await update.callback_query.answer(Messages.ONBOARDING_REQUIRED)
            return

        return await func(update, context, *args, user=user, **kwargs)

    return wrapper


def with_user(func: Callable) -> Callable:
    """
    Decorator to load user from database without requiring onboarding.

    Passes user (or None) to the handler via the `user` keyword argument.

    Usage:
        @with_user
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Optional[User]):
            if user:
                # user exists
            else:
                # no user found
    """
    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        *args,
        **kwargs
    ):
        telegram_id = update.effective_user.id
        user = await user_repo.get_user(telegram_id)
        return await func(update, context, *args, user=user, **kwargs)

    return wrapper
