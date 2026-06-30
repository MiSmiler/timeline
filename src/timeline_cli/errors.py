"""Custom exceptions for timeline-cli.

Exit code convention: 1 = user error, 2 = internal bug.
"""


class TimelineError(Exception):
    """Base error for timeline-cli (exit_code 1 = user error)."""

    exit_code = 1


class TimelineFileNotFoundError(TimelineError):
    """Timeline file not found."""

    def __init__(self, path: str):
        super().__init__(f"No timeline found. Run 'timeline-cli init' to initialize.\nExpected: {path}")
        self.path = path


class TimelineValidationError(TimelineError):
    """User input validation failed."""

    pass


class TimelineInternalError(TimelineError):
    """Internal error (exit_code 2 = bug, should be reported)."""

    exit_code = 2
