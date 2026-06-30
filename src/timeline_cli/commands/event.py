"""Handlers for ``timeline-cli event`` subcommands."""

from __future__ import annotations

import argparse

from timeline_cli.errors import TimelineValidationError
from timeline_cli.formatting import format_items_jsonl, format_items_markdown
from timeline_cli.storage import (
    add_event,
    delete_item,
    edit_event,
    filter_by_date,
    filter_by_text,
    parse_id,
    read_timeline,
    resolve_data_file,
    write_timeline,
)
from timeline_cli.time_expression import DateRange, TimePoint


def handle_event_add(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli event add <text> --at <expr>``."""
    tp = TimePoint.parse(args.at)
    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    event = add_event(items_mutable, text=args.text, tp=tp)

    write_timeline(data_file, header, items_mutable)
    print(f"created e{event.id}: {event.text} ({event.date} {event.time})")


def handle_event_list(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli event list --range <expr> [--with-text <text>] [--json]``."""
    if args.range_ is None and args.with_text is None:
        raise TimelineValidationError("At least one filter is required: --range or --with-text")

    date_range = DateRange.parse(args.range_) if args.range_ else None

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)

    # Filter to events only
    from timeline_cli.models import Event

    events = [item for item in items if isinstance(item, Event)]

    if date_range is not None:
        events = filter_by_date(events, date_range)
    if args.with_text is not None:
        events = filter_by_text(events, args.with_text)

    if args.json_output:
        output = format_items_jsonl(events)
    else:
        output = format_items_markdown(events)

    if output:
        print(output)


def handle_event_edit(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli event edit <id> [--new-text <text>] [--new-at <expr>]``."""
    if args.new_text is None and args.new_at is None:
        raise TimelineValidationError("At least one modification flag is required: --new-text or --new-at")

    id_ = parse_id(args.id, "event")
    new_tp = TimePoint.parse(args.new_at) if args.new_at else None

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    new_event, old_event = edit_event(items_mutable, id_, new_text=args.new_text, new_tp=new_tp)

    write_timeline(data_file, header, items_mutable)

    # Print diffs for changed fields
    diffs: list[str] = []
    if args.new_text is not None and new_event.text != old_event.text:
        diffs.append(f"text: {old_event.text} → {new_event.text}")
    if new_tp is not None:
        if new_event.date != old_event.date or new_event.time != old_event.time:
            old_dt = f"{old_event.date} {old_event.time}"
            new_dt = f"{new_event.date} {new_event.time}"
            diffs.append(f"time: {old_dt} → {new_dt}")

    if diffs:
        print(f"edited e{id_}: {', '.join(diffs)}")


def handle_event_delete(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli event delete <id> [--yes]``."""
    id_ = parse_id(args.id, "event")

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    # Find the item first (so we can show text in prompt and output)
    from timeline_cli.storage import _find_index

    idx = _find_index(items_mutable, "event", id_)
    target = items_mutable[idx]

    if not args.yes:
        answer = input(f"Delete e{id_}: {target.text}? [y/N] ")
        if answer.strip().lower() != "y":
            print("Cancelled.")
            return

    deleted = delete_item(items_mutable, "event", id_)

    write_timeline(data_file, header, items_mutable)
    print(f"deleted e{deleted.id}: {deleted.text}")
