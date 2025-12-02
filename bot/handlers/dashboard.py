"""Dashboard command handler - opens Mini App."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CommandHandler, ContextTypes

from config import settings


async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show button to open the Mini App dashboard."""
    if not settings.webapp_enabled or not settings.webapp_url:
        await update.message.reply_text(
            "Dashboard is not configured. Set WEBAPP_URL in your environment."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="Open Dashboard",
            web_app=WebAppInfo(url=settings.webapp_url)
        )]
    ])

    await update.message.reply_text(
        "Tap the button below to open your nutrition dashboard:",
        reply_markup=keyboard
    )


def get_dashboard_handler():
    """Get the dashboard command handler."""
    return CommandHandler("dashboard", dashboard_command)
