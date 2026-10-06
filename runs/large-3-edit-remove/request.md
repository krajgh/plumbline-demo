Part 3 of 3 of the split proposed by run 183da93-20261005T111104Z (its split_proposal, change 3): edit and remove. Branch `organize-edit` from main, which now has part 1 (tags, a061f09) and part 2 (priorities, 0f44eee).

Add edit and remove to tasklist:
6. `edit ID` changes only the fields it is given: `--title`, `--due DATE` or `--no-due`, `--priority`. An unknown id or an invalid value exits 2 and changes nothing.
7. `remove ID` deletes a task and prints `removed ID`; an unknown id exits 2.
8 (edit part). Task files written by earlier versions (no tags, no priority) still load, list, complete and edit as before; `edit` adds only the keys it was asked to change.

Choices the parent run's planner made where the request was silent, kept here: `edit` prints `edited ID`. `edit` with no field option exits 2. `--due` together with `--no-due` exits 2. `--no-due` removes the "due" key. The title is stripped like in `add`, and a blank title is refused. Every value is validated before anything changes, so a bad value next to a good one changes nothing. `edit` never alters tags, done state or id. Ids are not renumbered after `remove`.

Follow the conventions parts 1 and 2 established: errors are one `error: ...` line on stderr with exit 2, reusing the existing wording (`error: no task with id ID`, `error: invalid due date: VALUE`, `error: invalid priority: VALUE`); priorities are validated with core.PRIORITIES; a normal priority is stored as no "priority" key, so `edit --priority normal` removes the key and `--priority high`/`low` sets it.
