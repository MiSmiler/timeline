"""Custom exceptions for timeline-cli."""


class TimelineError(Exception):
    """Base error for timeline-cli."""

    exit_code = 1


class TimelineFileNotFoundError(TimelineError):
    """Timeline file not found."""

    def __init__(self, path: str):
        super().__init__("Timeline file not found. Run 'timeline-cli init' to create one.")
        self.path = path


class TimelineValidationError(TimelineError):
    """User input validation failed."""

    pass


class TimelineInternalError(TimelineError):
    """Internal/unexpected error."""

    exit_code = 2
