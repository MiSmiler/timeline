"""Tests for parse_at_parameter function."""

import re
from datetime import date, datetime
from unittest.mock import patch

import pytest

from timeline_cli.range_parser import parse_at_parameter


class TestParseAtBasic:
    """Tests for Slice 1: basic parsing."""

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

    def test_parse_at_relative_date_today(self):
        """--at "today" → date=today, time=None"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("today")
            assert result.date == "2026-06-22"
            assert result.time is None

    def test_parse_at_relative_date_yesterday(self):
        """--at "yesterday" → date=yesterday, time=None"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("yesterday")
            assert result.date == "2026-06-21"
            assert result.time is None

    def test_parse_at_relative_date_tomorrow(self):
        """--at "tomorrow" → date=tomorrow, time=None"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("tomorrow")
            assert result.date == "2026-06-23"
            assert result.time is None

    def test_parse_at_undated(self):
        """--at "" → date=None, time=None"""
        result = parse_at_parameter("")
        assert result.date is None
        assert result.time is None


class TestParseAtRelativeDateWithTime:
    """Tests for Slice 2: relative date + explicit time."""

    def test_parse_at_today_with_time(self):
        """--at "today 15:00" → date=today, time=15:00"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("today 15:00")
            assert result.date == "2026-06-22"
            assert result.time == "15:00"

    def test_parse_at_yesterday_with_time(self):
        """--at "yesterday 10:00" → date=yesterday, time=10:00"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("yesterday 10:00")
            assert result.date == "2026-06-21"
            assert result.time == "10:00"

    def test_parse_at_tomorrow_with_time(self):
        """--at "tomorrow 09:00" → date=tomorrow, time=09:00"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("tomorrow 09:00")
            assert result.date == "2026-06-23"
            assert result.time == "09:00"


class TestParseAtTimeOnly:
    """Tests for Slice 3: time only defaults to today."""

    def test_parse_at_time_only_defaults_today(self):
        """--at "15:00" → date=today, time=15:00"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("15:00")
            assert result.date == "2026-06-22"
            assert result.time == "15:00"

    def test_parse_at_time_only_early_morning(self):
        """--at "09:30" → date=today, time=09:30"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            result = parse_at_parameter("09:30")
            assert result.date == "2026-06-22"
            assert result.time == "09:30"


class TestParseAtNow:
    """Tests for Slice 4: 'now' keyword."""

    def test_parse_at_now(self):
        """--at "now" → date=today, time=current HH:MM"""
        with patch("timeline_cli.range_parser.date") as mock_date:
            mock_date.today.return_value = date(2026, 6, 22)
            with patch("timeline_cli.range_parser.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2026, 6, 22, 14, 30)
                result = parse_at_parameter("now")
                assert result.date == "2026-06-22"
                assert result.time == "14:30"

    def test_parse_at_now_time_format(self):
        """--at "now" time should be HH:MM format"""
        result = parse_at_parameter("now")
        assert re.match(r"\d{2}:\d{2}", result.time)


class TestParseAtRelativeOffset:
    """Tests for Slice 5: relative time offset."""

    def test_parse_at_positive_offset_hours(self):
        """--at "+2h" → date=today, time=now+2h"""
        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 10, 0)
            result = parse_at_parameter("+2h")
            assert result.date == "2026-06-22"
            assert result.time == "12:00"

    def test_parse_at_negative_offset_minutes(self):
        """--at "-30m" → date=today, time=now-30m"""
        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 10, 0)
            result = parse_at_parameter("-30m")
            assert result.date == "2026-06-22"
            assert result.time == "09:30"

    def test_parse_at_combined_offset(self):
        """--at "+2h30m" → date=today, time=now+2h30m"""
        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 10, 0)
            result = parse_at_parameter("+2h30m")
            assert result.date == "2026-06-22"
            assert result.time == "12:30"

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
        from timeline_cli.range_parser import validate_event_time_not_future

        # Mock now to be 2026-06-22 14:00
        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 14, 0)
            mock_datetime.combine = datetime.combine

            # Create AtParameter directly (bypass parse to avoid mock issues)
            from timeline_cli.range_parser import AtParameter

            future_param = AtParameter(date="2026-06-22", time="16:00")
            with pytest.raises(TimelineValidationError) as exc_info:
                validate_event_time_not_future(future_param)
            assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_tomorrow_rejected(self):
        """Event with tomorrow's date is rejected."""
        from timeline_cli.errors import TimelineValidationError
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 14, 0)
            mock_datetime.combine = datetime.combine

            future_param = AtParameter(date="2026-06-23", time="10:00")
            with pytest.raises(TimelineValidationError) as exc_info:
                validate_event_time_not_future(future_param)
            assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_past_allowed(self):
        """Event with past datetime is allowed."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 14, 0)
            mock_datetime.combine = datetime.combine

            past_param = AtParameter(date="2026-06-22", time="10:00")
            # Should not raise
            validate_event_time_not_future(past_param)

    def test_event_at_offset_future_rejected(self):
        """Event with +2h offset (future) is rejected."""
        from timeline_cli.errors import TimelineValidationError
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        # Create AtParameter directly representing +2h from 10:00 = 12:00
        # Then check validation at 10:00
        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 10, 0)
            mock_datetime.combine = datetime.combine

            future_param = AtParameter(date="2026-06-22", time="12:00")
            with pytest.raises(TimelineValidationError) as exc_info:
                validate_event_time_not_future(future_param)
            assert "cannot be later than now" in str(exc_info.value)

    def test_event_at_offset_past_allowed(self):
        """Event with -2h offset (past) is allowed."""
        from timeline_cli.range_parser import AtParameter, validate_event_time_not_future

        with patch("timeline_cli.range_parser.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 6, 22, 14, 0)
            mock_datetime.combine = datetime.combine

            past_param = AtParameter(date="2026-06-22", time="12:00")
            # Should not raise
            validate_event_time_not_future(past_param)

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
