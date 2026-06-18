"""Range parser for timeline-cli --range parameter."""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from timeline_cli.models import DailyRecord, Event, Todo


@dataclass
class DateRange:
    """Represents a date/time range for filtering."""

    start: datetime | date | None = None  # None = no lower bound
    end: datetime | date | None = None  # None = no upper bound
    include_undated: bool = False  # Include items with no date


def parse_datetime(value: str) -> datetime | date:
    """Parse a datetime or date string.

    Args:
        value: String like "2026-06-17", "2026-06-17T14:30", "today", "yesterday", "tomorrow", or "now"

    Returns:
        datetime or date object
    """
    from datetime import timedelta

    if value == "today":
        return date.today()
    if value == "yesterday":
        return date.today() - timedelta(days=1)
    if value == "tomorrow":
        return date.today() + timedelta(days=1)
    if value == "now":
        return datetime.now()

    # Try datetime format first
    if "T" in value:
        return datetime.fromisoformat(value)

    # Try date format
    return date.fromisoformat(value)


def parse_range(range_str: str, now: datetime | None = None) -> DateRange:
    """Parse --range parameter string.

    Supported formats:
    - ".." = all (no bounds)
    - "today" / "yesterday" / "tomorrow" = relative date
    - "..today" / "today.." = relative to today
    - "YYYY-MM-DD.." / "..YYYY-MM-DD" = relative to date
    - "YYYY-MM-DD..YYYY-MM-DD" = date range
    - "YYYY-MM-DDTHH:MM.." = precise time point
    - "..now" / "now.." = relative to current time
    - "?" = undated items (include_undated=True)

    Args:
        range_str: Range specification string
        now: Current datetime (defaults to datetime.now())

    Returns:
        DateRange object
    """
    if now is None:
        now = datetime.now()

    # Special case: undated
    if range_str == "?":
        return DateRange(include_undated=True)

    # Special case: all
    if range_str == "..":
        return DateRange()

    # Single value (no "..")
    if ".." not in range_str:
        value = parse_datetime(range_str)
        if isinstance(value, datetime):
            # Single datetime: match exactly that moment
            return DateRange(start=value, end=value)
        else:
            # Single date: match that entire day
            start_dt = datetime.combine(value, time.min)
            end_dt = datetime.combine(value, time.max)
            return DateRange(start=start_dt, end=end_dt)

    # Split range
    parts = range_str.split("..", maxsplit=1)
    left = parts[0] if parts[0] else None
    right = parts[1] if len(parts) > 1 and parts[1] else None

    start = None
    end = None

    if left:
        start = parse_datetime(left)
        # If start is a date, use start of day
        if isinstance(start, date) and not isinstance(start, datetime):
            start = datetime.combine(start, time.min)

    if right:
        end = parse_datetime(right)
        # If end is a date, use end of day
        if isinstance(end, date) and not isinstance(end, datetime):
            end = datetime.combine(end, time.max)

    return DateRange(start=start, end=end)


def is_date_in_range(date_str: str, date_range: DateRange) -> bool:
    """Check if a date string falls within the range.

    Args:
        date_str: Date string like "2026-06-17" or None for undated
        date_range: DateRange to check against

    Returns:
        True if date is in range
    """
    # Handle undated items
    if date_str is None:
        return date_range.include_undated

    # Parse the date
    item_date = date.fromisoformat(date_str)

    # Check start bound
    if date_range.start is not None:
        if isinstance(date_range.start, datetime):
            # Compare as datetime
            item_dt = datetime.combine(item_date, time.min)
            if item_dt < date_range.start:
                return False
        else:
            # Compare as date
            if item_date < date_range.start:
                return False

    # Check end bound
    if date_range.end is not None:
        if isinstance(date_range.end, datetime):
            # Compare as datetime
            item_dt = datetime.combine(item_date, time.max)
            if item_dt > date_range.end:
                return False
        else:
            # Compare as date
            if item_date > date_range.end:
                return False

    return True


def is_datetime_in_range(dt: datetime, date_range: DateRange) -> bool:
    """Check if a datetime falls within the range.

    Args:
        dt: datetime object
        date_range: DateRange to check against

    Returns:
        True if datetime is in range
    """
    # Check start bound
    if date_range.start is not None:
        start = date_range.start
        if isinstance(start, date) and not isinstance(start, datetime):
            start = datetime.combine(start, time.min)
        if dt < start:
            return False

    # Check end bound
    if date_range.end is not None:
        end = date_range.end
        if isinstance(end, date) and not isinstance(end, datetime):
            end = datetime.combine(end, time.max)
        if dt > end:
            return False

    return True


def filter_todos_by_range(records: dict[str, "DailyRecord"], date_range: DateRange) -> list[tuple[str, "Todo"]]:
    """Filter todos by date range.

    Args:
        records: Dictionary of date -> DailyRecord
        date_range: DateRange to filter by

    Returns:
        List of (date, todo) tuples that match the range
    """
    results = []
    for date_str, record in records.items():
        # Handle undated record (0000-00-00)
        if date_str == "0000-00-00":
            if date_range.include_undated:
                for todo in record.todos:
                    results.append((date_str, todo))
            continue

        # Check if date is in range
        if not is_date_in_range(date_str, date_range):
            continue

        # Include all todos from this date
        for todo in record.todos:
            results.append((date_str, todo))

    return results


def filter_events_by_range(records: dict[str, "DailyRecord"], date_range: DateRange) -> list[tuple[str, "Event"]]:
    """Filter events by date range.

    Args:
        records: Dictionary of date -> DailyRecord
        date_range: DateRange to filter by

    Returns:
        List of (date, event) tuples that match the range
    """
    results = []
    for date_str, record in records.items():
        # Handle undated record (0000-00-00)
        if date_str == "0000-00-00":
            if date_range.include_undated:
                for event in record.events:
                    results.append((date_str, event))
            continue

        # Check if date is in range
        if not is_date_in_range(date_str, date_range):
            continue

        # Include all events from this date
        for event in record.events:
            results.append((date_str, event))

    return results
