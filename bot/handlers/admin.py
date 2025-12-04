"""
Admin command handlers.

Provides admin-only commands like broadcast messaging.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import settings
from database.repositories.user_repo import user_repo

logger = logging.getLogger(__name__)


async def broadcast_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle /broadcast command - send message to all users.

    Usage: /broadcast <message>
    Only works for admin user.
    """
    # Check if user is admin
    if update.effective_user.id != settings.admin_user_id:
        return

    # Get message text
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)

    # Get all users
    users = await user_repo.get_all_users()

    if not users:
        await update.message.reply_text("No users found.")
        return

    # Send to all users
    success_count = 0
    failed_count = 0

    await update.message.reply_text(f"Sending to {len(users)} users...")

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text=message
            )
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {user.telegram_id}: {e}")
            failed_count += 1

    await update.message.reply_text(
        f"Broadcast complete.\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {failed_count}"
    )


def get_admin_handler() -> CommandHandler:
    """Return the broadcast command handler."""
    return CommandHandler("broadcast", broadcast_command)
