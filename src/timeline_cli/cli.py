"""CLI entry point for timeline-cli using argparse."""

from __future__ import annotations

import argparse
import sys

from timeline_cli.errors import TimelineError, TimelineValidationError
from timeline_cli.version import get_version


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for timeline-cli.

    Returns:
        Configured ArgumentParser with all subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="timeline-cli",
        description="A CLI tool for managing daily events and notes with jsonline storage",
    )
    parser.add_argument("--version", action="version", version=f"timeline-cli {get_version()}")
    parser.add_argument("--debug", action="store_true", help="Show full stack trace for errors")

    subparsers = parser.add_subparsers(dest="resource", help="Resource type")

    # --- init ---
    subparsers.add_parser("init", help="Initialize .timeline directory")

    # --- event ---
    event_parser = subparsers.add_parser("event", help="Manage events")
    event_actions = event_parser.add_subparsers(dest="action", help="Action")

    # event add
    event_add_parser = event_actions.add_parser("add", help="Add an event")
    event_add_parser.add_argument("text", help="Event description text")
    event_add_parser.add_argument("--at", required=True, help="Time expression (now, todayT14:00, 2026-06-26T09:30)")

    # event list
    event_list_parser = event_actions.add_parser("list", help="List events")
    event_list_parser.add_argument(
        "--range",
        dest="range_",
        default=None,
        help="Date range expression (today, 2026-06-20..2026-06-26, ..)",
    )
    event_list_parser.add_argument("--with-text", default=None, help="Filter by text substring")
    event_list_parser.add_argument("--json", dest="json_output", action="store_true", help="Output raw JSONL")

    # event edit
    event_edit_parser = event_actions.add_parser("edit", help="Edit an event")
    event_edit_parser.add_argument("id", help="Event ID (e.g., e1)")
    event_edit_parser.add_argument("--new-text", default=None, help="New event text")
    event_edit_parser.add_argument("--new-at", default=None, help="New time expression")

    # event delete
    event_delete_parser = event_actions.add_parser("delete", help="Delete an event")
    event_delete_parser.add_argument("id", help="Event ID (e.g., e1)")
    event_delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    # --- note ---
    note_parser = subparsers.add_parser("note", help="Manage notes")
    note_actions = note_parser.add_subparsers(dest="action", help="Action")

    # note add
    note_add_parser = note_actions.add_parser("add", help="Add a note")
    note_add_parser.add_argument("text", help="Note text")
    note_add_parser.add_argument("--at", required=True, help="Time expression (date-only, e.g., today, 2026-06-26)")

    # note list
    note_list_parser = note_actions.add_parser("list", help="List notes")
    note_list_parser.add_argument("--range", dest="range_", default=None, help="Date range expression")
    note_list_parser.add_argument("--with-text", default=None, help="Filter by text substring")
    note_list_parser.add_argument("--json", dest="json_output", action="store_true", help="Output raw JSONL")

    # note edit
    note_edit_parser = note_actions.add_parser("edit", help="Edit a note")
    note_edit_parser.add_argument("id", help="Note ID (e.g., n1)")
    note_edit_parser.add_argument("--new-text", default=None, help="New note text")
    note_edit_parser.add_argument("--new-at", default=None, help="New time expression")

    # note delete
    note_delete_parser = note_actions.add_parser("delete", help="Delete a note")
    note_delete_parser.add_argument("id", help="Note ID (e.g., n1)")
    note_delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    return parser


def _dispatch(args: argparse.Namespace) -> None:
    """Dispatch to appropriate command handler.

    Args:
        args: Parsed CLI arguments.
    """
    if args.resource == "init":
        from timeline_cli.commands.init import handle_init

        handle_init(args)
        return

    if args.resource == "event":
        from timeline_cli.commands.event import (
            handle_event_add,
            handle_event_delete,
            handle_event_edit,
            handle_event_list,
        )

        action_map = {
            "add": handle_event_add,
            "list": handle_event_list,
            "edit": handle_event_edit,
            "delete": handle_event_delete,
        }
    elif args.resource == "note":
        from timeline_cli.commands.note import (
            handle_note_add,
            handle_note_delete,
            handle_note_edit,
            handle_note_list,
        )

        action_map = {
            "add": handle_note_add,
            "list": handle_note_list,
            "edit": handle_note_edit,
            "delete": handle_note_delete,
        }
    else:
        raise TimelineValidationError(f"Unknown resource: {args.resource}")

    handler = action_map.get(args.action)
    if handler is None:
        raise TimelineValidationError(f"Command not implemented yet: {args.resource} {args.action or ''}".strip())

    handler(args)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for timeline-cli.

    Args:
        argv: Command-line arguments.  Reads sys.argv if None.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.resource is None:
        parser.print_help()
        sys.exit(0)

    try:
        _dispatch(args)
    except TimelineError as e:
        _handle_error(e, args.debug)
    except Exception as e:
        if args.debug:
            raise
        _handle_error(TimelineError(str(e)), debug=True, show_debug_hint=True)


def _handle_error(
    error: TimelineError,
    debug: bool = False,
    show_debug_hint: bool = False,
) -> None:
    """Print error to stderr and exit.

    exit_code 1 (user error): print message only.
    exit_code 2 (internal bug): also prompt --debug / report, unless debug
                                 is on in which case re-raise for full stack.
    """
    if debug and error.exit_code == 2:
        raise error
    print(f"Error: {error}", file=sys.stderr)
    if show_debug_hint or (error.exit_code == 2 and not debug):
        print("Run with --debug for details or report a bug.", file=sys.stderr)
    sys.exit(error.exit_code)


if __name__ == "__main__":
    main()
