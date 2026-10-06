Part 2 of 3 of the split proposed by run 183da93-20261005T111104Z (its split_proposal, change 2): priorities. Branch `organize-priorities` from main, which now has part 1 (tags, commit a061f09).

Add priorities to tasklist:
4. `add` takes `--priority high|normal|low`, default `normal`; any other value is refused like a bad tag: exit code 2, one line on stderr naming the value (`error: invalid priority: VALUE`), and nothing stored.
5. `list` orders open tasks by priority (high, then normal, then low), then by id, and marks a high-priority task with `! ` (exclamation mark and one space) before its title, e.g. `[ ] 3 ! Pay rent`; `list --overdue` keeps its oldest-due-first order (and still shows the marker). Ordering and marker apply with `list --tag` as well.
8 (priority part). Task files written by earlier versions (no priority) still load, list and complete as before; a task without a "priority" key is treated as normal, and a task without tags or a priority prints exactly as today. `done` adds no "priority" key.

Carried from the parent run's spec review: finding spec-review/requirements-1 (MINOR). The parent spec applied priority ordering to `list --all` as well, done tasks included, while the request orders only open tasks. Do not widen the request silently: the spec must state explicitly how `list --all` orders done tasks, keep open tasks ordered by priority then id, and say why in its risks.

Follow the error conventions part 1 established: one `error: ...` line on stderr, exit 2, and a malformed stored value (a "priority" that is not one of high/normal/low) handled the way malformed stored due dates and tags are, exit 2 with one line naming the task by id.
