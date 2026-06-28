"""Tests for time expression parsing — TimePoint and DateRange."""

from dataclasses import FrozenInstanceError
from datetime import date, datetime, time
from unittest.mock import patch

import pytest

from timeline_cli.errors import TimelineValidationError
from timeline_cli.time_expression import DateRange, TimePoint

# ---------------------------------------------------------------------------
# TimePoint.parse
# ---------------------------------------------------------------------------


class TestTimePointParse:
    """Tests for TimePoint.parse()."""

    # -- Acceptance criteria ------------------------------------------------

    def test_today(self) -> None:
        """``today`` returns current date and no time."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("today")

        assert tp.date == date(2026, 6, 27)
        assert tp.time is None

    def test_now(self) -> None:
        """``now`` returns current date and current time."""
        with patch("timeline_cli.time_expression.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 27, 15, 30, 0)
            tp = TimePoint.parse("now")

        assert tp.date == date(2026, 6, 27)
        assert tp.time == time(15, 30, 0)

    def test_today_with_time(self) -> None:
        """``todayT14:00`` returns current date and 14:00."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("todayT14:00")

        assert tp.date == date(2026, 6, 27)
        assert tp.time == time(14, 0)

    def test_absolute_date_with_time(self) -> None:
        """``2026-06-26T09:30`` returns exact date and 09:30."""
        tp = TimePoint.parse("2026-06-26T09:30")

        assert tp.date == date(2026, 6, 26)
        assert tp.time == time(9, 30)

    def test_yesterday(self) -> None:
        """``yesterday`` returns yesterday's date and no time."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("yesterday")

        assert tp.date == date(2026, 6, 26)
        assert tp.time is None

    def test_absolute_date(self) -> None:
        """``2026-06-26`` returns exact date and no time."""
        tp = TimePoint.parse("2026-06-26")

        assert tp.date == date(2026, 6, 26)
        assert tp.time is None

    # -- Additional coverage ------------------------------------------------

    def test_yesterday_with_time(self) -> None:
        """``yesterdayT14:00`` returns yesterday's date and 14:00."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("yesterdayT14:00")

        assert tp.date == date(2026, 6, 26)
        assert tp.time == time(14, 0)

    def test_strips_whitespace(self) -> None:
        """Leading/trailing whitespace is ignored."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("  today  ")

        assert tp.date == date(2026, 6, 27)
        assert tp.time is None

    def test_strips_whitespace_around_t(self) -> None:
        """Whitespace around ``T`` separator is ignored."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            tp = TimePoint.parse("today T 14:00")

        assert tp.date == date(2026, 6, 27)
        assert tp.time == time(14, 0)

    # -- Error cases --------------------------------------------------------

    def test_empty_string_raises(self) -> None:
        """Empty string raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="must not be empty"):
            TimePoint.parse("")

    def test_whitespace_only_raises(self) -> None:
        """Whitespace-only string raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="must not be empty"):
            TimePoint.parse("   ")

    def test_invalid_date_raises(self) -> None:
        """An unrecognised date expression raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            TimePoint.parse("tomorrow")

    def test_invalid_time_raises(self) -> None:
        """An invalid time format raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="Invalid time"):
            TimePoint.parse("todayT25:00")

    def test_garbage_string_raises(self) -> None:
        """A completely unrecognisable string raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            TimePoint.parse("not-a-date-or-time")

    def test_now_with_explicit_time_raises(self) -> None:
        """``nowT14:00`` is rejected — ``now`` is a datetime, not a date part."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            TimePoint.parse("nowT14:00")

    # -- Immutability -------------------------------------------------------

    def test_frozen(self) -> None:
        """TimePoint is immutable (frozen dataclass)."""
        tp = TimePoint.parse("2026-06-26")
        with pytest.raises(FrozenInstanceError):
            tp.date = date(2026, 7, 1)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DateRange.parse
# ---------------------------------------------------------------------------


class TestDateRangeParse:
    """Tests for DateRange.parse()."""

    # -- Acceptance criteria ------------------------------------------------

    def test_single_date_today(self) -> None:
        """``today`` returns start = end = current date."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            dr = DateRange.parse("today")

        assert dr.start == date(2026, 6, 27)
        assert dr.end == date(2026, 6, 27)

    def test_closed_range(self) -> None:
        """``2026-06-20..2026-06-26`` returns a closed range."""
        dr = DateRange.parse("2026-06-20..2026-06-26")

        assert dr.start == date(2026, 6, 20)
        assert dr.end == date(2026, 6, 26)

    def test_unbounded(self) -> None:
        """``..`` returns an unbounded range (start=None, end=None)."""
        dr = DateRange.parse("..")

        assert dr.start is None
        assert dr.end is None

    def test_open_start(self) -> None:
        """``..2026-06-26`` returns start=None, end=that date."""
        dr = DateRange.parse("..2026-06-26")

        assert dr.start is None
        assert dr.end == date(2026, 6, 26)

    def test_open_end(self) -> None:
        """``2026-06-20..`` returns start=that date, end=None."""
        dr = DateRange.parse("2026-06-20..")

        assert dr.start == date(2026, 6, 20)
        assert dr.end is None

    # -- Additional coverage ------------------------------------------------

    def test_range_open_end_relative(self) -> None:
        """``today..`` returns open-end range starting from today."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            dr = DateRange.parse("today..")

        assert dr.start == date(2026, 6, 27)
        assert dr.end is None

    def test_range_open_start_relative(self) -> None:
        """``..yesterday`` returns open-start range ending at yesterday."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            dr = DateRange.parse("..yesterday")

        assert dr.start is None
        assert dr.end == date(2026, 6, 26)

    def test_single_date_yesterday(self) -> None:
        """``yesterday`` returns start = end = yesterday's date."""
        with patch("timeline_cli.time_expression.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 27)
            mock_date.fromisoformat.side_effect = date.fromisoformat
            dr = DateRange.parse("yesterday")

        assert dr.start == date(2026, 6, 26)
        assert dr.end == date(2026, 6, 26)

    def test_single_date_absolute(self) -> None:
        """``2026-06-26`` returns start = end = that date."""
        dr = DateRange.parse("2026-06-26")

        assert dr.start == date(2026, 6, 26)
        assert dr.end == date(2026, 6, 26)

    def test_range_strips_whitespace(self) -> None:
        """Whitespace around ``..`` is ignored."""
        dr = DateRange.parse("  2026-06-20  ..  2026-06-26  ")

        assert dr.start == date(2026, 6, 20)
        assert dr.end == date(2026, 6, 26)

    # -- Error cases --------------------------------------------------------

    def test_empty_string_raises(self) -> None:
        """Empty string raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="must not be empty"):
            DateRange.parse("")

    def test_whitespace_only_raises(self) -> None:
        """Whitespace-only string raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="must not be empty"):
            DateRange.parse("   ")

    def test_invalid_date_in_range_raises(self) -> None:
        """An invalid date on either side of ``..`` raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            DateRange.parse("2026-06-20..garbage")

        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            DateRange.parse("garbage..2026-06-26")

    def test_unknown_single_date_raises(self) -> None:
        """An unrecognised single-date expression raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            DateRange.parse("tomorrow")

    def test_single_date_now_raises(self) -> None:
        """``now`` is rejected — it is a datetime expression, not a date."""
        with pytest.raises(TimelineValidationError, match="Invalid date expression"):
            DateRange.parse("now")

    def test_reversed_range_raises(self) -> None:
        """A reversed range (end before start) raises TimelineValidationError."""
        with pytest.raises(TimelineValidationError, match="start.*after.*end"):
            DateRange.parse("2026-06-26..2026-06-20")

    # -- Immutability -------------------------------------------------------

    def test_frozen(self) -> None:
        """DateRange is immutable (frozen dataclass)."""
        dr = DateRange.parse("..")
        with pytest.raises(FrozenInstanceError):
            dr.start = date(2026, 7, 1)  # type: ignore[misc]
