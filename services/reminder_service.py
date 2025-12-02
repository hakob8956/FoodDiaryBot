import logging
from datetime import datetime
from telegram.ext import ContextTypes

from services.feature_flags import feature_flags
from database.repositories.user_repo import user_repo
from database.repositories.food_log_repo import food_log_repo

logger = logging.getLogger(__name__)

REMINDER_MESSAGE = """Hey! You haven't logged any food today.

Send me a photo of your meal or a text description to track your nutrition!

(Use /notifications off to disable these reminders)"""


async def check_and_send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    Job that runs every hour to send reminder notifications.

    Checks the 'daily_reminder' feature flag and sends reminders to users
    who haven't logged food today and have the current hour set as their
    reminder time.
    """
    # Check if feature is enabled via GrowthBook
    if not feature_flags.is_enabled("daily_reminder", default=False):
        return

    current_hour = datetime.now().hour
    logger.info(f"Checking for users to remind at hour {current_hour}")

    try:
        # Get users who should receive reminder at this hour
        users = await user_repo.get_users_for_reminder(current_hour)

        if not users:
            logger.debug(f"No users to remind at hour {current_hour}")
            return

        sent_count = 0
        for user in users:
            # Double-check they haven't logged today
            has_logged = await food_log_repo.has_logged_today(user.telegram_id)
            if has_logged:
                continue

            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=REMINDER_MESSAGE
                )
                await user_repo.update_last_reminder(user.telegram_id)
                sent_count += 1
                logger.info(f"Sent reminder to user {user.telegram_id}")

            except Exception as e:
                logger.warning(f"Failed to send reminder to {user.telegram_id}: {e}")

        logger.info(f"Sent {sent_count} reminders at hour {current_hour}")

    except Exception as e:
        logger.error(f"Error in reminder job: {e}", exc_info=True)
