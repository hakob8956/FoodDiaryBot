from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


HELP_TEXT = """FoodGPT - Your Nutrition Tracking Assistant

LOGGING FOOD:
- Send a photo of your meal
- Send a text description (e.g., "grilled chicken with rice")
- Send both a photo with a caption

COMMANDS:

/start - Set up your profile (weight, height, activity, goal)

/profile - View your current profile and stats

/setcalories <number> - Override your daily calorie target
  Example: /setcalories 2200

/setweight <number> - Update your weight (in kg)
  Example: /setweight 75.5

/summarize [date/range] - Get nutrition summary
  Examples:
    /summarize - today's summary
    /summarize yesterday
    /summarize this week
    /summarize 2024-11-15
    /summarize 2024-11-10 to 2024-11-15

/delete [id] - Delete a food entry
  Examples:
    /delete - show recent entries to delete
    /delete 42 - delete entry #42

/notifications - Manage daily reminders
  Examples:
    /notifications - view settings
    /notifications on - enable reminders
    /notifications off - disable reminders
    /notifications time 20 - set reminder hour (0-23)

/rawlog - Export all logs as raw JSON (for debugging)

/help - Show this help message

TIPS:
- Be consistent with logging for accurate tracking
- Include portion sizes in descriptions when possible
- The more detail you provide, the better the estimates"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(HELP_TEXT)


def get_help_handler() -> CommandHandler:
    """Return the help command handler."""
    return CommandHandler("help", help_command)
