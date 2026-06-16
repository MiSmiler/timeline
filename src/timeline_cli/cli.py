"""CLI entry point for timeline-cli using argparse."""

import argparse
import sys


def main() -> None:
    """Main entry point for timeline-cli."""
    parser = argparse.ArgumentParser(
        prog="timeline-cli",
        description="A CLI tool for managing daily events, todos, and notes with jsonline storage",
    )
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

    # Dispatch to command handlers (to be implemented in #8)
    print(f"Command not implemented yet: {args.resource} {args.action}")
    sys.exit(1)


def _setup_todo_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup todo subcommand parsers."""
    # todo add
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    add_parser.add_argument("text", help="Todo text")
    add_parser.add_argument("--time", help="Time in HH:MM format")
    add_parser.add_argument("--detail", action="append", help="Detail lines")

    # todo list
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    list_parser.add_argument("--time", help="Filter by time (HH:MM)")
    list_parser.add_argument("--status", choices=["pending", "completed", "abandoned"], help="Filter by status")
    list_parser.add_argument("--overdue", action="store_true", help="Show overdue todos")
    list_parser.add_argument("--undated", action="store_true", help="Show undated todos")
    list_parser.add_argument("text_prefix", nargs="?", help="Filter by text prefix")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--simple", action="store_true", help="Output as simple text")

    # todo complete
    complete_parser = subparsers.add_parser("complete", help="Complete a todo")
    complete_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    complete_parser.add_argument("--time", help="Time in HH:MM format")
    complete_parser.add_argument("text_prefix", help="Text prefix to locate todo")

    # todo abandon
    abandon_parser = subparsers.add_parser("abandon", help="Abandon a todo")
    abandon_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    abandon_parser.add_argument("--time", help="Time in HH:MM format")
    abandon_parser.add_argument("text_prefix", help="Text prefix to locate todo")

    # todo edit
    edit_parser = subparsers.add_parser("edit", help="Edit a todo")
    edit_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    edit_parser.add_argument("--time", help="Time in HH:MM format")
    edit_parser.add_argument("text_prefix", help="Text prefix to locate todo")
    edit_parser.add_argument("--new-text", help="New text")
    edit_parser.add_argument("--new-time", help="New time in HH:MM format")
    edit_parser.add_argument("--append-detail", help="Append a detail line")
    edit_parser.add_argument("--set-detail", action="append", help="Replace all details")

    # todo move
    move_parser = subparsers.add_parser("move", help="Move a todo to another date")
    move_parser.add_argument("from_date", help="Current date (YYYY-MM-DD)")
    move_parser.add_argument("to_date", help="Target date (YYYY-MM-DD)")
    move_parser.add_argument("--time", help="Time in HH:MM format")
    move_parser.add_argument("text_prefix", help="Text prefix to locate todo")

    # todo delete
    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    delete_parser.add_argument("--time", help="Time in HH:MM format")
    delete_parser.add_argument("text_prefix", help="Text prefix to locate todo")
    delete_parser.add_argument("--yes", action="store_true", help="Skip confirmation")


def _setup_event_commands(subparsers: argparse._SubParsersAction) -> None:
    """Setup event subcommand parsers."""
    # event add
    add_parser = subparsers.add_parser("add", help="Add a new event")
    add_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    add_parser.add_argument("--time", required=True, help="Time in HH:MM format")
    add_parser.add_argument("text", help="Event text")
    add_parser.add_argument("--detail", action="append", help="Detail lines")

    # event list
    list_parser = subparsers.add_parser("list", help="List events")
    list_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--simple", action="store_true", help="Output as simple text")

    # event edit
    edit_parser = subparsers.add_parser("edit", help="Edit an event")
    edit_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    edit_parser.add_argument("time", help="Time in HH:MM format")
    edit_parser.add_argument("text_prefix", help="Text prefix to locate event")
    edit_parser.add_argument("--new-text", help="New text")
    edit_parser.add_argument("--new-time", help="New time in HH:MM format")
    edit_parser.add_argument("--append-detail", help="Append a detail line")
    edit_parser.add_argument("--set-detail", action="append", help="Replace all details")

    # event delete
    delete_parser = subparsers.add_parser("delete", help="Delete an event")
    delete_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    delete_parser.add_argument("time", help="Time in HH:MM format")
    delete_parser.add_argument("text_prefix", help="Text prefix to locate event")
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
    subparsers.add_parser("init", help="Initialize timelines.jsonl")

    # list
    list_parser = subparsers.add_parser("list", help="List all dates")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # export
    export_parser = subparsers.add_parser("export", help="Export a date as markdown")
    export_parser.add_argument("date", help="Date in YYYY-MM-DD format")
    export_parser.add_argument("--output-dir", required=True, help="Output directory")

    # export-all
    export_all_parser = subparsers.add_parser("export-all", help="Export all dates as markdown")
    export_all_parser.add_argument("--output-dir", required=True, help="Output directory")

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Validate data integrity")
    doctor_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")

    # migrate
    migrate_parser = subparsers.add_parser("migrate", help="Migrate schema version")
    migrate_parser.add_argument("--to", type=int, required=True, help="Target schema version")


if __name__ == "__main__":
    main()
