"""CLI entry point for timeline-cli using argparse."""

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
    subparsers.add_parser("init", help="Initialize .timeline directory")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point for timeline-cli.

    Args:
        argv: Command-line arguments. Reads sys.argv if None.
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


def _dispatch(args: argparse.Namespace) -> None:
    """Dispatch to appropriate command handler.

    Args:
        args: Parsed CLI arguments.

    Raises:
        TimelineValidationError: If the command is not implemented.
    """
    if args.resource == "init":
        from timeline_cli.commands.init import handle_init

        handle_init(args)
    else:
        action = getattr(args, "action", None)
        raise TimelineValidationError(f"Command not implemented yet: {args.resource} {action or ''}".strip())


def _handle_error(
    error: TimelineError,
    debug: bool = False,
    show_debug_hint: bool = False,
) -> None:
    """Print error to stderr and exit.

    exit_code 1 (user error): print message only.
    exit_code 2 (internal bug): also prompt --debug / report, unless debug is on
                                in which case re-raise for full stack trace.
    """
    if debug and error.exit_code == 2:
        raise error
    print(f"Error: {error}", file=sys.stderr)
    if show_debug_hint or (error.exit_code == 2 and not debug):
        print("Run with --debug for details or report a bug.", file=sys.stderr)
    sys.exit(error.exit_code)


if __name__ == "__main__":
    main()
