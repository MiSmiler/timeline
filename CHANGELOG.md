# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-06-17

### Added

#### ID System (Issue #42)
- Introduce unique ID for Todo and Event items
- ID format: `t<random>` for todos, `e<random>` for events (5-char random ID)
- ID generation on item creation
- ID display in all list outputs (table, JSON, simple)
- ID lookup functions: `find_todo_by_id()`, `find_event_by_id()`
- Cross-record ID lookup: `find_todo_by_id_in_timeline()`, `find_event_by_id_in_timeline()`

#### Range Filtering (Issue #43)
- New `--range` parameter for `todo list` and `event list`
- Supported formats:
  - `..` - all items
  - `today` - current day
  - `..today` / `today..` - relative to today
  - `YYYY-MM-DD` - specific date
  - `YYYY-MM-DD..YYYY-MM-DD` - date range
  - `..now` / `now..` - relative to current time
  - `YYYY-MM-DDTHH:MM..` - precise time point
  - `?` - undated items
- Keywords: `now`, `today`

#### Output Formatting (Issue #44)
- New `--output` parameter for list and action commands
- Supported formats: `table` (default), `json`, `simple`
- New `--contains` parameter for text substring filtering
- New modules: `range_parser.py`, `output_formatter.py`

### Changed

#### Todo Commands API (Issue #45)
- `todo add`: parameter order changed to `TEXT --date DATE --time TIME`
  - Old: `todo add DATE TEXT --time TIME`
  - New: `todo add TEXT --date DATE --time TIME`
- `todo list`: `--range` parameter now required
  - Old: `todo list [--date DATE]`
  - New: `todo list --range RANGE`
- `todo edit`: use `--id` for item identification
  - Old: `todo edit DATE TEXT_PREFIX`
  - New: `todo edit --id ID`
  - Added: `--clear-time` option to clear time field
- `todo complete/abandon/delete`: use `--id` for item identification
  - Old: `todo complete DATE TEXT_PREFIX`
  - New: `todo complete --id ID`
- All todo commands support `--output` parameter

#### Event Commands API (Issue #46)
- `event add`: parameter order changed to `TEXT --date DATE --time TIME`
  - Old: `event add DATE --time TIME TEXT`
  - New: `event add TEXT --date DATE --time TIME`
  - Note: `--date` and `--time` are both required
- `event list`: `--range` parameter now required
  - Old: `event list DATE`
  - New: `event list --range RANGE`
- `event edit/delete`: use `--id` for item identification
  - Old: `event edit DATE TIME TEXT_PREFIX`
  - New: `event edit --id ID`
- All event commands support `--output` parameter

### Removed

#### Deprecated Features (Issue #48)
- `todo move` command (merged into `todo edit --new-date`)
- `--overdue` parameter (replaced by `--range ..now --status pending`)
- `--undated` parameter (replaced by `--range ?`)
- `--json` parameter (replaced by `--output json`)
- `--simple` parameter (replaced by `--output simple`)
- `text_prefix` positional parameter (replaced by `--contains`)
- Legacy positional arguments for identification (date, time, text_prefix)

### Fixed

- ID uniqueness guarantee with collision detection
- UTF-8 encoding for Chinese text in storage
- List command parameter consistency

### Dependencies

- Added `ruff` as development dependency for code formatting and linting

### Tests

- Added `test_id.py` - 11 tests for ID generation and lookup
- Added `test_range.py` - 10 tests for range filtering
- Added `test_output.py` - 11 tests for output formatting
- Updated existing tests to use new API
- Total tests: 145 (all passing)

### Documentation

- Added ADR-0004: ID design decisions
- Added ADR-0005: Project version 0.1.1 feature summary
- Updated CONTEXT.md with ID system information

---

## [0.1.0] - 2026-05-XX

### Initial Release
- Basic todo/event/note management
- JSONL storage format
- Markdown export functionality
- Schema version 1