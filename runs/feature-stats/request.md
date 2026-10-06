Work on a new branch `stats` from main. Add a `stats` command to tasklist:
1. `stats` prints, one per line and in this order: `open: N`, `done: N`, `high: N`, `normal: N`, `low: N` (open tasks by priority), and `overdue: N` (open tasks whose due date is before today, as `list --overdue` decides it, with TASKLIST_TODAY honoured).
2. Then one line per tag carried by an open task, as `#tag: N`, ordered by count (highest first), then by tag name.
3. `stats --tag NAME` limits every figure to tasks carrying that tag, and prints no per-tag lines.
4. An empty or missing task file prints the six count lines with 0 and exits 0.
5. A malformed stored value (due date, tags or priority) is reported the way `list` reports it: exit 2, one line on stderr naming the task by id, nothing on stdout.
6. Task files written by earlier versions (no tags, no priority, no due date) count as normal priority with no tags.
Expect size M.
