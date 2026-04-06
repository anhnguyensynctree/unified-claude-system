#!/usr/bin/env python3
"""
validate-queue.py — enforce OMS task schema on cleared-queue.md

Usage:
  validate-queue.py <path>          # validate only — exit 1 on violations
  validate-queue.py <path> --fix    # auto-correct Model-hint in-place, then validate

Exit 0 = clean. Exit 1 = violations found (printed to stderr).
Violations other than Model-hint always require human fix — --fix only corrects Model-hint.
"""
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "Feature",
    "Milestone",
    "Department",
    "Type",
    "Infra-critical",
    "Spec",
    "Scenarios",
    "Artifacts",
    "Produces",
    "Verify",
    "Context",
    "Activated",
    "Validation",
    "Depends",
    "File-count",
    "Model-hint"
]

# Fields where "none" is a valid value
NULLABLE_FIELDS = {"Depends", "Produces", "Verify"}

MAX_FILES = 4

# Regex patterns for field lines (both formats used across projects)
RE_BOLD = re.compile(r'^[-\s]*\*\*([A-Za-z-]+):\*\*\s*(.*)')
RE_PLAIN = re.compile(r'^([A-Za-z-]+):\s*(.*)')


def parse_tasks(text: str) -> list[dict]:
    """Parse cleared-queue.md into task dicts with id + fields."""
    # Support any heading depth: ## TASK-, #### TASK-, etc.
    blocks = re.split(r'^(?=#{1,6}\s+TASK-)', text, flags=re.MULTILINE)
    tasks = []
    for block in blocks:
        m = re.match(r'^#{1,6}\s+(TASK-\S+)', block)
        if not m:
            continue
        task_id = m.group(1).rstrip('—').strip()
        fields: dict[str, str] = {}
        lines = block.splitlines()
        i = 0
        while i < len(lines):
            # Stop at separator or a new section heading (FEATURE block, etc.)
            if lines[i].startswith('---') or (lines[i].startswith('#') and i > 0):
                break
            line = lines[i]
            fm = RE_BOLD.match(line) or RE_PLAIN.match(line)
            if fm:
                key = fm.group(1).strip()
                val = fm.group(2).strip()
                if val == '|':
                    # YAML literal block scalar — i is advanced inside the loop
                    body: list[str] = []
                    i += 1
                    while i < len(lines) and (lines[i].startswith('  ') or not lines[i].strip()):
                        body.append(lines[i].strip())
                        i += 1
                    val = ' '.join(l for l in body if l)
                    if key:
                        fields[key] = val
                    continue  # i already points to next field — do NOT increment
                elif val == '':
                    # List-style: subsequent "- item" lines (any indentation)
                    body = []
                    j = i + 1
                    while j < len(lines) and re.match(r'^\s*-\s+', lines[j]):
                        body.append(lines[j].lstrip(' -').strip())
                        j += 1
                    if body:
                        val = ' | '.join(body)
                if key:
                    fields[key] = val
                    i += 1
                    continue
            i += 1
        tasks.append({"id": task_id, "fields": fields})
    return tasks


def derive_model_hint(fields: dict) -> str | None:
    """
    Derive the correct Model-hint from schema rules.
    Returns None if derivation is impossible (missing File-count or Type).

    Rules from task-schema.md § Model-hint derivation:
    - gate → sonnet (always, for reliability)
    - infra-critical: true + any → sonnet (highest reliability)
    - impl + ≤3 files → qwen-coder (primary code model)
    - research + ≤3 files → qwen (best reasoning, 1M context)
    """
    task_type = fields.get("Type", "").lower().strip()
    infra = fields.get("Infra-critical", "").lower().strip()
    fc_raw = fields.get("File-count", "")
    fc_match = re.search(r'\d+', fc_raw)
    if not fc_match:
        return None
    file_count = int(fc_match.group())

    # Quality gate (highest reliability)
    if task_type == "gate":
        return "sonnet"
    if infra == "true":
        return "sonnet"

    # Implementation tasks — accept any code-capable free model (round-robin at elaboration)
    if task_type in ("impl", "build", "test"):
        if file_count <= 3:
            return "qwen-coder"  # primary — but llama/gpt-oss also valid (round-robin)
        else:
            return None  # must be split

    # Research tasks — accept any reasoning free model (round-robin at elaboration)
    if task_type == "research":
        if file_count <= 3:
            return "qwen"  # primary — but nemotron/stepfun also valid (round-robin)
        return None

    return None


def fix_model_hints(path: Path) -> int:
    """
    Auto-correct Model-hint for all queued tasks in path.
    Rewrites the file in-place. Returns count of corrections made.
    Both bold (**Model-hint:** X) and plain (Model-hint: X) formats supported.
    """
    text = path.read_text(errors="replace")
    tasks = parse_tasks(text)
    corrections = 0

    for task in tasks:
        if task["fields"].get("Status", "").lower() != "queued":
            continue
        expected = derive_model_hint(task["fields"])
        if not expected:
            continue
        actual = task["fields"].get("Model-hint", "").strip().lower()
        if actual == expected:
            continue

        tid = task["id"]
        # Replace in text — handle both heading depths and both field formats
        escaped = re.escape(tid)
        bold_pat = re.compile(
            r'(#{1,6}\s+' + escaped + r'.*?)(\*\*Model-hint:\*\*\s*)(\S+)',
            re.DOTALL
        )
        plain_pat = re.compile(
            r'(#{1,6}\s+' + escaped + r'.*?)(^Model-hint:\s*)(\S+)',
            re.DOTALL | re.MULTILINE
        )

        hint: str = expected  # narrowed: None guarded above
        new_text, n = bold_pat.subn(lambda mo: mo.group(1) + mo.group(2) + hint, text, count=1)
        if n == 0:
            new_text, n = plain_pat.subn(lambda mo: mo.group(1) + mo.group(2) + hint, text, count=1)
        if n > 0:
            text = new_text
            corrections += 1
            print(f"[queue-validator] {tid}: Model-hint auto-fixed {actual} → {expected}", file=sys.stderr)

    if corrections:
        path.write_text(text)
    return corrections


def validate_task(task: dict) -> list[str]:
    errors: list[str] = []
    tid = task["id"]
    fields = task["fields"]

    if fields.get("Status", "").lower() != "queued":
        return []

    # 1. Required fields present and non-placeholder
    missing = []
    for field in REQUIRED_FIELDS:
        val = fields.get(field, "").strip()
        if not val:
            missing.append(field)
        elif field not in NULLABLE_FIELDS and val.lower() in ("tbd", "todo", "...", "[empty]"):
            missing.append(f"{field} (placeholder)")
    if missing:
        errors.append(f"{tid}: missing fields: {', '.join(missing)}")

    # 2. Type must be one of the valid values
    task_type = fields.get("Type", "").strip().lower()
    if task_type and task_type not in ("impl", "research", "gate"):
        errors.append(f"{tid}: Type '{task_type}' invalid — must be impl, research, or gate")

    # 3. File-count ≤ 4
    fc_raw = fields.get("File-count", "")
    fc_match = re.search(r'\d+', fc_raw)
    if fc_match:
        fc = int(fc_match.group())
        if fc > MAX_FILES:
            errors.append(f"{tid}: File-count {fc} exceeds ≤4 rule — split before queuing")

    # 3. Model-hint matches schema derivation (post --fix this should never fire)
    # qwen36 is an acceptable upgrade from qwen (reasoning-tier, same cost class)
    # Model-hint validation — accept round-robin alternatives within the same tier
    IMPL_MODELS = {'qwen-coder', 'llama', 'gpt-oss'}
    RESEARCH_MODELS = {'qwen', 'qwen36', 'nemotron', 'stepfun'}
    actual_hint = fields.get("Model-hint", "").strip().lower()
    expected_hint = derive_model_hint(fields)
    if expected_hint and actual_hint and actual_hint != expected_hint:
        # Allow round-robin: any model in the same tier is valid
        same_tier = False
        if expected_hint == 'qwen-coder' and actual_hint in IMPL_MODELS:
            same_tier = True
        if expected_hint == 'qwen' and actual_hint in RESEARCH_MODELS:
            same_tier = True
        if not same_tier:
            errors.append(
                f"{tid}: Model-hint '{actual_hint}' should be '{expected_hint}' or a same-tier alternative "
                f"(impl: {IMPL_MODELS}, research: {RESEARCH_MODELS})"
            )

    # 4. Spec must use SHALL
    spec = fields.get("Spec", "")
    if spec and "SHALL" not in spec:
        errors.append(f"{tid}: Spec missing SHALL — got: {spec[:80]}")

    # 5. Scenarios must be GIVEN/WHEN/THEN
    scenarios = fields.get("Scenarios", "")
    if scenarios and "GIVEN" not in scenarios.upper():
        errors.append(f"{tid}: Scenarios missing GIVEN/WHEN/THEN format")

    # 6. Impl tasks must have test files in Artifacts
    artifacts = fields.get("Artifacts", "")
    test_patterns = ('.test.', '.spec.', '__tests__/', 'test_', '/tests/')
    if task_type == "impl" and artifacts:
        has_tests = any(p in artifacts for p in test_patterns)
        if not has_tests:
            errors.append(
                f"{tid}: impl task has no test files in Artifacts — "
                "add test files (e.g. tests/test_foo.py, src/__tests__/foo.test.ts). "
                "TDD requires test artifacts for RED→GREEN execution."
            )

    # 7. Impl tasks must have real test execution in Verify (not just ls/echo)
    verify = fields.get("Verify", "")
    if task_type == "impl" and verify:
        test_cmds = ('pytest', 'vitest', 'jest', 'pnpm test', 'npm test', 'python -c')
        has_test_cmd = any(cmd in verify for cmd in test_cmds)
        if not has_test_cmd and verify.lower() not in ('none', ''):
            # Check if verify is ONLY ls/echo/cat (weak commands)
            weak_only = all(
                any(w in part.strip().split()[0] for w in ('ls', 'echo', 'cat', 'wc'))
                for part in verify.split('|') if part.strip()
            )
            if weak_only:
                errors.append(
                    f"{tid}: Verify has no test execution — only weak commands (ls/echo). "
                    "Add pytest/vitest/jest or a real assertion command."
                )

    # 8. Research tasks must have Verify with output check
    if task_type == "research":
        if not verify or verify.lower() in ('none', ''):
            errors.append(f"{tid}: research task has no Verify — add: ls logs/research/{tid}.md | wc -l logs/research/{tid}.md")

    return errors


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

    all_errors: list[str] = []
    for task in queued:
        all_errors.extend(validate_task(task))

    if all_errors:
        print(f"\n[queue-validator] {path} — {len(all_errors)} violation(s):", file=sys.stderr)
        for err in all_errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
