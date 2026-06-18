"""CLI entry point for timeline-cli using argparse."""

import argparse
import sys

from timeline_cli.version import get_version


def main() -> None:
    """Main entry point for timeline-cli."""
    parser = argparse.ArgumentParser(
        prog="timeline-cli",
        description="A CLI tool for managing daily events, todos, and notes with jsonline storage",
    )
    parser.add_argument("--version", action="version", version=f"timeline-cli {get_version()}")
    subparsers = parser.add_subparsers(dest="resource", help="Resource type")

    # Todo subcommands
    todo_parser = subparsers.add_parser("todo", help="Todo operations")
    todo_subparsers = todo_parser.add_subparsers(dest="action", help="Todo action")
    _setup_todo_commands(todo_subparsers)

    # Event subcommands
    event_parser = subparsers.add_parser("event", help="Event operations")
    event_subparsers = event_parser.add_subparsers(dest="action", help="Event action")
    _setup_event_commands(event_subparsers)

    # Note subcommands
    note_parser = subparsers.add_parser("note", help="Note operations")
    note_subparsers = note_parser.add_subparsers(dest="action", help="Note action")
    _setup_note_commands(note_subparsers)

    # Other commands
    _setup_other_commands(subparsers)

    args = parser.parse_args()

    if args.resource is None:
        parser.print_help()
        sys.exit(0)

    # Dispatch to command handlers
    _dispatch(args)


def _dispatch(args: argparse.Namespace) -> None:
    """Dispatch to appropriate command handler."""
    if args.resource == "init":
        from timeline_cli.commands.init import handle_init

        handle_init()
    elif args.resource == "todo":
        from timeline_cli.commands.todo import (
            handle_todo_abandon,
            handle_todo_add,
            handle_todo_complete,
            handle_todo_delete,
            handle_todo_edit,
            handle_todo_list,
        )

        if args.action == "add":
            handle_todo_add(args)
        elif args.action == "list":
            handle_todo_list(args)
        elif args.action == "complete":
            handle_todo_complete(args)
        elif args.action == "abandon":
            handle_todo_abandon(args)
        elif args.action == "edit":
            handle_todo_edit(args)
        elif args.action == "delete":
            handle_todo_delete(args)
        else:
            print(f"Todo action not implemented: {args.action}")
            sys.exit(1)
    elif args.resource == "event":
        from timeline_cli.commands.event import (
            handle_event_add,
            handle_event_delete,
            handle_event_edit,
            handle_event_list,
        )

        if args.action == "add":
            handle_event_add(args)
        elif args.action == "list":
            handle_event_list(args)
        elif args.action == "edit":
            handle_event_edit(args)
        elif args.action == "delete":
            handle_event_delete(args)
        else:
            print(f"Event action not implemented: {args.action}")
            sys.exit(1)
    elif args.resource == "note":
        from timeline_cli.commands.note import handle_note_add, handle_note_edit, handle_note_show

        if args.action == "add":
            handle_note_add(args)
        elif args.action == "show":
            handle_note_show(args)
        elif args.action == "edit":
            handle_note_edit(args)
        else:
            print(f"Note action not implemented: {args.action}")
            sys.exit(1)
    elif args.resource == "list":
        from timeline_cli.commands.list import handle_list

        handle_list(args)
    elif args.resource == "doctor":
        from timeline_cli.commands.doctor import handle_doctor

        handle_doctor(args)
    else:
        action = getattr(args, "action", None)
        print(f"Command not implemented yet: {args.resource} {action or ''}")
        sys.exit(1)


def _setup_todo_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup todo subcommand parsers."""
    # todo add (Issue #45: new order TEXT --date DATE --time TIME)
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("text", help="Todo text")
    add_parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    add_parser.add_argument("--time", help="Time in HH:MM format")
    add_parser.add_argument("--detail", action="append", help="Detail lines")

    # todo list (Issue #45: --range required)
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument(
        "--range",
        required=True,
        help="Date/time range (e.g., 'today', '..now', '2026-06-01..2026-06-30', '?')",
    )
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--show-id", action="store_true", help="Show todo IDs in output")
    list_parser.add_argument("--contains", help="Filter by text substring")
    list_parser.add_argument("--time", help="Filter by time (HH:MM)")
    list_parser.add_argument("--status", choices=["pending", "completed", "abandoned"], help="Filter by status")

    # todo complete (Issue #45: use --id)
    complete_parser = subparsers.add_parser("complete", help="Complete a todo")
    complete_parser.add_argument("--id", required=True, help="Todo ID (e.g., 't7b3k')")

    # todo abandon (Issue #45: use --id)
    abandon_parser = subparsers.add_parser("abandon", help="Abandon a todo")
    abandon_parser.add_argument("--id", required=True, help="Todo ID (e.g., 't7b3k')")

    # todo edit (Issue #45: use --id)
    edit_parser = subparsers.add_parser("edit", help="Edit a todo")
    edit_parser.add_argument("--id", required=True, help="Todo ID (e.g., 't7b3k')")
    edit_parser.add_argument("--new-text", help="New text")
    edit_parser.add_argument("--new-time", help="New time in HH:MM format")
    edit_parser.add_argument("--clear-time", action="store_true", help="Clear time field")
    edit_parser.add_argument("--append-detail", action="append", help="Append a detail line")
    edit_parser.add_argument("--set-detail", help="Replace all details (newline-separated)")

    # todo delete (Issue #45: use --id)
    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("--id", required=True, help="Todo ID (e.g., 't7b3k')")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")


def _setup_event_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup event subcommand parsers."""
    # event add (Issue #46: new order TEXT --date DATE --time TIME)
    add_parser = subparsers.add_parser("add", help="Add a new event")
    add_parser.add_argument("text", help="Event text")
    add_parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    add_parser.add_argument("--time", required=True, help="Time in HH:MM format")
    add_parser.add_argument("--detail", action="append", help="Detail lines")

    # event list (Issue #46: --range required)
    list_parser = subparsers.add_parser("list", help="List events")
    list_parser.add_argument("--range", required=True, help="Date/time range (e.g., 'today', '2026-06-01..2026-06-30')")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--show-id", action="store_true", help="Show event IDs in output")
    list_parser.add_argument("--contains", help="Filter by text substring")

    # event edit (Issue #46: use --id)
    edit_parser = subparsers.add_parser("edit", help="Edit an event")
    edit_parser.add_argument("--id", required=True, help="Event ID (e.g., 'e4x1m')")
    edit_parser.add_argument("--new-text", help="New text")
    edit_parser.add_argument("--new-time", help="New time in HH:MM format")
edit_parser.add_argument("--append-detail", action="append", help="Append a detail line")
    edit_parser.add_argument("--set-detail", help="Replace all details (newline-separated)")

    # event delete (Issue #46: use --id)
    delete_parser = subparsers.add_parser("delete", help="Delete an event")
    delete_parser.add_argument("--id", required=True, help="Event ID (e.g., 'e4x1m')")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")


def _setup_note_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup note subcommand parsers."""
    # note add
    add_parser = subparsers.add_parser("add", help="Add a note")
    add_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    add_parser.add_argument("text", help="Note text")

    # note show
    show_parser = subparsers.add_parser("show", help="Show a note")
    show_parser.add_argument("date", help="Date in YYYY-MM-DD format")

    # note edit
    edit_parser = subparsers.add_parser("edit", help="Edit a note")
    edit_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    edit_parser.add_argument("text", help="New note text")


def _setup_other_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup other command parsers."""
    # init
    subparsers.add_parser("init", help="Initialize .timelines.jsonl")

    # list
    list_parser = subparsers.add_parser("list", help="List all dates")
    list_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format")

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Validate data integrity")
    doctor_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")


if __name__ == "__main__":
    main()
