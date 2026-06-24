# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-06-24

### Breaking Changes

#### Time Parameter API Change (ADR-0010, ADR-0012)
- Replaced `--range` parameter with `--at` for unified time expression system
- Old: `todo list --range today`, `event list --range 2026-06-01..2026-06-30`
- New: `todo list --at today`, `event list --at 2026-06-01..2026-06-30`
- See CONTEXT.md for Timepoint/Timerange syntax details

#### JSON Output Format Change (ADR-0008)
- Changed from JSON array to JSONlines format
- Old: Single JSON array wrapping all items
- New: One JSON object per line, no array wrapper
- Optimized for AI Agent consumption and streaming
- Affects `todo list --json` and `event list --json`

#### Removed Commands
- Removed `export` and `export-all` commands
- Export functionality may be reintroduced in future versions

### Storage

#### [Breaking] Storage Location Migration (ADR-0011)
- Migrated storage location to hidden directory
- Old: `data.jsonl` in project root
- New: `.timeline/data.jsonl` in hidden directory
- Users must manually move existing data files to new location

#### One Item Per Line Format (ADR-0006)
- Changed from one Daily Record per line to one item per line
- Improves git diff readability
- Each line is a standalone JSON object

#### Null Date for Undated Todos (ADR-0013)
- Changed undated todo representation from `date: "0000-00-00"` to `date: null`
- More semantically correct representation

### Added

#### diary Command (#56)
- New `timeline-cli diary [date]` command for complete daily view
- Shows events, todos, and notes for one date in markdown format
- Accepts relative keywords: `today`, `yesterday`, `tomorrow`
- Supports `--show-id` flag to display item IDs

#### Version Flag
- New `--version` flag to show timeline-cli version
- Usage: `timeline-cli --version`

#### --no-time Parameter (#82)
- New `--no-time` parameter for filtering todos without time component
- Only valid for todo commands
- Can combine with `--at` (must be Timerange, not Timepoint)

#### Time Keywords
- `now` keyword: Current timestamp for precise time filtering
- `undated` keyword: Create undated todos with `todo add --at undated`

#### CLI Error Handling Standard (#65)
- Unified error handling with custom exception classes
- Consistent error messages across all commands
- See ADR-0009 for design details

### Changed

#### Simplified Output Formats (ADR-0007)
- Removed `--output` parameter
- Only two formats: markdown (default) and JSON (`--json`)
- Removed `simple` and `table` formats

#### Unified Action Command Output (#55)
- Action commands (add/edit/complete/abandon/delete) output unified to git-style
- Format: `[ID] Action: Text` (e.g., `[twk08a] Added: Buy groceries`)

#### --set-detail Newline Separator (#54)
- Changed `--set-detail` to accept newline-separated multi-line content
- Old: Multiple calls required for multi-line details
- New: Single call with `\n` separator

#### Relative Date Keywords Normalization
- Extended `--at` to support relative keywords in add commands
- Keywords: `today`, `yesterday`, `tomorrow`
- Add commands now accept these keywords for date specification

#### list Command Simplification (#57)
- `timeline-cli list` (show all dates with counts) now only supports markdown output
- Removed `--json` from list command (not from `todo list` or `event list`)

### Fixed

- Fixed JSON output Chinese character display (`ensure_ascii=False`)
- Fixed Timerange terminology and filtering bugs (#87, #88, #89)
- Fixed undated todo boundary and sorting issues (#90, #91)
- Fixed markdown output formatting consistency (#62)

### Developer

#### Tooling
- Added pyright config for LSP type checking
- Updated ruff config (existing from v0.1.1)

#### Skills
- Added `report-timeline-cli-issues` skill for bug reporting
- Updated `timeline` skill to reflect current CLI implementation

---

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