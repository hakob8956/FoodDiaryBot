from typing import Tuple, Optional


def validate_weight(value: str) -> Tuple[bool, Optional[float], str]:
    """
    Validate weight input (in kg).

    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    try:
        weight = float(value.replace(",", "."))
        if weight < 20:
            return False, None, "Weight seems too low. Please enter at least 20 kg."
        if weight > 500:
            return False, None, "Weight seems too high. Please enter at most 500 kg."
        return True, weight, ""
    except ValueError:
        return False, None, "Please enter a valid number for weight (e.g., 75 or 75.5)."


def validate_height(value: str) -> Tuple[bool, Optional[float], str]:
    """
    Validate height input (in cm).

    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    try:
        height = float(value.replace(",", "."))
        if height < 50:
            return False, None, "Height seems too low. Please enter at least 50 cm."
        if height > 300:
            return False, None, "Height seems too high. Please enter at most 300 cm."
        return True, height, ""
    except ValueError:
        return False, None, "Please enter a valid number for height (e.g., 175 or 175.5)."


def validate_age(value: str) -> Tuple[bool, Optional[int], str]:
    """
    Validate age input.

    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    try:
        age = int(value)
        if age < 10:
            return False, None, "Age must be at least 10 years."
        if age > 120:
            return False, None, "Age must be at most 120 years."
        return True, age, ""
    except ValueError:
        return False, None, "Please enter a valid whole number for age (e.g., 25)."


def validate_calories(value: str) -> Tuple[bool, Optional[int], str]:
    """
    Validate calorie target input.

    Returns:
        Tuple of (is_valid, parsed_value, error_message)
    """
    try:
        calories = int(value)
        if calories < 800:
            return False, None, "Calorie target should be at least 800 for safety."
        if calories > 10000:
            return False, None, "Calorie target seems too high. Maximum is 10,000."
        return True, calories, ""
    except ValueError:
        return False, None, "Please enter a valid whole number for calories (e.g., 2000)."
