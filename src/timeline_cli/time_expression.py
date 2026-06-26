"""Time expression parsing — TimePoint and DateRange value objects.

These are pure value objects that parse user-supplied time expression strings
into concrete :class:`datetime.date` and :class:`datetime.time` values.

Relative expressions (``today``, ``yesterday``, ``now``) are resolved at parse
time using :func:`datetime.date.today` / :func:`datetime.datetime.now`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from timeline_cli.errors import TimelineValidationError


def _parse_date_string(s: str) -> date:
    """Parse a date expression into a :class:`datetime.date`.

    Args:
        s: One of ``"today"``, ``"yesterday"``, or an ISO-format date string
           (``YYYY-MM-DD``).

    Returns:
        The resolved :class:`datetime.date`.

    Raises:
        TimelineValidationError: If the expression is not a recognised date.
    """
    s = s.strip()
    if s == "today":
        return date.today()
    if s == "yesterday":
        return date.today() - timedelta(days=1)
    if s == "now":
        return date.today()
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        raise TimelineValidationError(
            f"Invalid date expression: {s!r}. Expected 'today', 'yesterday', 'now', or YYYY-MM-DD."
        ) from None


@dataclass(frozen=True)
class TimePoint:
    """A point-in-time parsed from a user-supplied time expression.

    Supports relative expressions that resolve to the current date/time,
    absolute ISO-format dates, and optional time-of-day suffixes.
    """

    date: date
    """The resolved date."""

    time: time | None = None
    """The resolved time of day, or ``None`` if no time was provided."""

    @classmethod
    def parse(cls, s: str) -> TimePoint:
        """Parse a time expression string into a :class:`TimePoint`.

        Supported formats:

        * ``today`` — current date, no time
        * ``yesterday`` — yesterday's date, no time
        * ``now`` — current date and current time
        * ``YYYY-MM-DD`` — exact date, no time
        * ``<date>T<HH:MM>`` — date with explicit time (e.g. ``todayT14:00``,
          ``2026-06-26T09:30``)

        Args:
            s: The time expression string.

        Returns:
            A new :class:`TimePoint` with resolved date and optional time.

        Raises:
            TimelineValidationError: If the expression is empty or invalid.
        """
        s = s.strip()
        if not s:
            raise TimelineValidationError("Time expression must not be empty.")

        # Split on 'T' to separate date and time parts
        if "T" in s:
            date_part, _, time_part = s.partition("T")
            date_part = date_part.strip()
            time_part = time_part.strip()
        else:
            date_part = s
            time_part = None

        # Resolve date part
        if date_part == "now":
            dt = datetime.now()
            parsed_date = dt.date()
            parsed_time = dt.time() if time_part is None else _parse_time(time_part)
        elif date_part == "today":
            parsed_date = date.today()
            parsed_time = _parse_time(time_part) if time_part else None
        elif date_part == "yesterday":
            parsed_date = date.today() - timedelta(days=1)
            parsed_time = _parse_time(time_part) if time_part else None
        else:
            parsed_date = _parse_date_string(date_part)
            parsed_time = _parse_time(time_part) if time_part else None

        return cls(date=parsed_date, time=parsed_time)


def _parse_time(s: str) -> time:
    """Parse a time string in ``HH:MM`` format.

    Args:
        s: Time string like ``"14:00"``.

    Returns:
        The parsed :class:`datetime.time`.

    Raises:
        TimelineValidationError: If the time format is invalid.
    """
    s = s.strip()
    try:
        return time.fromisoformat(s)
    except (ValueError, TypeError):
        raise TimelineValidationError(f"Invalid time format: {s!r}. Expected HH:MM.") from None


@dataclass(frozen=True)
class DateRange:
    """A date range parsed from a user-supplied range expression.

    Supports single dates, closed ranges, open-start ranges, open-end ranges,
    and the unbounded range.
    """

    start: date | None = None
    """The start date of the range, or ``None`` for unbounded start."""

    end: date | None = None
    """The end date of the range, or ``None`` for unbounded end."""

    @classmethod
    def parse(cls, s: str) -> DateRange:
        """Parse a date range expression string into a :class:`DateRange`.

        Supported formats:

        * Single date — ``today``, ``yesterday``, ``2026-06-26`` (start = end =
          that date)
        * Closed range — ``2026-06-20..2026-06-26``
        * Open-start — ``..2026-06-26``
        * Open-end — ``2026-06-20..``
        * Unbounded — ``..``

        Args:
            s: The date range expression string.

        Returns:
            A new :class:`DateRange` with resolved start and end dates.

        Raises:
            TimelineValidationError: If the expression is empty or contains
                invalid date strings.
        """
        s = s.strip()
        if not s:
            raise TimelineValidationError("Date range expression must not be empty.")

        if ".." in s:
            left, _, right = s.partition("..")
            left = left.strip()
            right = right.strip()

            start = _parse_date_string(left) if left else None
            end = _parse_date_string(right) if right else None
        else:
            parsed = _parse_date_string(s)
            start = parsed
            end = parsed

        return cls(start=start, end=end)
