#!/usr/bin/env python3
"""
validate-queue.py — enforce OMS task schema on cleared-queue.md

Usage:
  validate-queue.py <path>          # validate only — exit 1 on violations
  validate-queue.py <path> --fix    # auto-correct Model-hint in-place, then validate

Exit 0 = clean. Exit 1 = violations found (printed to stderr).
Violations other than Model-hint always require human fix — --fix only corrects Model-hint.
"""
import sys
from pathlib import Path

from queue_validator import validate_task, _validate_duplicates, _validate_features
from queue_validator.parser import parse_tasks
from queue_validator.model_hint import fix_model_hints


def main() -> None:
    args = sys.argv[1:]
    fix_mode = "--fix" in args
    paths = [a for a in args if not a.startswith("--")]

    if not paths:
        print("Usage: validate-queue.py <cleared-queue.md> [--fix]", file=sys.stderr)
        sys.exit(1)

    path = Path(paths[0])
    if not path.exists():
        sys.exit(0)

    if fix_mode:
        fix_model_hints(path)

    text = path.read_text(errors="replace")
    tasks = parse_tasks(text)
    queued = [t for t in tasks if t["fields"].get("Status", "").lower() == "queued"]

    if not queued:
        sys.exit(0)

    # Detect project root from queue file location
    project_root = None
    for parent in path.parents:
        if (parent / '.claude').is_dir():
            project_root = parent
            break

    all_errors: list[str] = []
    for task in queued:
        all_errors.extend(validate_task(task, all_tasks=tasks, project_root=project_root))

    # Cross-task duplicate detection
    all_errors.extend(_validate_duplicates(queued))

    # Feature-level validation
    all_errors.extend(_validate_features(text))

    if all_errors:
        print(f"\n[queue-validator] {path} — {len(all_errors)} violation(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
