"""
Display labels for enums and data.

Provides human-readable labels for enum values used in the UI.
"""

from constants import ActivityLevel, Goal, Sex


# Activity level display labels
ACTIVITY_LABELS: dict[ActivityLevel, str] = {
    ActivityLevel.SEDENTARY: "Sedentary",
    ActivityLevel.LIGHTLY_ACTIVE: "Lightly Active",
    ActivityLevel.MODERATELY_ACTIVE: "Moderately Active",
    ActivityLevel.VERY_ACTIVE: "Very Active",
}

# Activity level with descriptions (for buttons)
ACTIVITY_LABELS_FULL: dict[ActivityLevel, str] = {
    ActivityLevel.SEDENTARY: "Sedentary (little/no exercise)",
    ActivityLevel.LIGHTLY_ACTIVE: "Lightly Active (1-3 days/week)",
    ActivityLevel.MODERATELY_ACTIVE: "Moderately Active (3-5 days/week)",
    ActivityLevel.VERY_ACTIVE: "Very Active (6-7 days/week)",
}

# Goal display labels
GOAL_LABELS: dict[Goal, str] = {
    Goal.LOSE: "Lose Weight",
    Goal.MAINTAIN: "Maintain Weight",
    Goal.GAIN: "Gain Weight",
    Goal.GAIN_MUSCLES: "Build Muscle",
}

# Sex display labels
SEX_LABELS: dict[Sex, str] = {
    Sex.MALE: "Male",
    Sex.FEMALE: "Female",
}


def get_activity_label(activity: ActivityLevel, full: bool = False) -> str:
    """Get display label for activity level."""
    if full:
        return ACTIVITY_LABELS_FULL.get(activity, str(activity))
    return ACTIVITY_LABELS.get(activity, str(activity))


def get_goal_label(goal: Goal) -> str:
    """Get display label for goal."""
    return GOAL_LABELS.get(goal, str(goal))


def get_sex_label(sex: Sex) -> str:
    """Get display label for sex."""
    return SEX_LABELS.get(sex, str(sex))
