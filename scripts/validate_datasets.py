"""Validate the shared JSONL evaluation contract without external dependencies."""

import argparse
import json
from pathlib import Path

REQUIRED_FIELDS = {
    "id": str,
    "scenario": str,
    "input": str,
    "actual_output": str,
    "expected_output": str,
    "retrieval_context": list,
}


def validate(dataset_dir: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    count = 0
    for path in sorted(dataset_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                count += 1
                location = f"{path}:{line_number}"
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{location}: invalid JSON: {exc.msg}")
                    continue
                for field, expected_type in REQUIRED_FIELDS.items():
                    if field not in row:
                        errors.append(f"{location}: missing field {field}")
                    elif not isinstance(row[field], expected_type):
                        errors.append(f"{location}: {field} must be {expected_type.__name__}")
                    elif isinstance(row[field], (str, list)) and not row[field]:
                        errors.append(f"{location}: {field} must not be empty")
                case_id = row.get("id")
                if isinstance(case_id, str):
                    if case_id in seen_ids:
                        errors.append(f"{location}: duplicate id {case_id}")
                    seen_ids.add(case_id)
                if row.get("scenario") != path.stem:
                    errors.append(f"{location}: scenario must match filename {path.stem}")
                contexts = row.get("retrieval_context")
                if isinstance(contexts, list) and any(not isinstance(item, str) for item in contexts):
                    errors.append(f"{location}: retrieval_context items must be strings")
    if count == 0:
        errors.append(f"{dataset_dir}: no cases found")
    return count, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=Path("evals/datasets"))
    args = parser.parse_args()
    count, errors = validate(args.dataset_dir)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {count} cases in {args.dataset_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
