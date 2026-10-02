"""Sprint helper: message bus, merge lock and clock. Standard library only.

  python sprint.py init                      create the bus and record the start time
  python sprint.py clock                     print minutes since the start
  python sprint.py say --sender A --to B --kind READY --text "..."
  python sprint.py inbox --me B              print unread messages for B and ALL
  python sprint.py lock | unlock             serialise merges into integration

The bus lives outside every git worktree. Override with VERIFIEDS_BUS.
"""

import argparse
import os
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


def init():
    BUS.mkdir(parents=True, exist_ok=True)
    start = BUS / "start.txt"
    if not start.exists():
        start.write_text(str(int(time.time())), encoding="utf-8")
    print(f"bus={BUS}")
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
    parser.add_argument(
        "command", choices=["init", "clock", "say", "inbox", "lock", "unlock"]
    )
    parser.add_argument("--sender")
    parser.add_argument("--to")
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--text", default="")
    parser.add_argument("--me")
    args = parser.parse_args()
    if args.command == "say":
        if not (args.sender and args.to and args.kind):
            parser.error("say needs --sender, --to and --kind")
        return say(args.sender, args.to, args.kind, args.text)
    if args.command == "inbox":
        if not args.me:
            parser.error("inbox needs --me")
        return inbox(args.me)
    return {"init": init, "clock": clock, "lock": lock, "unlock": unlock}[
        args.command
    ]()


if __name__ == "__main__":
    sys.exit(main())
