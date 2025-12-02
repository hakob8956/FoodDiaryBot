"""WebApp data handler - processes commands sent from Mini App."""
import logging
from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

logger = logging.getLogger(__name__)

# Map of commands to their handler functions
COMMAND_RESPONSES = {
    '/start': "Starting profile setup... Please use /start in the chat.",
    '/profile': None,  # Will be handled dynamically
    '/setcalories': "To set calories, use: /setcalories <number>\nExample: /setcalories 2000",
    '/setweight': "To set weight, use: /setweight <number>\nExample: /setweight 75",
    '/summarize': None,  # Will be handled dynamically
    '/delete': None,  # Will be handled dynamically
    '/notifications': None,  # Will be handled dynamically
    '/rawlog': None,  # Will be handled dynamically
    '/help': None,  # Will be handled dynamically
}


async def webapp_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from the Mini App via sendData."""
    if not update.effective_message or not update.effective_message.web_app_data:
        return

    data = update.effective_message.web_app_data.data
    logger.info(f"Received webapp data: {data}")

    # Check if it's a command
    if data.startswith('/'):
        command = data.split()[0]  # Get just the command part

        # Send acknowledgment and instruction
        await update.effective_message.reply_text(
            f"Command received: {command}\n\n"
            f"Please type {command} in the chat to execute it."
        )
    else:
        await update.effective_message.reply_text(f"Received: {data}")


def get_webapp_data_handler():
    """Get the webapp data message handler."""
    return MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA,
        webapp_data_handler
    )
