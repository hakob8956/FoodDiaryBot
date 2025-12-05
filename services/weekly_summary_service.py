"""
Weekly summary notification service.

Sends automated weekly nutrition summaries to users every Monday morning.
"""

import logging
from datetime import date, datetime, timedelta
from telegram.ext import ContextTypes

from services.feature_flags import feature_flags
from services.summary_generator import summary_generator
from database.repositories.user_repo import user_repo
from constants import WEEKLY_SUMMARY_DAY, WEEKLY_SUMMARY_HOUR

logger = logging.getLogger(__name__)

WEEKLY_SUMMARY_HEADER = """📊 Weekly Nutrition Summary

Here's how you did last week:

"""

WEEKLY_SUMMARY_FOOTER = """

(Use /notifications weeklysummary off to disable these summaries)"""


def get_last_week_dates() -> tuple[date, date]:
    """Get the start and end dates for the previous week (Mon-Sun)."""
    today = date.today()
    # Find last Monday
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    last_monday = this_monday - timedelta(days=7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


async def send_weekly_summaries(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job that runs every hour to send weekly summary notifications.

    Checks if it's Monday at the configured hour and sends summaries
    to eligible users.
    """
    # Check if feature is enabled via GrowthBook
    if not feature_flags.is_enabled("weekly_summary", default=True):
        return

    now = datetime.now()
    current_day = now.weekday()  # 0 = Monday
    current_hour = now.hour

    # Only run on Monday at the configured hour
    if current_day != WEEKLY_SUMMARY_DAY or current_hour != WEEKLY_SUMMARY_HOUR:
        return

    logger.info("Running weekly summary job...")

    try:
        # Get users eligible for weekly summary
        users = await user_repo.get_users_for_weekly_summary()

        if not users:
            logger.debug("No users eligible for weekly summary")
            return

        start_date, end_date = get_last_week_dates()
        sent_count = 0

        for user in users:
            try:
                # Generate the summary for last week
                summary = await summary_generator.generate_summary(
                    telegram_id=user.telegram_id,
                    start_date=start_date,
                    end_date=end_date
                )

                if not summary or summary["totals"]["meals_logged"] == 0:
                    # Skip users with no data last week
                    logger.debug(f"No data for user {user.telegram_id}, skipping")
                    continue

                # Format the summary
                formatted_summary = summary_generator.format_summary_response(summary)
                message = WEEKLY_SUMMARY_HEADER + formatted_summary + WEEKLY_SUMMARY_FOOTER

                # Send the message
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message
                )

                # Update last sent timestamp
                await user_repo.update_last_weekly_summary(user.telegram_id)
                sent_count += 1
                logger.info(f"Sent weekly summary to user {user.telegram_id}")

            except Exception as e:
                logger.warning(f"Failed to send weekly summary to {user.telegram_id}: {e}")

        logger.info(f"Sent {sent_count} weekly summaries")

    except Exception as e:
        logger.error(f"Error in weekly summary job: {e}", exc_info=True)
