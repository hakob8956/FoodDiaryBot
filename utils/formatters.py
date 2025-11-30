import json


def format_json_for_telegram(data: dict, indent: int = 2) -> str:
    """Format JSON data for Telegram message (with code block)."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)
    # Telegram has a 4096 character limit
    if len(json_str) > 4000:
        json_str = json_str[:4000] + "\n... (truncated)"
    return f"```json\n{json_str}\n```"


def format_calories(amount: int) -> str:
    """Format calorie amount with 'kcal' suffix."""
    return f"{amount:,} kcal"


def format_macros(protein: float, carbs: float, fat: float) -> str:
    """Format macros in a compact string."""
    return f"P: {protein:.1f}g | C: {carbs:.1f}g | F: {fat:.1f}g"


def format_percentage(value: float, total: float) -> str:
    """Format a value as percentage of total."""
    if total == 0:
        return "0%"
    pct = (value / total) * 100
    return f"{pct:.1f}%"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
