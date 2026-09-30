# tasklist

A tiny to-do list for the command line. Python 3.11+, standard library only.

## Usage

```
$ python -m tasklist add "Buy milk"
added 1
$ python -m tasklist add "Call Sam"
added 2
$ python -m tasklist done 2
done 2
$ python -m tasklist list
[ ] 1 Buy milk
$ python -m tasklist list --all
[ ] 1 Buy milk
[x] 2 Call Sam
```

A task can have a due date: `add "Pay rent" --due 2026-10-01` (YYYY-MM-DD only).
`list` shows it as `(due 2026-10-01)`. `list --overdue` shows open tasks due before
today, earliest first; "today" is `TASKLIST_TODAY` (YYYY-MM-DD) if set, else the clock.

Tasks are kept in a JSON file. Its path is `--file PATH` if given (put it before
the command), else the `TASKLIST_FILE` environment variable, else `./tasks.json`.

An unknown id or an empty title prints one line to stderr and exits with status 2.

## Tests

```
uv run --no-project --with pytest pytest -q
```
