# Timeline CLI

A todo/event/note management tool designed for AI agents, using jsonline storage.

## Installation

```bash
# Recommended: global installation (isolated environment)
uv tool install .

# Or development mode
uv sync
```

## Usage

```bash
# Initialize timeline directory
timeline-cli init

# View today's diary
timeline-cli diary today

# Add a todo
timeline-cli todo add "Review PR" --at today

# Add an event
timeline-cli event add "Meeting with team" --at todayT10:00

# List todos with structured output (for agents)
timeline-cli todo list --at today --json

# Complete a todo by ID
timeline-cli todo complete --id tabc12
```

For all commands and options, run `timeline-cli --help`.

## Development

```bash
# Install dependencies
uv sync

# Run CLI
uv run timeline-cli --help

# Format code
uv run ruff format

# Lint code
uv run ruff check

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_todo.py -v

# Run CLI from another directory
uv run --project /path/to/timeline timeline-cli init
```

## Documentation

- `timeline-cli --help` - View all commands
- [CONTEXT.md](CONTEXT.md) - Domain terminology and concepts
- [docs/adr/](docs/adr/) - Architecture decision records