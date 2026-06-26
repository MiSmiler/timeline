"""CLI entry point for timeline-cli using argparse."""

import argparse
import sys

from timeline_cli.errors import TimelineError
from timeline_cli.version import get_version


def main() -> None:
    """Main entry point for timeline-cli."""
    parser = argparse.ArgumentParser(
        prog="timeline-cli",
        description="A CLI tool for managing daily events and notes with jsonline storage",
    )
    parser.add_argument("--version", action="version", version=f"timeline-cli {get_version()}")
    parser.add_argument("--debug", action="store_true", help="Show full stack trace for errors")
    subparsers = parser.add_subparsers(dest="resource", help="Resource type")

    # Init command
    subparsers.add_parser("init", help="Initialize .timeline directory")

    args = parser.parse_args()

    if args.resource is None:
        parser.print_help()
        sys.exit(0)

    try:
        _dispatch(args)
    except TimelineError as e:
        if args.debug and e.exit_code == 2:
            raise
        print(f"Error: {e}", file=sys.stderr)
        if e.exit_code == 2 and not args.debug:
            print("Run with --debug for details or report a bug.", file=sys.stderr)
        sys.exit(e.exit_code)
    except Exception as e:
        if args.debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        print("Run with --debug for details or report a bug.", file=sys.stderr)
        sys.exit(2)


def _dispatch(args: argparse.Namespace) -> None:
    """Dispatch to appropriate command handler."""
    if args.resource == "init":
        from timeline_cli.commands.init import handle_init

        handle_init(args)
    else:
        action = getattr(args, "action", None)
        print(f"Command not implemented yet: {args.resource} {action or ''}")
        sys.exit(1)


if __name__ == "__main__":
    main()
