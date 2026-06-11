---
name: timeline
description: Use when user wants to create reminders or todos, record completed actions or events, check pending tasks, or modify/move existing todos.
---

# Timeline Skill

A skill for managing todos and events stored in markdown files, organized by date.

## Data Storage

### File Location
- Directory: `timeline/` at project root
- Filename format: `YYYY-MM-DD.md` (e.g., `2026-06-11.md`)
- Undated todos: `0000-00-00.md`

### File Structure
Each file follows this template:

```markdown
# YYYY-MM-DD

## Events

## Todos

## Notes
```

### Data Formats

#### Events
- Format: `- HH:MM Description.`
- Must have a time
- Represents something that happened at a specific moment
- Supports detail (indented with 4 spaces):

```markdown
- 14:30 Met with client.
    - Discussed project timeline.
```

#### Todos
- Format: `- [ ] HH:MM Description` (with time) or `- [ ] Description` (without time)
- States:
  - `[ ]` - Not completed
  - `[x]` - Completed
  - `[ ] ~~Description~~` - Abandoned (strikethrough)
- Supports detail:

```markdown
- [ ] 15:00 Clean desk
    - Throw away expired snacks.
```

#### Notes
- Free-form text for thoughts, goals, moods, etc.
- No specific format required

### Sorting Rules
- Within each section, items with time are sorted chronologically
- Items without time appear at the end

---

## Operations

### Creating Todos
**Trigger words**: "提醒", "待办", "要做", "创建待办"

**Examples**:
- "提醒我明天三点开会" -> Create todo for tomorrow at 15:00
- "创建待办，明天买洗发水" -> Create todo for tomorrow (no time)
- "下周三提醒我准备会议纪要" -> Create todo for next Wednesday

**Date parsing**:
- Relative: "今天", "明天", "后天"
- Specific: "下周一", "这周五", "6月15日"
- When uncertain, ask for clarification

**Time parsing**:
- Default: PM (e.g., "三点" -> 15:00)
- "凌晨" prefix for early hours
- When current time is late night/early morning (after midnight), "明天" might mean "today" - ask for confirmation

### Creating Events
**Trigger words**: "约了", "买了", completed action verbs

**Important**: Event time = when the action happened, NOT when the scheduled event will occur.

**Examples**:
- "约了客户明天下午三点开会" -> Event created for NOW, recording that you made the appointment
- "买了洗发水了" -> Event created for current time

**After creating an event for a future commitment**, ask user if they want to create a corresponding todo.

**Time rules**:
- Must have a time
- If not specified, defaults to current time
- Can specify past time

### Completing Todos
**Trigger words**: "做完了", "搞定了", completed action verbs

**Flow**:
1. Create an Event recording the completed action
2. Search for matching Todo across all files (including `0000-00-00.md`)
3. If exactly one match: mark as `[x]`
4. If multiple matches: ask user which one
5. If no match: only create the Event

**Example**:
```
User: 买了洗发水了
AI: 
- Creates Event: "15:30 买了洗发水。"
- Finds matching Todo: "买洗发水"
- Marks Todo as [x]
```

### Abandoning Todos
**Trigger words**: "不做了", "算了", "取消", "放弃"

**Action**: Add strikethrough to the todo description
- `- [ ] ~~Description~~`

### Moving Todos
**Trigger words**: "移到", "推到", "延期到", "改到"

**Examples**:
- "把这个移到明天" -> Move to tomorrow
- "推到晚上六点" -> Change time to 18:00 (same day or target day)
- "昨天的待办移到今天" -> Move yesterday's todos to today

### Editing
**Trigger words**: "改成", "修改", "换成"

**Supports**: Editing time or description for both Todos and Events

### Deleting
**Trigger words**: "删掉", "删除"

**Action**: Ask for confirmation before deleting

### Viewing
**Trigger words**: "今天有什么事", "看看今天的待办", "今天的事"

**Action**: Display Events, Todos, and Notes for the specified day (default: today)

### Review
**Trigger words**: "有什么事做", "过期的", "看看没做完的"

**Action**: Display all overdue uncompleted todos across all files

### Adding Details
**Trigger words**: "补充", "备注", "加个备注"

**Action**: Add indented detail to an existing item

**Can also add detail during creation**:
- "提醒我三点收拾桌面，记得扔掉过期零食"

---

## Response Format

After completing an operation, show the file and content:

```
已在 2026-06-12.md 创建待办：
- [ ] 15:00 开会
    - 记得带资料
```

---

## Time Parsing Rules

| User says | Interpretation |
|-----------|----------------|
| "三点" | 15:00 (default PM) |
| "凌晨三点" | 03:00 |
| "早上九点" | 09:00 |
| "今晚八点" | 20:00 today |
| "明天" | Tomorrow |
| "下周三" | Next Wednesday |

**Late night edge case**: If current time is after midnight and user says "明天", confirm whether they mean "today" (since they haven't slept yet) or actual tomorrow.

**Ambiguous cases**: Always ask for clarification (e.g., "下周开会" -> "请问是下周几？")

---

## Helper Scripts

### List Uncompleted Todos
```bash
python3 .claude/skills/timeline/scripts/todo_list.py
```

Returns all uncompleted todos across all files.

### Validate Date Consistency
```bash
python3 .claude/skills/timeline/scripts/validate.py
```

Checks if the H1 date matches the filename for all markdown files.

---

## Edge Cases

1. **No matching todo found when completing**: Only create the Event, inform user
2. **Multiple potential matches**: List them and ask user to confirm
3. **Time in the past for new todo**: Allow it (for recording missed items)
4. **File doesn't exist**: Create it with the standard template
5. **Empty sections**: Always pre-create the three H2 headers (Events, Todos, Notes)