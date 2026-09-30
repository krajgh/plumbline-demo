"""The tasklist command line: parse arguments, call core and store, print results."""

import argparse
import datetime
import os
import sys
from pathlib import Path

from tasklist import core, store

EXIT_ERROR = 2  # the status argparse also uses for a bad command line
TODAY_ENV_VAR = "TASKLIST_TODAY"


def format_task(task: core.Task) -> str:
    """Return the one-line form of a task, such as "[x] 2 Call Sam (due 2026-10-01)"."""
    mark = "x" if task["done"] else " "
    line = f"[{mark}] {task['id']} {task['title']}"
    if task.get("due"):
        line += f" (due {task['due']})"
    return line


def today() -> datetime.date:
    """Return today's date: $TASKLIST_TODAY if set and non-empty, else the clock.

    Raises ValueError if $TASKLIST_TODAY is not a YYYY-MM-DD date.
    """
    value = os.environ.get(TODAY_ENV_VAR)
    if value:
        return core.parse_date(value)
    return datetime.date.today()


def fail(message: str) -> int:
    """Print message as a one-line error on stderr and return the error status."""
    print(f"error: {message}", file=sys.stderr)
    return EXIT_ERROR


def cmd_add(args: argparse.Namespace, path: Path) -> int:
    """Add a task and print its id."""
    tasks = store.load(path)
    try:
        task = core.add_task(tasks, args.title, args.due)
    except ValueError as error:
        if args.title.strip():  # the title is fine, so the due date was bad
            return fail(f"invalid due date: {args.due}")
        return fail(str(error))
    store.save(path, tasks)
    print(f"added {task['id']}")
    return 0


def cmd_done(args: argparse.Namespace, path: Path) -> int:
    """Mark a task as done and print its id."""
    tasks = store.load(path)
    try:
        core.complete_task(tasks, args.id)
    except KeyError:
        return fail(f"no task with id {args.id}")
    store.save(path, tasks)
    print(f"done {args.id}")
    return 0


def cmd_list(args: argparse.Namespace, path: Path) -> int:
    """Print the open tasks, every task with --all, or the overdue ones, one per line."""
    tasks = store.load(path)
    if args.overdue:
        try:
            shown = core.overdue_tasks(tasks, today())
        except ValueError:
            return fail(f"invalid {TODAY_ENV_VAR}: {os.environ[TODAY_ENV_VAR]}")
    else:
        shown = core.visible_tasks(tasks, show_all=args.show_all)
    for task in shown:
        print(format_task(task))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser, with its add, done and list subcommands."""
    parser = argparse.ArgumentParser(prog="tasklist", description="A tiny to-do list.")
    parser.add_argument(
        "--file",
        metavar="PATH",
        help=f"task file (default: ${store.ENV_VAR}, else ./{store.DEFAULT_FILE})",
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    add = commands.add_parser("add", help="add a task")
    add.add_argument("title", metavar="TITLE", help="what needs doing")
    add.add_argument("--due", metavar="DATE", help="due date, YYYY-MM-DD")
    add.set_defaults(handler=cmd_add)

    done = commands.add_parser("done", help="mark a task as done")
    done.add_argument("id", metavar="ID", type=int, help="id of the task")
    done.set_defaults(handler=cmd_done)

    show = commands.add_parser("list", help="list open tasks")
    show.add_argument(
        "--all", dest="show_all", action="store_true", help="include finished tasks"
    )
    show.add_argument(
        "--overdue",
        action="store_true",
        help=f"only open tasks due before today (${TODAY_ENV_VAR}, else the clock)",
    )
    show.set_defaults(handler=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line and return the exit status.

    argv defaults to sys.argv[1:].
    """
    args = build_parser().parse_args(argv)
    path = store.resolve_path(args.file)
    return args.handler(args, path)
