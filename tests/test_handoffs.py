"""Test suite verifying handoff documentation for all BOARD.md task entries (T4)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_every_board_task_has_handoff_with_required_headings() -> None:
    """Verify every Task ID in BOARD.md has a handoff with required headings."""
    board_path = ROOT / ".agent" / "state" / "BOARD.md"
    assert board_path.exists()
    board_text = board_path.read_text(encoding="utf-8")

    # Extract task IDs from BOARD.md markdown table
    task_ids: list[str] = []
    for line in board_text.splitlines():
        if not line.startswith("|") or "Task ID" in line or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[2]:
            task_ids.append(parts[2])

    assert len(task_ids) > 0, "No task IDs found in BOARD.md"

    handoffs_dir = ROOT / ".agent" / "state" / "handoffs"
    assert handoffs_dir.exists()

    required_headings = [
        "Files Changed",
        "Tests",
        "Open Risks",
    ]

    for task_id in task_ids:
        handoff_file = handoffs_dir / f"{task_id}.md"
        assert handoff_file.exists(), (
            f"Missing handoff file for task {task_id}: {handoff_file}"
        )

        content = handoff_file.read_text(encoding="utf-8")

        for heading in required_headings:
            pattern = re.compile(rf"#+\s*{re.escape(heading)}", re.IGNORECASE)
            assert pattern.search(content), (
                f"Handoff {handoff_file.name} missing required heading '{heading}'"
            )

        evidence_pattern = re.compile(
            r"#+\s*Evidence(?:\s*Log)?(?:\s*Path)?", re.IGNORECASE
        )
        assert evidence_pattern.search(content), (
            f"Handoff {handoff_file.name} missing Evidence heading"
        )


def test_board_has_no_done_rows() -> None:
    """Verify BOARD.md has no 'done' state rows per T4 specification."""
    board_path = ROOT / ".agent" / "state" / "BOARD.md"
    content = board_path.read_text(encoding="utf-8")

    for line in content.splitlines():
        if (
            line.startswith("|")
            and not line.startswith("| Node")
            and not line.startswith("|---")
        ):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                state = parts[5]
                assert state != "done", f"BOARD.md row has 'done' state: {line}"
