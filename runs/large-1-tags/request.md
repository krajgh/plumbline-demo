Part 1 of 3 of the split proposed by run 183da93-20261005T111104Z (its split_proposal, change 1): tags. Branch `organize-tags` from main.

Add tags to tasklist:
1. `add` takes `--tag NAME`, which may be repeated; tags are stored with the task. A tag is lowercase letters, digits and dashes; anything else is refused with exit code 2, one line on stderr naming the value, and nothing stored.
2. `tag ID NAME` adds a tag to an existing task and `untag ID NAME` removes one; an unknown id exits 2 with one line on stderr.
3. `list --tag NAME` shows only tasks carrying that tag, and combines with `--all` and `--overdue`. `list` prints a task's tags after its title and due date, as `#work #home`.
8 (tag part). Task files written by earlier versions (no tags) still load, list and complete as before, and a task without tags prints exactly as today.

Choices the parent run's planner made where the request was silent, kept here: tags are stored as a JSON list under "tags", in the order given, duplicates dropped, and no "tags" key when there are none. Errors are one stderr line, `error: invalid tag: VALUE` and `error: no task with id ID`. `tag` and `untag` print `tagged ID` and `untagged ID`. Tagging a tag that is already present exits 0. Untagging a tag the task does not carry exits 2 with one stderr line. `untag` deletes the "tags" key when it becomes empty.

Carried from the parent run's spec review: finding spec-review/requirements-2 (MINOR). The empty-tag case (`--tag ''`) must have a test that actually discriminates: a check that stderr "contains the value" passes for any message when the value is empty. Assert the exact line `error: invalid tag: ` (or an equivalent exact check) instead. Finding spec-review/requirements-1 (priority ordering under `list --all`) belongs to part 2 and is not in scope here.
