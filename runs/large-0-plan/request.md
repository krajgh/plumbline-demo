Work on a new branch `organize` from main. Add tags, priorities, and edit and remove to tasklist:
1. `add` takes `--tag NAME`, which may be repeated; tags are stored with the task. A tag is lowercase letters, digits and dashes; anything else is refused with exit code 2, one line on stderr naming the value, and nothing stored.
2. `tag ID NAME` adds a tag to an existing task and `untag ID NAME` removes one; an unknown id exits 2 with one line on stderr.
3. `list --tag NAME` shows only tasks carrying that tag, and combines with `--all` and `--overdue`. `list` prints a task's tags after its title and due date, as `#work #home`.
4. `add` takes `--priority high|normal|low`, default `normal`; any other value is refused like a bad tag.
5. `list` orders open tasks by priority (high, then normal, then low), then by id, and marks a high-priority task with `!` before its title; `list --overdue` keeps its oldest-due-first order.
6. `edit ID` changes only the fields it is given: `--title`, `--due DATE` or `--no-due`, `--priority`. An unknown id or an invalid value exits 2 and changes nothing.
7. `remove ID` deletes a task and prints `removed ID`; an unknown id exits 2.
8. Task files written by earlier versions (no tags, no priority) still load, list, complete and edit as before, and a task without tags or a priority prints exactly as today.
Expect size L: code and tests well over 400 lines. Propose a split.
