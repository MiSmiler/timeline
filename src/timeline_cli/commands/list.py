"""List command implementation."""

import json

from timeline_cli.storage import DEFAULT_STORAGE_FILE, read_timeline


def handle_list(args) -> None:
    """Handle list command - list all dates."""
    timeline = read_timeline(DEFAULT_STORAGE_FILE)

    dates = sorted(timeline.records.keys())

    if args.json:
        print(json.dumps(dates))
    else:
        if not dates:
            print("No dates found")
            return
        for date in dates:
            print(date)
