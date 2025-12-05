"""
Centralized user-facing messages.

All bot messages should be defined here to ensure consistency
and make localization easier in the future.
"""


class Messages:
    """User-facing message strings."""

    # =========================================================================
    # GENERAL
    # =========================================================================
    ONBOARDING_REQUIRED = (
        "Please set up your profile first with /start"
    )
    ANALYZING_FOOD = "Analyzing..."
    ANALYSIS_ERROR = "Sorry, I couldn't analyze this food. Please try again."
    UNKNOWN_ERROR = "An error occurred. Please try again later."

    # =========================================================================
    # ONBOARDING
    # =========================================================================
    WELCOME_BACK = (
        "Welcome back, {first_name}!\n\n"
        "Your profile is already set up.\n"
        "Daily target: {daily_target} kcal\n\n"
        "Send a food photo or description to log a meal.\n"
        "Use /profile to view your stats or /help for commands."
    )

    ONBOARDING_START = (
        "Hi {first_name}! I'm FoodGPT, your nutrition tracking assistant.\n\n"
        "Let's set up your profile to calculate your daily calorie needs.\n\n"
        "What's your current weight in kg? (e.g., 75)"
    )

    ONBOARDING_WEIGHT_PROMPT = "What's your current weight in kg? (e.g., 75)"
    ONBOARDING_HEIGHT_PROMPT = "Now, what's your height in cm? (e.g., 175)"
    ONBOARDING_AGE_PROMPT = "How old are you? (e.g., 28)"
    ONBOARDING_SEX_PROMPT = "What's your biological sex? (This affects calorie calculations)"
    ONBOARDING_ACTIVITY_PROMPT = "What's your typical activity level?"
    ONBOARDING_GOAL_PROMPT = "What's your goal?"

    ONBOARDING_WEIGHT_CONFIRM = "Weight: {weight} kg\n\n" + ONBOARDING_HEIGHT_PROMPT
    ONBOARDING_HEIGHT_CONFIRM = "Height: {height} cm\n\n" + ONBOARDING_AGE_PROMPT
    ONBOARDING_AGE_CONFIRM = "Age: {age}\n\n" + ONBOARDING_SEX_PROMPT
    ONBOARDING_SEX_CONFIRM = "Sex: {sex}\n\n" + ONBOARDING_ACTIVITY_PROMPT
    ONBOARDING_ACTIVITY_CONFIRM = "Activity Level: {activity}\n\n" + ONBOARDING_GOAL_PROMPT

    ONBOARDING_SUMMARY = (
        "Profile Summary:\n\n"
        "Weight: {weight} kg\n"
        "Height: {height} cm\n"
        "Age: {age}\n"
        "Sex: {sex}\n"
        "Activity: {activity}\n"
        "Goal: {goal}\n\n"
        "Recommended Daily Calories: {daily_target} kcal\n\n"
        "Is this correct?"
    )

    ONBOARDING_RESTART = "Let's start over.\n\n" + ONBOARDING_WEIGHT_PROMPT

    ONBOARDING_COMPLETE = (
        "Profile saved!\n\n"
        "Your daily calorie target is {daily_target} kcal.\n\n"
        "You can now:\n"
        "- Send a food photo to log a meal\n"
        "- Send a text description of what you ate\n"
        "- Use /summarize to see your nutrition summary\n"
        "- Use /profile to view your stats\n"
        "- Use /help for all commands"
    )

    ONBOARDING_CANCELLED = "Onboarding cancelled. Use /start to begin again."

    WEBAPP_BUTTON_TEXT = "Open Dashboard"
    WEBAPP_PROMPT = "Open the dashboard to view your nutrition charts and calendar:"

    # =========================================================================
    # PROFILE
    # =========================================================================
    PROFILE_NOT_FOUND = "Profile not found. Use /start to set up your profile."

    PROFILE_DISPLAY = (
        "Your Profile:\n\n"
        "Weight: {weight} kg\n"
        "Height: {height} cm\n"
        "Age: {age}\n"
        "Sex: {sex}\n"
        "Activity: {activity}\n"
        "Goal: {goal}\n\n"
        "Daily Target: {daily_target} kcal"
        "{override_note}"
    )

    PROFILE_OVERRIDE_NOTE = "\n(manually set)"

    CALORIES_UPDATED = "Daily calorie target updated to {calories} kcal."
    CALORIES_INVALID = "Please provide a valid calorie amount (e.g., /setcalories 2000)"
    CALORIES_OUT_OF_RANGE = "Calorie target must be between 1000 and 10000."

    WEIGHT_UPDATED = "Weight updated to {weight} kg."
    WEIGHT_INVALID = "Please provide a valid weight (e.g., /setweight 75.5)"

    # =========================================================================
    # FOOD LOGGING
    # =========================================================================
    FOOD_LOGGED = (
        "Logged: {food_list}\n"
        "~{calories} kcal | {protein}g protein"
    )

    FOOD_PROGRESS = (
        "\n\nToday: {consumed}/{target} kcal"
    )

    FOOD_REMAINING = " ({remaining} remaining)"
    FOOD_OVER_TARGET = " ({over} over target)"

    FOOD_LOW_CONFIDENCE = "\n(estimate has higher uncertainty)"
    FOOD_ENTRY_ID = "\n\n(Entry #{entry_id} - use /delete {entry_id} to remove)"

    # =========================================================================
    # DELETE
    # =========================================================================
    DELETE_NO_LOGS = "You don't have any food logs to delete."
    DELETE_SELECT_ENTRY = (
        "Recent entries:\n\n"
        "{entries}\n\n"
        "Reply with /delete <id> to delete an entry."
    )
    DELETE_ENTRY_FORMAT = "#{id} - {time}: {items} ({calories} kcal)"
    DELETE_NOT_FOUND = "Entry #{entry_id} not found or already deleted."
    DELETE_SUCCESS = "Entry #{entry_id} deleted successfully."
    DELETE_INVALID_ID = "Please provide a valid entry ID (e.g., /delete 42)"

    # =========================================================================
    # SUMMARY
    # =========================================================================
    SUMMARY_NO_DATA = "No food logs found for this period."
    SUMMARY_PARSE_ERROR = (
        "I couldn't understand that date format.\n\n"
        "Try:\n"
        "- /summarize (today)\n"
        "- /summarize yesterday\n"
        "- /summarize this week\n"
        "- /summarize 2024-11-15\n"
        "- /summarize 2024-11-10 to 2024-11-15"
    )

    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================
    NOTIFICATIONS_STATUS = (
        "Notification Settings:\n\n"
        "Daily Reminders: {status}\n"
        "Reminder time: {hour}:00\n\n"
        "Weekly Summary: {weekly_status}\n"
        "(Sent every Monday at 9:00 AM)\n\n"
        "Commands:\n"
        "/notifications on - Enable daily reminders\n"
        "/notifications off - Disable daily reminders\n"
        "/notifications time <0-23> - Set reminder hour\n"
        "/notifications weeklysummary on - Enable weekly summaries\n"
        "/notifications weeklysummary off - Disable weekly summaries"
    )
    NOTIFICATIONS_ENABLED = "Enabled"
    NOTIFICATIONS_DISABLED = "Disabled"
    NOTIFICATIONS_ON = "Daily reminders enabled! You'll be reminded at {hour}:00."
    NOTIFICATIONS_OFF = "Daily reminders disabled."
    NOTIFICATIONS_TIME_SET = "Reminder time set to {hour}:00."
    NOTIFICATIONS_TIME_INVALID = "Please provide an hour between 0 and 23 (e.g., /notifications time 20)"
    WEEKLY_SUMMARY_ON = "Weekly summaries enabled! You'll receive a summary every Monday at 9:00 AM."
    WEEKLY_SUMMARY_OFF = "Weekly summaries disabled."

    # =========================================================================
    # RAWLOG
    # =========================================================================
    RAWLOG_NO_DATA = "No food logs found."
    RAWLOG_SUCCESS = "Here's your raw log data:"

    # =========================================================================
    # HELP
    # =========================================================================
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

/dashboard - Open the nutrition dashboard

/rawlog - Export all logs as raw JSON (for debugging)

/help - Show this help message

TIPS:
- Be consistent with logging for accurate tracking
- Include portion sizes in descriptions when possible
- The more detail you provide, the better the estimates"""
