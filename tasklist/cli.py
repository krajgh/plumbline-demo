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
    marker = "! " if task.get("priority") == "high" else ""
    line = f"[{mark}] {task['id']} {marker}{task['title']}"
    if task.get("due"):
        line += f" (due {task['due']})"
    if task.get("tags"):
        line += " " + " ".join(f"#{name}" for name in task["tags"])
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
    if args.priority not in core.PRIORITIES:
        return fail(f"invalid priority: {args.priority}")
    for name in args.tags or []:
        if not core.is_valid_tag(name):
            return fail(f"invalid tag: {name}")
    tasks = store.load(path)
    try:
        task = core.add_task(tasks, args.title, args.due, args.tags, args.priority)
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


def bad_tags(tasks: list[core.Task]) -> str | None:
    """Return an error message for the first task whose stored tags are not a list of strings."""
    for task in tasks:
        tags = task.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            return f"task {task['id']} has invalid tags: {tags!r}"
    return None


def bad_priority(tasks: list[core.Task]) -> str | None:
    """Return an error message for the first task whose present priority is not a known one."""
    for task in tasks:
        if "priority" in task and task["priority"] not in core.PRIORITIES:
            return f"task {task['id']} has an invalid priority: {task['priority']!r}"
    return None


def cmd_tag(args: argparse.Namespace, path: Path) -> int:
    """Add a tag to a task."""
    tasks = store.load(path)
    message = core.is_valid_tag(args.name) and bad_tags([t for t in tasks if t["id"] == args.id])
    if message:
        return fail(message)
    try:
        core.add_tag(tasks, args.id, args.name)
    except ValueError:
        return fail(f"invalid tag: {args.name}")
    except KeyError:
        return fail(f"no task with id {args.id}")
    store.save(path, tasks)
    print(f"tagged {args.id}")
    return 0


def cmd_untag(args: argparse.Namespace, path: Path) -> int:
    """Remove a tag from a task."""
    tasks = store.load(path)
    message = bad_tags([t for t in tasks if t["id"] == args.id])
    if message:
        return fail(message)
    try:
        core.remove_tag(tasks, args.id, args.name)
    except ValueError as error:
        return fail(str(error))
    except KeyError:
        return fail(f"no task with id {args.id}")
    store.save(path, tasks)
    print(f"untagged {args.id}")
    return 0


def cmd_list(args: argparse.Namespace, path: Path) -> int:
    """Print the open tasks, every task with --all, or the overdue ones, one per line."""
    tasks = store.load(path)
    if args.overdue:
        try:
            now = today()
        except ValueError:
            return fail(f"invalid {TODAY_ENV_VAR}: {os.environ[TODAY_ENV_VAR]}")
        for task in tasks:  # a bad stored due date is reported by the task's id
            if not task["done"] and "due" in task:
                try:
                    core.parse_date(task["due"])
                except ValueError:
                    return fail(f"task {task['id']} has an invalid due date: {task['due']}")
        message = bad_tags([t for t in tasks if not t["done"]])  # every open task, like due dates
        if message:
            return fail(message)
        message = bad_priority([t for t in tasks if not t["done"]])
        if message:
            return fail(message)
        shown = core.overdue_tasks(tasks, now)
    else:
        # check before sorting (an unsortable value must not raise) and before the --tag filter
        message = bad_priority(tasks if args.show_all else [t for t in tasks if not t["done"]])
        if message:
            return fail(message)
        shown = core.visible_tasks(tasks, show_all=args.show_all)
    message = bad_tags(shown)
    if message:
        return fail(message)
    if args.tag is not None:
        shown = core.tagged_tasks(shown, args.tag)
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
    add.add_argument(
        "--tag", dest="tags", metavar="NAME", action="append", help="tag (repeatable)"
    )
    add.add_argument(
        "--priority", metavar="LEVEL", default="normal", help="high, normal (default) or low"
    )
    add.set_defaults(handler=cmd_add)

    for name, handler, text in (
        ("tag", cmd_tag, "add a tag to a task"),
        ("untag", cmd_untag, "remove a tag from a task"),
    ):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("id", metavar="ID", type=int, help="id of the task")
        sub.add_argument("name", metavar="NAME", help="tag name")
        sub.set_defaults(handler=handler)

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
    show.add_argument("--tag", metavar="NAME", help="only tasks with this tag")
    show.set_defaults(handler=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command line and return the exit status.

    argv defaults to sys.argv[1:].
    """
    argv = sys.argv[1:] if argv is None else list(argv)
    args = build_parser().parse_args(argv)
    path = store.resolve_path(args.file)
    return args.handler(args, path)
