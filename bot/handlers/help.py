"""
Help command handler.

Displays all available bot commands and usage instructions.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.messages import Messages


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(Messages.HELP_TEXT)


def get_help_handler() -> CommandHandler:
    """Return the help command handler."""
    return CommandHandler("help", help_command)
