"""Handlers for ``timeline-cli note`` subcommands."""

from __future__ import annotations

import argparse

from timeline_cli.errors import TimelineValidationError
from timeline_cli.formatting import format_items_jsonl, format_items_markdown
from timeline_cli.storage import (
    add_note,
    delete_item,
    edit_note,
    filter_by_date,
    filter_by_text,
    parse_id,
    read_timeline,
    resolve_data_file,
    write_timeline,
)
from timeline_cli.time_expression import DateRange, TimePoint


def handle_note_add(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli note add <text> --at <expr>``."""
    tp = TimePoint.parse(args.at)
    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    note = add_note(items_mutable, text=args.text, tp=tp)

    write_timeline(data_file, header, items_mutable)
    print(f"created n{note.id}: {note.text} ({note.date})")


def handle_note_list(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli note list --range <expr> [--with-text <text>] [--json]``."""
    if args.range_ is None and args.with_text is None:
        raise TimelineValidationError("At least one filter is required: --range or --with-text")

    date_range = DateRange.parse(args.range_) if args.range_ else None

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)

    # Filter to notes only
    from timeline_cli.models import Note

    notes = [item for item in items if isinstance(item, Note)]

    if date_range is not None:
        notes = filter_by_date(notes, date_range)
    if args.with_text is not None:
        notes = filter_by_text(notes, args.with_text)

    if args.json_output:
        output = format_items_jsonl(notes)
    else:
        output = format_items_markdown(notes)

    if output:
        print(output)


def handle_note_edit(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli note edit <id> [--new-text <text>] [--new-at <expr>]``."""
    if args.new_text is None and args.new_at is None:
        raise TimelineValidationError("At least one modification flag is required: --new-text or --new-at")

    id_ = parse_id(args.id, "note")
    new_tp = TimePoint.parse(args.new_at) if args.new_at else None

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    new_note, old_note = edit_note(items_mutable, id_, new_text=args.new_text, new_tp=new_tp)

    write_timeline(data_file, header, items_mutable)

    # Print diffs for changed fields
    diffs: list[str] = []
    if args.new_text is not None and new_note.text != old_note.text:
        diffs.append(f"text: {old_note.text} → {new_note.text}")
    if new_tp is not None and new_note.date != old_note.date:
        diffs.append(f"date: {old_note.date} → {new_note.date}")

    if diffs:
        print(f"edited n{id_}: {', '.join(diffs)}")


def handle_note_delete(args: argparse.Namespace) -> None:
    """Handle ``timeline-cli note delete <id> [--yes]``."""
    id_ = parse_id(args.id, "note")

    data_file = resolve_data_file()
    header, items = read_timeline(data_file)
    items_mutable = list(items)

    # Find the item first (so we can show text in prompt and output)
    from timeline_cli.storage import _find_index

    idx = _find_index(items_mutable, "note", id_)
    target = items_mutable[idx]

    if not args.yes:
        answer = input(f"Delete n{id_}: {target.text}? [y/N] ")
        if answer.strip().lower() != "y":
            print("Cancelled.")
            return

    deleted = delete_item(items_mutable, "note", id_)

    write_timeline(data_file, header, items_mutable)
    print(f"deleted n{deleted.id}: {deleted.text}")
