from datetime import date, timedelta
from dateutil import parser as dateutil_parser
from typing import Tuple, Optional


def parse_date_input(text: str) -> Tuple[date, date]:
    """
    Parse flexible date input into a date range.

    Supports:
    - "today" -> today, today
    - "yesterday" -> yesterday, yesterday
    - "this week" -> monday of this week, today
    - "last week" -> last monday, last sunday
    - "this month" -> 1st of month, today
    - "2024-11-15" -> specific date, same date
    - "2024-11-10 to 2024-11-15" or "2024-11-10:2024-11-15" -> range

    Returns:
        Tuple of (start_date, end_date)
    """
    text = text.strip().lower()
    today = date.today()

    # Keywords
    if text == "today" or text == "":
        return today, today

    if text == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    if text == "this week":
        monday = today - timedelta(days=today.weekday())
        return monday, today

    if text == "last week":
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return last_monday, last_sunday

    if text == "this month":
        first_of_month = today.replace(day=1)
        return first_of_month, today

    if text == "last month":
        first_of_this_month = today.replace(day=1)
        last_of_prev_month = first_of_this_month - timedelta(days=1)
        first_of_prev_month = last_of_prev_month.replace(day=1)
        return first_of_prev_month, last_of_prev_month

    # Date range with separator
    for separator in [" to ", ":", " - "]:
        if separator in text:
            parts = text.split(separator)
            if len(parts) == 2:
                start = _parse_single_date(parts[0].strip())
                end = _parse_single_date(parts[1].strip())
                if start and end:
                    return start, end

    # Single date
    parsed = _parse_single_date(text)
    if parsed:
        return parsed, parsed

    # Default to today if nothing matched
    return today, today


def _parse_single_date(text: str) -> Optional[date]:
    """Parse a single date string."""
    try:
        dt = dateutil_parser.parse(text, dayfirst=False)
        return dt.date()
    except (ValueError, TypeError):
        return None


def format_date_range(start: date, end: date) -> str:
    """Format a date range for display."""
    if start == end:
        return start.strftime("%B %d, %Y")
    else:
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
