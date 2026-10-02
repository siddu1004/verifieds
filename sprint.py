"""Sprint helper: task claims, message bus, merge lock, clock. Standard library only.

  python sprint.py init [--tasks FILE]   create the bus, record start, load tasks
  python sprint.py next --me W1          claim the next ready task
                                         (prints TASK <id>, WAIT or ALL_DONE)
  python sprint.py finish --task T1      mark a task done (unblocks dependants)
  python sprint.py release --task T1     give back a claimed, unfinished task
  python sprint.py status                show each task: todo, running or done
  python sprint.py clock                 print minutes since the start
  python sprint.py say --sender A --to B --kind READY --text "..."
  python sprint.py inbox --me B          print unread messages for B and ALL
  python sprint.py lock | unlock         serialise merges into integration

The bus lives outside every git worktree. Override with VERIFIEDS_BUS.
"""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

DEFAULT = r"C:\dev\bus" if sys.platform == "win32" else str(Path.home() / "vbus")
BUS = Path(os.environ.get("VERIFIEDS_BUS", DEFAULT))
KINDS = (
    "READY",
    "NEED",
    "CHANGE",
    "REVIEW_REQUEST",
    "REVIEW_RESULT",
    "BLOCKED",
    "DONE",
    "HALT",
)


def init(tasks_file):
    BUS.mkdir(parents=True, exist_ok=True)
    (BUS / "claims").mkdir(exist_ok=True)
    (BUS / "done").mkdir(exist_ok=True)
    start = BUS / "start.txt"
    if not start.exists():
        start.write_text(str(int(time.time())), encoding="utf-8")
    if tasks_file:
        shutil.copy(tasks_file, BUS / "tasks.json")
    print(f"bus={BUS}")
    return 0


def load_tasks():
    return json.loads((BUS / "tasks.json").read_text(encoding="utf-8"))


def next_task(me):
    done = {p.name for p in (BUS / "done").iterdir()}
    pending = [t for t in load_tasks() if t["id"] not in done]
    if not pending:
        print("ALL_DONE")
        return 0
    for task in pending:
        if not all(dep in done for dep in task["deps"]):
            continue
        try:
            (BUS / "claims" / task["id"]).mkdir()
        except FileExistsError:
            continue
        (BUS / "claims" / task["id"] / "owner.txt").write_text(me, encoding="utf-8")
        print(f"TASK {task['id']}")
        return 0
    print("WAIT")
    return 0


def finish(task):
    (BUS / "done" / task).mkdir(exist_ok=True)
    print(f"done {task}")
    return 0


def release(task):
    shutil.rmtree(BUS / "claims" / task, ignore_errors=True)
    print(f"released {task}")
    return 0


def status():
    done = {p.name for p in (BUS / "done").iterdir()}
    for task in load_tasks():
        owner_file = BUS / "claims" / task["id"] / "owner.txt"
        if task["id"] in done:
            state = "done"
        elif owner_file.exists():
            state = "running (" + owner_file.read_text(encoding="utf-8") + ")"
        else:
            state = "todo"
        print(f"{task['id']:6s} {state}")
    return 0


def clock():
    start = int((BUS / "start.txt").read_text(encoding="utf-8"))
    print(int((time.time() - start) / 60))
    return 0


def say(sender, to, kind, text):
    name = f"{time.time_ns()}-{sender}-to-{to}-{kind}.md"
    (BUS / name).write_text(text.strip() + "\n", encoding="utf-8")
    print(f"sent {name}")
    return 0


def inbox(me):
    marker = BUS / f".read-{me}"
    seen = marker.read_text(encoding="utf-8") if marker.exists() else ""
    last = seen
    shown = 0
    for path in sorted(BUS.glob("*.md")):
        stamp, rest = path.name.split("-", 1)
        _sender, _, remainder = rest.partition("-to-")
        target = remainder.split("-", 1)[0]
        if path.name <= seen or target not in (me, "ALL"):
            continue
        print(f"--- {path.name}")
        print(path.read_text(encoding="utf-8").rstrip())
        last = max(last, path.name)
        shown += int(bool(stamp))
    marker.write_text(last, encoding="utf-8")
    if shown == 0:
        print("(no new messages)")
    return 0


def lock():
    try:
        (BUS / "merge.lock").mkdir()
    except FileExistsError:
        print("LOCKED: another lane is merging; wait 20 seconds and retry")
        return 1
    print("lock acquired")
    return 0


def unlock():
    try:
        (BUS / "merge.lock").rmdir()
    except FileNotFoundError:
        print("lock was not held")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = [
        "init",
        "clock",
        "say",
        "inbox",
        "lock",
        "unlock",
        "next",
        "finish",
        "release",
        "status",
    ]
    parser.add_argument("command", choices=commands)
    parser.add_argument("--sender")
    parser.add_argument("--to")
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--text", default="")
    parser.add_argument("--me")
    parser.add_argument("--tasks")
    parser.add_argument("--task")
    args = parser.parse_args()
    if args.command == "say":
        if not (args.sender and args.to and args.kind):
            parser.error("say needs --sender, --to and --kind")
        return say(args.sender, args.to, args.kind, args.text)
    if args.command == "inbox":
        if not args.me:
            parser.error("inbox needs --me")
        return inbox(args.me)
    if args.command == "next":
        if not args.me:
            parser.error("next needs --me")
        return next_task(args.me)
    if args.command in ("finish", "release"):
        if not args.task:
            parser.error(f"{args.command} needs --task")
        return (finish if args.command == "finish" else release)(args.task)
    if args.command == "init":
        return init(args.tasks)
    table = {"clock": clock, "lock": lock, "unlock": unlock, "status": status}
    return table[args.command]()


if __name__ == "__main__":
    sys.exit(main())
