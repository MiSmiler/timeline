"""Tests for TimeExpr parsing module (Issue #80)."""

import re
from datetime import datetime, timedelta

import pytest

from timeline_cli.time_expr import (
    DateRange,
    TimeExpr,
    Timepoint,
    Timerange,
    parse_timepoint,
    parse_timerange,
)
from timeline_cli.errors import TimelineValidationError


class TestTimepointParsing:
    """Tests for parse_timepoint function."""

    def test_parse_timepoint_datetime_with_T_separator(self):
        """parse_timepoint("2026-06-23T09:00") -> date=2026-06-23, time=09:00"""
        tp = parse_timepoint("2026-06-23T09:00")
        assert tp.date == "2026-06-23"
        assert tp.time == "09:00"
        assert not tp.is_undated
        assert not tp.is_now

    def test_parse_timepoint_explicit_date_only(self):
        """parse_timepoint("2026-06-23") -> date=2026-06-23, time=None"""
        tp = parse_timepoint("2026-06-23")
        assert tp.date == "2026-06-23"
        assert tp.time is None
        assert not tp.is_undated
        assert not tp.is_now

    def test_parse_timepoint_relative_date_today(self):
        """parse_timepoint("today") -> date=today's date, time=None"""
        tp = parse_timepoint("today")
        assert tp.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", tp.date)
        assert tp.time is None
        assert not tp.is_undated

    def test_parse_timepoint_relative_date_yesterday(self):
        """parse_timepoint("yesterday") -> date=yesterday's date"""
        tp = parse_timepoint("yesterday")
        assert tp.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", tp.date)
        assert tp.time is None

    def test_parse_timepoint_relative_date_tomorrow(self):
        """parse_timepoint("tomorrow") -> date=tomorrow's date"""
        tp = parse_timepoint("tomorrow")
        assert tp.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", tp.date)
        assert tp.time is None

    def test_parse_timepoint_today_with_T_separator(self):
        """parse_timepoint("todayT09:00") -> date=today, time=09:00"""
        tp = parse_timepoint("todayT09:00")
        assert tp.date is not None
        assert re.match(r"\d{4}-\d{2}-\d{2}", tp.date)
        assert tp.time == "09:00"
        assert not tp.is_undated
        assert not tp.is_now

    def test_parse_timepoint_yesterday_with_T_separator(self):
        """parse_timepoint("yesterdayT10:30") -> date=yesterday, time=10:30"""
        tp = parse_timepoint("yesterdayT10:30")
        assert tp.date is not None
        assert tp.time == "10:30"

    def test_parse_timepoint_tomorrow_with_T_separator(self):
        """parse_timepoint("tomorrowT08:00") -> date=tomorrow, time=08:00"""
        tp = parse_timepoint("tomorrowT08:00")
        assert tp.date is not None
        assert tp.time == "08:00"

    def test_parse_timepoint_time_only_auto_fill_today(self):
        """parse_timepoint("09:00") -> date=today, time=09:00"""
        tp = parse_timepoint("09:00")
        assert tp.date is not None  # auto-filled to today
        assert tp.time == "09:00"

    def test_parse_timepoint_time_only_various_times(self):
        """parse_timepoint accepts various HH:MM formats."""
        tp = parse_timepoint("15:30")
        assert tp.date is not None
        assert tp.time == "15:30"

        tp2 = parse_timepoint("23:59")
        assert tp2.time == "23:59"

        tp3 = parse_timepoint("00:00")
        assert tp3.time == "00:00"

    def test_parse_timepoint_undated_keyword(self):
        """parse_timepoint("undated") -> date=None, time=None, is_undated=True"""
        tp = parse_timepoint("undated")
        assert tp.date is None
        assert tp.time is None
        assert tp.is_undated
        assert not tp.is_now

    def test_parse_timepoint_now_keyword(self):
        """parse_timepoint("now") -> date=today, time=current, is_now=True"""
        now = datetime.now()
        tp = parse_timepoint("now")
        assert tp.date == now.date().isoformat()
        assert tp.time == now.strftime("%H:%M")
        assert not tp.is_undated
        assert tp.is_now

    def test_parse_timepoint_now_with_explicit_time(self):
        """parse_timepoint("now", now=explicit) uses provided datetime."""
        explicit_now = datetime(2026, 6, 23, 14, 30)
        tp = parse_timepoint("now", now=explicit_now)
        assert tp.date == "2026-06-23"
        assert tp.time == "14:30"
        assert tp.is_now

    def test_parse_timepoint_empty_boundary_marker(self):
        """parse_timepoint("") -> date=None, time=None (boundary marker)"""
        tp = parse_timepoint("")
        assert tp.date is None
        assert tp.time is None
        assert not tp.is_undated  # empty is boundary, not undated keyword
        assert not tp.is_now

    def test_parse_timepoint_space_separator_rejected(self):
        """parse_timepoint("2026-06-23 09:00") -> raise error (space separator rejected)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("2026-06-23 09:00")
        assert "T separator" in str(exc_info.value) or "space" in str(exc_info.value)

    def test_parse_timepoint_relative_date_space_time_rejected(self):
        """parse_timepoint("today 09:00") -> raise error (space separator rejected)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("today 09:00")
        assert "T separator" in str(exc_info.value) or "space" in str(exc_info.value)

    def test_parse_timepoint_invalid_time_format_rejected(self):
        """parse_timepoint("todayT25:00") -> raise error (invalid time)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("todayT25:00")
        assert "Invalid time" in str(exc_info.value)

    def test_parse_timepoint_invalid_time_format_hour_rejected(self):
        """parse_timepoint("todayT9:00") -> raise error (not HH:MM)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("todayT9:00")
        assert "Invalid time" in str(exc_info.value)

    def test_parse_timepoint_invalid_format_rejected(self):
        """parse_timepoint("invalid") -> raise error"""
        with pytest.raises(TimelineValidationError):
            parse_timepoint("invalid")

    def test_parse_timepoint_relative_offset_positive_hours(self):
        """parse_timepoint("+2h") -> date=today, time=current+2h"""
        now = datetime(2026, 6, 23, 10, 0)
        tp = parse_timepoint("+2h", now=now)
        assert tp.date == "2026-06-23"
        assert tp.time == "12:00"

    def test_parse_timepoint_relative_offset_negative_minutes(self):
        """parse_timepoint("-30m") -> date=today, time=current-30m"""
        now = datetime(2026, 6, 23, 10, 30)
        tp = parse_timepoint("-30m", now=now)
        assert tp.date == "2026-06-23"
        assert tp.time == "10:00"

    def test_parse_timepoint_relative_offset_combined(self):
        """parse_timepoint("+2h30m") -> date=today, time=current+2h30m"""
        now = datetime(2026, 6, 23, 10, 0)
        tp = parse_timepoint("+2h30m", now=now)
        assert tp.date == "2026-06-23"
        assert tp.time == "12:30"

    def test_parse_timepoint_relative_offset_exceeds_limit_rejected(self):
        """parse_timepoint("+100h") -> raise error (exceeds 72h limit)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("+100h")
        assert "72 hours" in str(exc_info.value)

    def test_parse_timepoint_relative_offset_negative_exceeds_limit_rejected(self):
        """parse_timepoint("-80h") -> raise error (exceeds -72h limit)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timepoint("-80h")
        assert "72 hours" in str(exc_info.value)


class TestTimepointHasTimeComponent:
    """Tests for Timepoint.has_time_component() method."""

    def test_has_time_component_with_time_true(self):
        """Timepoint with time -> has_time_component() returns True."""
        tp = Timepoint(date="2026-06-23", time="09:00")
        assert tp.has_time_component() is True

    def test_has_time_component_without_time_false(self):
        """Timepoint without time -> has_time_component() returns False."""
        tp = Timepoint(date="2026-06-23", time=None)
        assert tp.has_time_component() is False

    def test_has_time_component_undated_false(self):
        """Undated Timepoint -> has_time_component() returns False."""
        tp = Timepoint(date=None, time=None, is_undated=True)
        assert tp.has_time_component() is False

    def test_has_time_component_now_true(self):
        """Now Timepoint -> has_time_component() returns True."""
        tp = Timepoint(date="2026-06-23", time="14:30", is_now=True)
        assert tp.has_time_component() is True

    def test_has_time_component_now_without_explicit_time_true(self):
        """Now Timepoint (time implicit) -> has_time_component() returns True."""
        tp = Timepoint(date="2026-06-23", time=None, is_now=True)
        assert tp.has_time_component() is True  # now implies time exists


class TestTimerangeParsing:
    """Tests for parse_timerange function."""

    def test_parse_timerange_all(self):
        """parse_timerange("..") -> left=empty, right=empty"""
        tr = parse_timerange("..")
        assert tr.left.date is None
        assert tr.left.time is None
        assert tr.right.date is None
        assert tr.right.time is None

    def test_parse_timerange_date_range(self):
        """parse_timerange("2026-06-23..2026-06-25") -> left=2026-06-23, right=2026-06-25"""
        tr = parse_timerange("2026-06-23..2026-06-25")
        assert tr.left.date == "2026-06-23"
        assert tr.left.time is None
        assert tr.right.date == "2026-06-25"
        assert tr.right.time is None

    def test_parse_timerange_relative_range(self):
        """parse_timerange("yesterday..today") -> left=yesterday, right=today"""
        tr = parse_timerange("yesterday..today")
        assert tr.left.date is not None
        assert tr.right.date is not None

    def test_parse_timerange_open_start(self):
        """parse_timerange("..today") -> left=empty, right=today"""
        tr = parse_timerange("..today")
        assert tr.left.date is None
        assert tr.right.date is not None

    def test_parse_timerange_open_end(self):
        """parse_timerange("today..") -> left=today, right=empty"""
        tr = parse_timerange("today..")
        assert tr.left.date is not None
        assert tr.right.date is None

    def test_parse_timerange_time_range(self):
        """parse_timerange("09:00..17:00") -> left=todayT09:00, right=todayT17:00"""
        tr = parse_timerange("09:00..17:00")
        assert tr.left.time == "09:00"
        assert tr.right.time == "17:00"
        # Both auto-filled to today
        assert tr.left.date is not None
        assert tr.right.date is not None

    def test_parse_timerange_datetime_range(self):
        """parse_timerange("2026-06-23T09:00..2026-06-23T17:00")"""
        tr = parse_timerange("2026-06-23T09:00..2026-06-23T17:00")
        assert tr.left.date == "2026-06-23"
        assert tr.left.time == "09:00"
        assert tr.right.date == "2026-06-23"
        assert tr.right.time == "17:00"

    def test_parse_timerange_date_with_time_range(self):
        """parse_timerange("todayT09:00..todayT17:00")"""
        tr = parse_timerange("todayT09:00..todayT17:00")
        assert tr.left.time == "09:00"
        assert tr.right.time == "17:00"

    def test_parse_timerange_mixed_range(self):
        """parse_timerange("2026-06-23..today")"""
        tr = parse_timerange("2026-06-23..today")
        assert tr.left.date == "2026-06-23"
        assert tr.right.date is not None  # today

    def test_parse_timerange_undated_rejected(self):
        """parse_timerange with undated keyword raises error."""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timerange("undated..today")
        assert "undated" in str(exc_info.value)

    def test_parse_timerange_reversed_rejected(self):
        """parse_timerange("2026-06-25..2026-06-23") -> raise error (reversed)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timerange("2026-06-25..2026-06-23")
        error_msg = str(exc_info.value).lower()
        assert "reversed" in error_msg or "left < right" in error_msg or "before" in error_msg

    def test_parse_timerange_reversed_time_rejected(self):
        """parse_timerange("17:00..09:00") -> raise error (reversed time)"""
        with pytest.raises(TimelineValidationError) as exc_info:
            parse_timerange("17:00..09:00")
        error_msg = str(exc_info.value).lower()
        assert "reversed" in error_msg or "left < right" in error_msg or "before" in error_msg

    def test_parse_timerange_same_date_allowed(self):
        """parse_timerange("2026-06-23..2026-06-23") -> allowed (same day)"""
        tr = parse_timerange("2026-06-23..2026-06-23")
        assert tr.left.date == "2026-06-23"
        assert tr.right.date == "2026-06-23"

    def test_parse_timerange_same_datetime_allowed(self):
        """parse_timerange("2026-06-23T09:00..2026-06-23T09:00") -> allowed"""
        tr = parse_timerange("2026-06-23T09:00..2026-06-23T09:00")
        assert tr.left.date == "2026-06-23"
        assert tr.left.time == "09:00"
        assert tr.right.date == "2026-06-23"
        assert tr.right.time == "09:00"


class TestTimerangeExpansion:
    """Tests for Timerange.expand_for_query() method."""

    def test_expand_date_only_left(self):
        """Date-only left -> expanded to dateT00:00"""
        tr = parse_timerange("2026-06-23..")
        dr = tr.expand_for_query()
        assert dr.start.hour == 0
        assert dr.start.minute == 0
        assert dr.start.date().isoformat() == "2026-06-23"

    def test_expand_date_only_right(self):
        """Date-only right -> expanded to dateT23:59"""
        tr = parse_timerange("..2026-06-23")
        dr = tr.expand_for_query()
        assert dr.end.hour == 23
        assert dr.end.minute == 59
        assert dr.end.date().isoformat() == "2026-06-23"

    def test_expand_full_day_range(self):
        """date..date -> full day range T00:00..T23:59"""
        tr = parse_timerange("2026-06-23..2026-06-25")
        dr = tr.expand_for_query()
        assert dr.start.hour == 0
        assert dr.start.minute == 0
        assert dr.start.date().isoformat() == "2026-06-23"
        assert dr.end.hour == 23
        assert dr.end.minute == 59
        assert dr.end.date().isoformat() == "2026-06-25"

    def test_expand_empty_left_no_lower_bound(self):
        """Empty left -> no lower bound"""
        tr = parse_timerange("..2026-06-23")
        dr = tr.expand_for_query()
        assert dr.start is None
        assert dr.end is not None

    def test_expand_empty_right_no_upper_bound(self):
        """Empty right -> no upper bound"""
        tr = parse_timerange("2026-06-23..")
        dr = tr.expand_for_query()
        assert dr.start is not None
        assert dr.end is None

    def test_expand_all_range(self):
        """.. -> no bounds"""
        tr = parse_timerange("..")
        dr = tr.expand_for_query()
        assert dr.start is None
        assert dr.end is None

    def test_expand_time_only_auto_fills_today(self):
        """Time-only -> auto-fills date=today"""
        now = datetime(2026, 6, 23, 10, 0)
        tr = parse_timerange("09:00..17:00", now=now)
        dr = tr.expand_for_query(now=now)
        assert dr.start.date().isoformat() == "2026-06-23"
        assert dr.start.hour == 9
        assert dr.end.date().isoformat() == "2026-06-23"
        assert dr.end.hour == 17

    def test_expand_datetime_no_modification(self):
        """Datetime (date+time) -> no expansion needed"""
        tr = parse_timerange("2026-06-23T09:00..2026-06-23T17:00")
        dr = tr.expand_for_query()
        assert dr.start.hour == 9
        assert dr.end.hour == 17


class TestTimeExprParsing:
    """Tests for TimeExpr.parse() routing."""

    def test_parse_timeexpr_detects_timepoint(self):
        """Single value -> TimeExpr(kind='timepoint')"""
        te = TimeExpr.parse("today")
        assert te.kind == "timepoint"
        assert te.timepoint is not None
        assert te.timerange is None

    def test_parse_timeexpr_detects_timerange(self):
        """Range value -> TimeExpr(kind='timerange')"""
        te = TimeExpr.parse("today..tomorrow")
        assert te.kind == "timerange"
        assert te.timerange is not None
        assert te.timepoint is None

    def test_parse_timeexpr_undated_is_timepoint(self):
        """undated -> TimeExpr(kind='timepoint', is_undated=True)"""
        te = TimeExpr.parse("undated")
        assert te.kind == "timepoint"
        assert te.timepoint.is_undated

    def test_parse_timeexpr_now_is_timepoint(self):
        """now -> TimeExpr(kind='timepoint', is_now=True)"""
        te = TimeExpr.parse("now")
        assert te.kind == "timepoint"
        assert te.timepoint.is_now

    def test_parse_timeexpr_empty_is_timerange(self):
        """.. -> TimeExpr(kind='timerange')"""
        te = TimeExpr.parse("..")
        assert te.kind == "timerange"

    def test_parse_timeexpr_with_explicit_now(self):
        """TimeExpr.parse with now parameter uses provided datetime."""
        explicit_now = datetime(2026, 6, 23, 14, 30)
        te = TimeExpr.parse("today", now=explicit_now)
        assert te.timepoint.date == "2026-06-23"

        te2 = TimeExpr.parse("09:00", now=explicit_now)
        assert te2.timepoint.date == "2026-06-23"
        assert te2.timepoint.time == "09:00"


class TestDateRangeDataclass:
    """Tests for DateRange compatibility."""

    def test_daterange_from_timerange(self):
        """Timerange.expand_for_query returns DateRange."""
        tr = parse_timerange("2026-06-23..2026-06-25")
        dr = tr.expand_for_query()
        assert hasattr(dr, "start")
        assert hasattr(dr, "end")
        assert hasattr(dr, "include_undated")

    def test_daterange_empty_bounds(self):
        """DateRange with None bounds represents unbounded range."""
        from datetime import date

        dr = DateRange(start=None, end=None)
        assert dr.start is None
        assert dr.end is None

    def test_daterange_include_undated_flag(self):
        """DateRange has include_undated flag."""
        dr = DateRange(include_undated=True)
        assert dr.include_undated is True