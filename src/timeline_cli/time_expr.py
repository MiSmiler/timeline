"""TimeExpr parsing module for unified time expression system (Issue #80, ADR-0012).

Key concepts:
- Timepoint: A point in time with optional components (date, time)
- Timerange: A range between two Timepoints (start..end)
- TimeExpr: Unified abstraction containing either Timepoint or Timerange
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Literal

from timeline_cli.errors import TimelineValidationError

if TYPE_CHECKING:
    from timeline_cli.models import DailyRecord, Event, Todo


@dataclass
class DateRange:
    """Represents a date/time range for filtering (legacy compatibility).

    This is kept for compatibility with existing filter functions.
    Will be used by Timerange.expand_for_query().
    """

    start: datetime | date | None = None  # None = no lower bound
    end: datetime | date | None = None  # None = no upper bound
    include_undated: bool = False  # Include items with no date


@dataclass
class Timepoint:
    """A point in time with optional components.

    Components can be:
    - date + time: Precise point (e.g., 2026-06-23T09:00, todayT09:00)
    - date only: A day (e.g., 2026-06-23, today)
    - time only: Auto-fill date=today (e.g., 09:00)
    - empty: Boundary marker for Timerange
    - undated: No-date keyword (is_undated=True)
    - now: Current time keyword (resolved to concrete date/time)
    """

    date: str | None = None  # YYYY-MM-DD or None
    time: str | None = None  # HH:MM or None
    is_undated: bool = False  # True for "undated" keyword

    def has_time_component(self) -> bool:
        """Check if this timepoint has time (not date-only).

        Returns:
            True if time is set.
        """
        return self.time is not None

    def to_datetime(self, now: datetime | None = None) -> datetime | date | None:
        """Convert to concrete datetime/date.

        Args:
            now: Current datetime for testing. Defaults to datetime.now().

        Returns:
            datetime if both date and time present,
            date if only date present,
            None if undated or empty.
        """
        if now is None:
            now = datetime.now()

        if self.is_undated or (self.date is None and self.time is None):
            return None

        if self.date is None:
            # Time only - auto-filled to today
            date_obj = now.date()
        else:
            date_obj = date.fromisoformat(self.date)

        if self.time is None:
            return date_obj

        time_obj = time.fromisoformat(self.time)
        return datetime.combine(date_obj, time_obj)


@dataclass
class Timerange:
    """A range between two timepoints.

    Format: timepoint..timepoint
    Expansion rules applied during expand_for_query():
    - Start date-only -> dateT00:00
    - End date-only -> dateT23:59
    - Time-only -> auto-fill date=today
    - Empty -> start/end boundary

    Special case: is_undated=True means "undated items" (no date dimension).
    """

    start: Timepoint  # start boundary (empty = no lower bound)
    end: Timepoint  # end boundary (empty = no upper bound)
    is_undated: bool = False  # True for "undated" keyword

    def expand_for_query(self, now: datetime | None = None) -> DateRange:
        """Expand to concrete DateRange for filtering.

        Args:
            now: Current datetime for testing. Defaults to datetime.now().

        Returns:
            DateRange with expanded boundaries.
        """
        if now is None:
            now = datetime.now()

        # Special case: undated filter
        if self.is_undated:
            return DateRange(start=None, end=None, include_undated=True)

        # Expand start boundary
        if self.start.date is None and self.start.time is None:
            # Empty start -> no lower bound
            start = None
        elif self.start.is_undated:
            # Undated in range -> should have been rejected during parsing
            raise TimelineValidationError(
                "Timerange cannot include 'undated' keyword. Use --at undated to filter undated items."
            )
        else:
            # Has date or time
            if self.start.date is None:
                # Time only - auto-fill today
                start_date = now.date()
            else:
                start_date = date.fromisoformat(self.start.date)

            if self.start.time is None:
                # Date only - expand to T00:00
                start_time = time.min
            else:
                start_time = time.fromisoformat(self.start.time)

            start = datetime.combine(start_date, start_time)

        # Expand end boundary
        if self.end.date is None and self.end.time is None:
            # Empty end -> no upper bound
            end = None
        elif self.end.is_undated:
            raise TimelineValidationError(
                "Timerange cannot include 'undated' keyword. Use --at undated to filter undated items."
            )
        else:
            # Has date or time
            if self.end.date is None:
                # Time only - auto-fill today
                end_date = now.date()
            else:
                end_date = date.fromisoformat(self.end.date)

            if self.end.time is None:
                # Date only - expand to T23:59
                end_time = time.max.replace(microsecond=0)
            else:
                end_time = time.fromisoformat(self.end.time)

            end = datetime.combine(end_date, end_time)

        # Bug fix: include_undated=True for full range (..)
        include_undated = start is None and end is None

        return DateRange(start=start, end=end, include_undated=include_undated)


@dataclass
class TimeExpr:
    """Unified time expression - contains Timepoint or Timerange.

    This is the main abstraction for --at parameter.
    """

    kind: Literal["timepoint", "timerange"]
    timepoint: Timepoint | None = None
    timerange: Timerange | None = None

    @classmethod
    def parse(cls, value: str, now: datetime | None = None) -> "TimeExpr":
        """Parse time expression string.

        Detects ".." separator -> Timerange, otherwise -> Timepoint.
        Special case: "undated" -> Timerange(is_undated=True).

        Args:
            value: Time expression string.
            now: Current datetime for testing. Defaults to datetime.now().

        Returns:
            TimeExpr containing Timepoint or Timerange.

        Raises:
            TimelineValidationError: If format is invalid.
        """
        if now is None:
            now = datetime.now()

        # Special case: "undated" is a Timerange keyword
        if value == "undated":
            return cls(
                kind="timerange",
                timerange=Timerange(
                    start=Timepoint(),
                    end=Timepoint(),
                    is_undated=True,
                ),
            )

        # Detect ".." separator for timerange
        if ".." in value:
            timerange = parse_timerange(value, now=now)
            return cls(kind="timerange", timerange=timerange)
        else:
            timepoint = parse_timepoint(value, now=now)
            return cls(kind="timepoint", timepoint=timepoint)


def parse_timepoint(value: str, now: datetime | None = None) -> Timepoint:
    """Parse single timepoint.

    Supported formats:
    - "YYYY-MM-DDTHH:MM" -> explicit datetime with T separator
    - "YYYY-MM-DD" -> explicit date only
    - "today"/"yesterday"/"tomorrow" -> relative date
    - "todayT09:00" -> relative date with time (T separator)
    - "HH:MM" -> time only, auto-fills date=today
    - "undated" -> no date keyword
    - "now" -> current datetime
    - "" -> empty boundary marker
    - "+2h"/"-30m" -> relative offset from now

    Args:
        value: Timepoint string.
        now: Current datetime for testing. Defaults to datetime.now().

    Returns:
        Timepoint object.

    Raises:
        TimelineValidationError: If format is invalid.
    """
    if now is None:
        now = datetime.now()

    # Handle special keywords first
    if value == "undated":
        return Timepoint(date=None, time=None, is_undated=True)

    if value == "now":
        return Timepoint(date=now.date().isoformat(), time=now.strftime("%H:%M"))

    if value == "":
        return Timepoint(date=None, time=None)  # Empty boundary marker

    # Check for relative offset (+/-)
    if _is_relative_offset(value):
        return _parse_relative_offset(value, now)

    # Check for T separator (new unified format)
    if "T" in value:
        parts = value.split("T", maxsplit=1)
        date_part = parts[0]
        time_part = parts[1]

        # Normalize date part
        normalized_date = _normalize_date(date_part, now)

        # Validate time format (HH:MM)
        if not _is_valid_time_format(time_part):
            raise TimelineValidationError(f"Invalid time format: {time_part}. Use HH:MM format (e.g., 09:00).")

        return Timepoint(date=normalized_date, time=time_part)

    # Reject space separator (backward compatibility removed)
    if " " in value:
        raise TimelineValidationError(
            f"Space separator is not supported. Use T separator instead: '{value.replace(' ', 'T')}'"
        )

    # Try to parse as time only (HH:MM)
    if _is_valid_time_format(value):
        # Time only - auto-fill date=today
        return Timepoint(date=now.date().isoformat(), time=value)

    # Try to parse as date only
    normalized_date = _normalize_date(value, now)
    return Timepoint(date=normalized_date, time=None)


def parse_timerange(value: str, now: datetime | None = None) -> Timerange:
    """Parse timerange with ".." separator.

    Format: timepoint..timepoint
    Expansion rules will be applied during expand_for_query().

    Args:
        value: Timerange string (e.g., "today..tomorrow", "..", "09:00..17:00").
        now: Current datetime for testing. Defaults to datetime.now().

    Returns:
        Timerange object.

    Raises:
        TimelineValidationError: If format is invalid or range is reversed.
    """
    if now is None:
        now = datetime.now()

    # Special case: ".." means all (unbounded)
    if value == "..":
        return Timerange(start=Timepoint(), end=Timepoint())

    # Split by ".."
    parts = value.split("..", maxsplit=1)

    start_str = parts[0] if parts[0] else ""
    end_str = parts[1] if len(parts) > 1 and parts[1] else ""

    # Parse both sides
    start_tp = parse_timepoint(start_str, now=now)
    end_tp = parse_timepoint(end_str, now=now)

    # Validate: reject undated in timerange
    if start_tp.is_undated or end_tp.is_undated:
        raise TimelineValidationError(
            "'undated' keyword cannot be used in a timerange. "
            "Use --at undated to filter undated items, or use '..' for all dates."
        )

    # Create Timerange first
    tr = Timerange(start=start_tp, end=end_tp)

    # Validate: start < end (reject reversed ranges)
    # Use expand_for_query to apply correct expansion rules
    _validate_range_order(tr, now)

    return tr


def _normalize_date(value: str, now: datetime) -> str:
    """Normalize date string, converting relative keywords to YYYY-MM-DD.

    Args:
        value: Date string or relative keyword.
        now: Current datetime.

    Returns:
        Date string in YYYY-MM-DD format.

    Raises:
        TimelineValidationError: If format is invalid.
    """
    if value == "today":
        return now.date().isoformat()
    if value == "yesterday":
        return (now.date() - timedelta(days=1)).isoformat()
    if value == "tomorrow":
        return (now.date() + timedelta(days=1)).isoformat()

    # Try to parse as explicit date
    try:
        date_obj = date.fromisoformat(value)
        return date_obj.isoformat()
    except ValueError:
        raise TimelineValidationError(
            f"Invalid date: {value}. Use YYYY-MM-DD format or 'today'/'yesterday'/'tomorrow'."
        ) from None


def _is_valid_time_format(value: str) -> bool:
    """Check if value is a valid HH:MM time format."""
    if not re.match(r"^\d{2}:\d{2}$", value):
        return False
    # Also validate the actual time values (hour: 0-23, minute: 0-59)
    try:
        time.fromisoformat(value)
        return True
    except ValueError:
        return False


def _is_relative_offset(value: str) -> bool:
    """Check if value is a relative time offset (+2h, -30m, etc.)."""
    # Pattern: [+/-] followed by one or two number-unit pairs
    # Units: h, m, min
    pattern = r"^[+-](\d+h)?(\d+(m|min))?$"
    return bool(re.match(pattern, value))


def _parse_relative_offset(value: str, now: datetime) -> Timepoint:
    """Parse relative time offset and apply to now.

    Args:
        value: Offset string like "+2h30m", "-30m", "+1h15min".
        now: Current datetime.

    Returns:
        Timepoint with calculated date and time.

    Raises:
        TimelineValidationError: If offset exceeds ±72h.
    """
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
    new_dt = now + timedelta(minutes=total_minutes)

    return Timepoint(date=new_dt.date().isoformat(), time=new_dt.strftime("%H:%M"))


def _validate_range_order(tr: Timerange, now: datetime) -> None:
    """Validate that start < end (reversed ranges rejected).

    Uses expand_for_query() to apply correct expansion rules:
    - Start date-only -> dateT00:00
    - End date-only -> dateT23:59

    Args:
        tr: Timerange to validate.
        now: Current datetime for expansion.

    Raises:
        TimelineValidationError: If range is reversed (start >= end).
    """
    # Use expand_for_query to apply correct expansion rules
    dr = tr.expand_for_query(now=now)

    # Empty boundaries mean unbounded range (e.g., "..today" or "yesterday..")
    # Cannot validate order on unbounded ranges, so skip validation
    if dr.start is None or dr.end is None:
        return

    # Compare expanded datetime values
    if dr.start > dr.end:
        start_str = _format_datetime(dr.start)
        end_str = _format_datetime(dr.end)
        raise TimelineValidationError(
            f"Reversed time range: start ({start_str}) must be before end ({end_str})."
        )
    # start == end is allowed (single point range)


def _format_datetime(dt: datetime) -> str:
    """Format datetime for display in error messages.

    Args:
        dt: datetime object.

    Returns:
        String in YYYY-MM-DDTHH:MM format.
    """
    return dt.strftime("%Y-%m-%dT%H:%M")


# =============================================================================
# Date utilities (migrated from range_parser.py)
# =============================================================================


def normalize_date_string(value: str) -> str:
    """Normalize a date string, converting relative keywords to YYYY-MM-DD format.

    Args:
        value: Date string (may be relative keyword like "yesterday" or "tomorrow")

    Returns:
        Date string in YYYY-MM-DD format.

    Raises:
        TimelineValidationError: If format is invalid.
    """
    # Reject 'now' as date parameter
    if value == "now":
        raise TimelineValidationError("'now' is not a valid date. Use 'today' instead.")

    if value == "today":
        return date.today().isoformat()
    if value == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    if value == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()

    # Try to parse as explicit date
    try:
        date_obj = date.fromisoformat(value)
        return date_obj.isoformat()
    except ValueError:
        raise TimelineValidationError(
            f"Invalid date: {value}. Use YYYY-MM-DD format or 'today'/'yesterday'/'tomorrow'."
        ) from None


def is_date_in_range(date_str: str | None, date_range: DateRange) -> bool:
    """Check if a date string falls within the range.

    Args:
        date_str: Date string like "2026-06-17" or None for undated
        date_range: DateRange to check against

    Returns:
        True if date is in range
    """
    # Handle undated items (date is None)
    if date_str is None:
        return date_range.include_undated

    # Parse the date
    item_date = date.fromisoformat(date_str)

    # Check start bound
    if date_range.start is not None:
        if isinstance(date_range.start, datetime):
            # Compare as datetime - use start of day
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
            # Compare as datetime - use end of day (23:59:59, no microseconds)
            # to match our Timerange expansion which uses T23:59
            item_dt = datetime.combine(item_date, time.max.replace(microsecond=0))
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


def filter_todos_by_range(
    records: dict[str | None, "DailyRecord"], date_range: DateRange
) -> list[tuple[str | None, "Todo"]]:
    """Filter todos by date range with precise time handling.

    Args:
        records: Dictionary of date -> DailyRecord (date can be None for undated)
        date_range: DateRange to filter by

    Returns:
        List of (date, todo) tuples that match the range

    Filtering rules (Issue #89):
        - Timed todos: Precise datetime filtering, closed interval [start, end]
        - No-time todos: Date filtering, date must fall within [start.date(), end.date()]
        - Undated todos (date=None): Only included if date_range.include_undated=True
    """
    results = []

    # Determine the date bounds for no-time todo filtering
    # Extract date from datetime bounds if present
    start_date: date | None = None
    end_date: date | None = None

    if date_range.start is not None:
        if isinstance(date_range.start, datetime):
            start_date = date_range.start.date()
        else:
            start_date = date_range.start

    if date_range.end is not None:
        if isinstance(date_range.end, datetime):
            end_date = date_range.end.date()
        else:
            end_date = date_range.end

    for date_str, record in records.items():
        # Skip undated record if not included in range
        if date_str is None:
            if date_range.include_undated:
                # Include all undated todos
                for todo in record.todos:
                    results.append((None, todo))
            continue

        todo_date = date.fromisoformat(date_str)

        for todo in record.todos:
            if todo.time is not None:
                # Timed todo: precise datetime filtering
                todo_dt = datetime.combine(todo_date, time.fromisoformat(todo.time))
                if is_datetime_in_range(todo_dt, date_range):
                    results.append((date_str, todo))
            else:
                # No-time todo: date filtering
                # Check if todo_date falls within [start_date, end_date]
                if start_date is not None and todo_date < start_date:
                    continue
                if end_date is not None and todo_date > end_date:
                    continue
                results.append((date_str, todo))

    return results


def filter_events_by_range(
    records: dict[str | None, "DailyRecord"], date_range: DateRange
) -> list[tuple[str | None, "Event"]]:
    """Filter events by date range.

    Args:
        records: Dictionary of date -> DailyRecord (date can be None for undated)
        date_range: DateRange to filter by

    Returns:
        List of (date, event) tuples that match the range

    Note: Events always have a date (never None), so undated records are skipped.
    """
    results = []
    for date_str, record in records.items():
        # Events cannot be undated
        if date_str is None:
            continue

        # Check if date is in range
        if not is_date_in_range(date_str, date_range):
            continue

        # Include all events from this date
        for event in record.events:
            results.append((date_str, event))

    return results
