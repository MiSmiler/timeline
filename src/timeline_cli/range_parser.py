"""Range parser for timeline-cli --range parameter."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from timeline_cli.errors import TimelineValidationError

if TYPE_CHECKING:
    from timeline_cli.models import DailyRecord, Event, Todo


@dataclass
class AtParameter:
    """Parsed result from --at parameter."""

    date: str | None  # YYYY-MM-DD format or None for undated
    time: str | None  # HH:MM format or None


@dataclass
class DateRange:
    """Represents a date/time range for filtering."""

    start: datetime | date | None = None  # None = no lower bound
    end: datetime | date | None = None  # None = no upper bound
    include_undated: bool = False  # Include items with no date


def normalize_time_string(value: str) -> str:
    """Normalize a time string, converting 'now' to current HH:MM.

    Args:
        value: Time string (may be 'now' or HH:MM format)

    Returns:
        Time string in HH:MM format
    """
    if value == "now":
        return datetime.now().strftime("%H:%M")
    return value  # Already in HH:MM format


def validate_time_now_constraint(time_value: str, date_value: str) -> None:
    """Validate that --time now is only used with today's date.

    Args:
        time_value: The time argument value
        date_value: The date argument value (not yet normalized)

    Raises:
        TimelineValidationError: If 'now' is used with non-today date
    """
    if time_value == "now":
        normalized_date = normalize_date_string(date_value)
        today = date.today().isoformat()
        if normalized_date != today:
            raise TimelineValidationError(
                f"'--time now' can only be used when the date is today.\n"
                f"Current date is {today}, but specified date is {normalized_date}."
            )


def validate_time_now_for_existing_date(time_value: str, existing_date: str) -> None:
    """Validate that --time now is only used when existing item's date is today.

    Args:
        time_value: The --new-time argument value
        existing_date: The existing item's date (YYYY-MM-DD format)

    Raises:
        TimelineValidationError: If 'now' is used with non-today date
    """
    if time_value == "now":
        today = date.today().isoformat()
        if existing_date != today:
            raise TimelineValidationError(
                f"'--time now' can only be used when the date is today.\n"
                f"Current date is {today}, but specified date is {existing_date}."
            )


def parse_at_parameter(value: str) -> AtParameter:
    """Parse --at parameter string.

    Supported formats (Slice 1):
    - "YYYY-MM-DD HH:MM" → explicit datetime
    - "YYYY-MM-DD" → explicit date only
    - "today"/"yesterday"/"tomorrow" → relative date
    - "" → undated (no date, no time)

    Supported formats (Slice 2):
    - "today HH:MM" → relative date + explicit time
    - "yesterday HH:MM" → relative date + explicit time

    Supported formats (Slice 3):
    - "HH:MM" → time only, defaults to today

    Supported formats (Slice 4):
    - "now" → current datetime

    Supported formats (Slice 5):
    - "+2h30m" / "-30m" → offset from now

    Args:
        value: The --at parameter string

    Returns:
        AtParameter with date (YYYY-MM-DD) and time (HH:MM) fields

    Raises:
        TimelineValidationError: If format is invalid or constraints violated
    """
    if value == "":
        return AtParameter(date=None, time=None)

    # Slice 4: Handle "now" keyword
    if value == "now":
        return AtParameter(date=date.today().isoformat(), time=datetime.now().strftime("%H:%M"))

    # Check for space-separated parts (Slice 1, 2)
    parts = value.split(maxsplit=1)

    if len(parts) == 2:
        # Two parts: date and time
        date_part, time_part = parts

        # Slice 5: Reject relative date + relative offset combination
        if _is_relative_offset(time_part):
            raise TimelineValidationError(
                f"Cannot combine relative date with relative time offset.\n"
                f"Use '{time_part}' directly (base is now), or '{date_part} HH:MM' (explicit time)."
            )

        normalized_date = normalize_date_string(date_part)
        # Time validation: must be HH:MM format
        if not _is_valid_time_format(time_part):
            raise TimelineValidationError(f"Invalid time format: {time_part}. Use HH:MM format.")
        return AtParameter(date=normalized_date, time=time_part)

    # Single part
    single = parts[0]

    # Slice 5: Handle relative offset (+2h30m, -30m)
    if _is_relative_offset(single):
        return _parse_relative_offset(single)

    # Slice 3: Handle time-only format (HH:MM)
    if _is_valid_time_format(single):
        return AtParameter(date=date.today().isoformat(), time=single)

    # Slice 1: Try to parse as date or keyword
    try:
        normalized = normalize_date_string(single)
        return AtParameter(date=normalized, time=None)
    except TimelineValidationError:
        raise TimelineValidationError(f"Invalid --at parameter: {value}") from None


def _is_valid_time_format(value: str) -> bool:
    """Check if value is a valid HH:MM time format."""
    import re

    return bool(re.match(r"^\d{2}:\d{2}$", value))


def _is_relative_offset(value: str) -> bool:
    """Check if value is a relative time offset (+2h, -30m, etc.)."""
    import re

    # Pattern: [+/-] followed by one or two number-unit pairs
    # Units: h, m, min
    # Examples: +2h, -30m, +2h30m, -1h15min, +30min, -2h5m
    pattern = r"^[+-](\d+h)?(\d+(m|min))?$"
    return bool(re.match(pattern, value))


def _parse_relative_offset(value: str) -> AtParameter:
    """Parse relative time offset and apply to now.

    Args:
        value: Offset string like "+2h30m", "-30m", "+1h15min"

    Returns:
        AtParameter with today's date and calculated time

    Raises:
        TimelineValidationError: If offset exceeds ±72h
    """
    import re

    # Parse offset components
    sign = 1 if value.startswith("+") else -1
    offset_str = value[1:]  # Remove sign

    total_minutes = 0

    # Match hours: <number>h
    hours_match = re.search(r"(\d+)h", offset_str)
    if hours_match:
        total_minutes += int(hours_match.group(1)) * 60

    # Match minutes: <number>m or <number>min
    minutes_match = re.search(r"(\d+)(m|min)", offset_str)
    if minutes_match:
        total_minutes += int(minutes_match.group(1))

    total_minutes *= sign

    # Validate range: ±72h
    max_offset = 72 * 60
    if abs(total_minutes) > max_offset:
        raise TimelineValidationError(
            f"Time offset exceeds ±72 hours limit.\nSpecified offset: {value} ({total_minutes / 60:.1f} hours)."
        )

    # Calculate new time
    now = datetime.now()
    new_dt = now + timedelta(minutes=total_minutes)

    return AtParameter(date=new_dt.date().isoformat(), time=new_dt.strftime("%H:%M"))


def validate_event_time_not_future(at_param: AtParameter) -> None:
    """Validate that Event time is not later than now.

    Events represent "things that already happened", so they cannot be in the future.

    Args:
        at_param: Parsed --at parameter

    Raises:
        TimelineValidationError: If the datetime is later than now
    """
    # Only check if both date and time are specified
    if at_param.date is None or at_param.time is None:
        return  # Date-only events are allowed (no time constraint)

    # Build datetime from parsed result
    event_date = date.fromisoformat(at_param.date)
    event_time = time.fromisoformat(at_param.time)
    event_dt = datetime.combine(event_date, event_time)

    # Check against now
    now = datetime.now()
    if event_dt > now:
        raise TimelineValidationError(
            f"Event time cannot be later than now.\n"
            f"Specified: {at_param.date} {at_param.time}, Current: {now.strftime('%Y-%m-%d %H:%M')}"
        )


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
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise TimelineValidationError(f"Invalid datetime: {value}. Use YYYY-MM-DDTHH:MM format.") from None

    # Try date format
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise TimelineValidationError(f"Invalid date: {value}. Use YYYY-MM-DD format.") from None


def normalize_date_string(value: str) -> str:
    """Normalize a date string, converting relative keywords to YYYY-MM-DD format.

    Args:
        value: Date string (may be relative keyword like "yesterday" or "tomorrow")

    Returns:
        Date string in YYYY-MM-DD format (or special date like "0000-00-00")
    """
    # Issue #69: Reject 'now' as date parameter
    if value == "now":
        raise TimelineValidationError("'--date' does not support 'now'. Use 'today' instead.")

    # Special case: undated items (? or 0000-00-00)
    if value == "?" or value == "0000-00-00":
        return "0000-00-00"

    parsed = parse_datetime(value)
    if isinstance(parsed, datetime):
        # Convert datetime to date string
        return parsed.date().isoformat()
    else:
        # Already a date
        return parsed.isoformat()


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
