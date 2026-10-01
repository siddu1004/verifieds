"""Export Pydantic JSON schemas and check schema freshness."""

import json
import sys
from pathlib import Path
from typing import Any

from verifieds.schemas.models import CandidateDraft, Finding, Candidate, VerifyReport

MODELS = {
    "candidate_draft.json": CandidateDraft,
    "finding.json": Finding,
    "candidate.json": Candidate,
    "verify_report.json": VerifyReport,
}


def generate_schema_json(model_cls: Any) -> str:
    """Generate pretty-printed JSON schema string for a Pydantic model."""
    schema_dict = model_cls.model_json_schema()
    return json.dumps(schema_dict, indent=2) + "\n"


def export_schemas(target_dir: Path) -> None:
    """Export JSON schemas to target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename, model_cls in MODELS.items():
        content = generate_schema_json(model_cls)
        (target_dir / filename).write_text(content, encoding="utf-8")


def check_schemas(target_dir: Path) -> bool:
    """Check if exported schema files in target_dir are up to date."""
    for filename, model_cls in MODELS.items():
        filepath = target_dir / filename
        if not filepath.exists():
            return False
        expected = generate_schema_json(model_cls)
        actual = filepath.read_text(encoding="utf-8")
        if actual != expected:
            return False
    return True


def main() -> None:
    """CLI entry point for python -m verifieds.schemas.export [--check]."""
    project_root = Path(__file__).resolve().parent.parent.parent
    schemas_dir = project_root / "schemas"

    if "--check" in sys.argv:
        if not check_schemas(schemas_dir):
            sys.stderr.write(
                f"Error: Schema files in {schemas_dir} are stale or missing.\n"
                "Run 'python -m verifieds.schemas.export' to regenerate them.\n"
            )
            sys.exit(1)
        sys.stdout.write("All schemas are up to date.\n")
    else:
        export_schemas(schemas_dir)
        sys.stdout.write(f"Schemas exported successfully to {schemas_dir}\n")


if __name__ == "__main__":
    main()
