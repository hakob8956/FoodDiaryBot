import logging
import asyncio
import threading
from telegram import Update
from telegram.ext import Application, ContextTypes

from config import settings
from database.migrations import run_migrations
from bot.handlers.start import get_start_conversation_handler
from bot.handlers.help import get_help_handler
from bot.handlers.profile import get_profile_handlers
from bot.handlers.food_log import get_food_log_handler
from bot.handlers.summary import get_summary_handler
from bot.handlers.rawlog import get_rawlog_handler
from bot.handlers.delete import get_delete_handler
from bot.handlers.notifications import get_notifications_handler
from bot.handlers.dashboard import get_dashboard_handler
from bot.handlers.debug import get_debug_handlers
from services.reminder_service import check_and_send_reminders


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level.upper())
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all uncaught exceptions."""
    logger.error(f"Exception while handling update: {context.error}", exc_info=context.error)

    # Try to notify user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again."
            )
        except Exception:
            pass  # Ignore if we can't send the error message


async def post_init(application: Application):
    """Run after application is initialized but before polling starts."""
    logger.info("Running database migrations...")
    await run_migrations()
    logger.info("Database ready.")

    # Schedule reminder job (runs every hour)
    if application.job_queue:
        application.job_queue.run_repeating(
            check_and_send_reminders,
            interval=3600,  # Every hour
            first=60,  # First run after 60 seconds
            name="daily_reminder_check"
        )
        logger.info("Daily reminder job scheduled (hourly)")


def run_api_server():
    """Run the Mini App API server in a separate thread."""
    import uvicorn
    from webapp.api.server import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.webapp_port,
        log_level="info"
    )


def main():
    """Start the bot and optionally the Mini App API server."""
    logger.info("Starting FoodGPT bot...")

    # Start Mini App API server if enabled
    if settings.webapp_enabled:
        logger.info(f"Starting Mini App API server on port {settings.webapp_port}...")
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        logger.info("Mini App API server started")

    # Create application
    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    # Add handlers
    # Start conversation handler (must be first to handle onboarding properly)
    application.add_handler(get_start_conversation_handler())

    # Command handlers
    application.add_handler(get_help_handler())
    for handler in get_profile_handlers():
        application.add_handler(handler)
    application.add_handler(get_summary_handler())
    application.add_handler(get_rawlog_handler())
    application.add_handler(get_delete_handler())
    application.add_handler(get_notifications_handler())
    application.add_handler(get_dashboard_handler())

    # Debug handlers (remove in production)
    for handler in get_debug_handlers():
        application.add_handler(handler)

    # Food logging handler (photos and text messages)
    # This should be last to not interfere with conversation handlers
    application.add_handler(get_food_log_handler())

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Bot is ready! Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
