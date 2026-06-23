"""Tests for parse_at_parameter function."""

import re
from datetime import datetime

import pytest

from timeline_cli.range_parser import parse_at_parameter


class TestParseAtBasic:
    """Tests for Slice 1: basic format parsing."""

    def test_parse_at_explicit_datetime(self):
        """--at "2026-06-22 15:00" → date=2026-06-22, time=15:00"""
        result = parse_at_parameter("2026-06-22 15:00")
        assert result.date == "2026-06-22"
        assert result.time == "15:00"

    def test_parse_at_explicit_date(self):
        """--at "2026-06-22" → date=2026-06-22, time=None"""
        result = parse_at_parameter("2026-06-22")
        assert result.date == "2026-06-22"
        assert result.time is None

    def test_parse_at_relative_date_keywords_accepted(self):
        """Relative keywords are accepted and return valid date strings."""
        # We don't test exact values - that's tested in parse_datetime
        result_today = parse_at_parameter("today")
        assert result_today.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result_today.date)
        assert result_today.time is None

        result_yesterday = parse_at_parameter("yesterday")
        assert result_yesterday.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result_yesterday.date)
        assert result_yesterday.time is None

        result_tomorrow = parse_at_parameter("tomorrow")
        assert result_tomorrow.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result_tomorrow.date)
        assert result_tomorrow.time is None

    def test_parse_at_undated(self):
        """--at "" → date=None, time=None"""
        result = parse_at_parameter("")
        assert result.date is None
        assert result.time is None


class TestParseAtRelativeDateWithTime:
    """Tests for Slice 2: relative date + explicit time format."""

    def test_parse_at_relative_date_with_time_format(self):
        """Relative date + time format is accepted."""
        result = parse_at_parameter("today 15:00")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time == "15:00"

        result = parse_at_parameter("yesterday 10:00")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time == "10:00"

        result = parse_at_parameter("tomorrow 09:00")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time == "09:00"


class TestParseAtTimeOnly:
    """Tests for Slice 3: time only format."""

    def test_parse_at_time_only_returns_date_and_time(self):
        """Time-only format returns a date string and time."""
        result = parse_at_parameter("15:00")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time == "15:00"

        result = parse_at_parameter("09:30")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time == "09:30"


class TestParseAtNow:
    """Tests for Slice 4: 'now' keyword format."""

    def test_parse_at_now_returns_datetime(self):
        """--at "now" returns current date and time."""
        result = parse_at_parameter("now")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time is not None
        assert re.match(r"\d{2}:\d{2}", result.time)

    def test_parse_at_now_time_format(self):
        """--at "now" time should be HH:MM format"""
        result = parse_at_parameter("now")
        assert re.match(r"\d{2}:\d{2}", result.time)


class TestParseAtRelativeOffset:
    """Tests for Slice 5: relative time offset format."""

    def test_parse_at_positive_offset_hours_accepted(self):
        """--at "+2h" is accepted and returns valid date/time."""
        result = parse_at_parameter("+2h")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time is not None
        assert re.match(r"\d{2}:\d{2}", result.time)

    def test_parse_at_negative_offset_minutes_accepted(self):
        """--at "-30m" is accepted and returns valid date/time."""
        result = parse_at_parameter("-30m")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time is not None
        assert re.match(r"\d{2}:\d{2}", result.time)

    def test_parse_at_combined_offset_accepted(self):
        """--at "+2h30m" is accepted and returns valid date/time."""
        result = parse_at_parameter("+2h30m")
        assert result.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", result.date)
        assert result.time is not None
        assert re.match(r"\d{2}:\d{2}", result.time)

    def test_parse_at_offset_exceeds_72h_rejected(self):
        """--at "+100h" → TimelineValidationError"""
        from timeline_cli.errors import TimelineValidationError

        with pytest.raises(TimelineValidationError) as exc_info:
            parse_at_parameter("+100h")
        assert "±72 hours" in str(exc_info.value)

    def test_parse_at_negative_offset_exceeds_72h_rejected(self):
        """--at "-80h" → TimelineValidationError"""
        from timeline_cli.errors import TimelineValidationError

        with pytest.raises(TimelineValidationError) as exc_info:
            parse_at_parameter("-80h")
        assert "±72 hours" in str(exc_info.value)

    def test_parse_at_relative_date_with_offset_rejected(self):
        """--at "today +2h" → TimelineValidationError (forbidden combination)"""
        from timeline_cli.errors import TimelineValidationError

        with pytest.raises(TimelineValidationError) as exc_info:
            parse_at_parameter("today +2h")
        assert "relative time offset" in str(exc_info.value)


class TestValidateEventTimeNotFuture:
    """Tests for Slice 6: Event cannot be later than now."""

    def test_event_at_future_rejected(self):
        """Event with future datetime is rejected."""
        from timeline_cli.errors import TimelineValidationError
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        future_param = AtParameter(date="2026-06-22", time="16:00")
        now = datetime(2026, 6, 22, 14, 0)

        with pytest.raises(TimelineValidationError) as exc_info:
            validate_event_time_not_future(future_param, now=now)
        assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_tomorrow_rejected(self):
        """Event with tomorrow's date is rejected."""
        from timeline_cli.errors import TimelineValidationError
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        future_param = AtParameter(date="2026-06-23", time="10:00")
        now = datetime(2026, 6, 22, 14, 0)

        with pytest.raises(TimelineValidationError) as exc_info:
            validate_event_time_not_future(future_param, now=now)
        assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_past_allowed(self):
        """Event with past datetime is allowed."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        past_param = AtParameter(date="2026-06-22", time="10:00")
        now = datetime(2026, 6, 22, 14, 0)
        # Should not raise
        validate_event_time_not_future(past_param, now=now)

    def test_event_at_offset_future_rejected(self):
        """Event with +2h offset (future) is rejected."""
        from timeline_cli.errors import TimelineValidationError
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        future_param = AtParameter(date="2026-06-22", time="12:00")
        now = datetime(2026, 6, 22, 10, 0)

        with pytest.raises(TimelineValidationError) as exc_info:
            validate_event_time_not_future(future_param, now=now)
        assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_offset_past_allowed(self):
        """Event with -2h offset (past) is allowed."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        past_param = AtParameter(date="2026-06-22", time="12:00")
        now = datetime(2026, 6, 22, 14, 0)
        # Should not raise
        validate_event_time_not_future(past_param, now=now)

    def test_event_date_only_allowed(self):
        """Event with date only (no time) bypasses future check."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        date_only_param = AtParameter(date="2026-06-23", time=None)
        # Should not raise (date-only events have no time constraint)
        validate_event_time_not_future(date_only_param)

    def test_event_undated_allowed(self):
        """Undated event bypasses future check."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        undated_param = AtParameter(date=None, time=None)
        # Should not raise
        validate_event_time_not_future(undated_param)
