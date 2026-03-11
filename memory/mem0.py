#!/usr/bin/env python3
"""mem0.py — minimal memory extraction for Claude Code.

Usage:
  mem0.py extract <transcript_path>          # extracts facts, saves to project facts.json
  mem0.py retrieve <facts_path> [global]     # prints facts for context injection
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone
from urllib import request as urllib_request
from pathlib import Path

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"

EXTRACT_SYSTEM = """Extract memorable facts from this conversation. Focus on:
- User preferences, habits, workflow decisions
- Technical decisions (tools, frameworks, patterns chosen)
- Project context (what they're building, goals, constraints)
- Problems solved or discovered
- Personal context (role, environment, recurring needs)

Output ONLY a JSON array of concise strings. Each fact max 25 words.
Example: ["Prefers bun over npm", "Uses TDD with 80% coverage minimum"]
If nothing memorable, output: []"""

UPDATE_SYSTEM = """Classify each new fact against existing memories.
Output a JSON array of operations:
[{"op":"ADD","fact":"..."},{"op":"UPDATE","id":"...","fact":"..."},{"op":"NOOP","fact":"..."}]

Rules:
- ADD: genuinely new information not in existing memories
- UPDATE: refines or corrects an existing memory — include the id to replace
- NOOP: already captured (equivalent info exists)
Be conservative: prefer NOOP over duplicate ADD."""

HANDOFF_SYSTEM = """Extract a session handoff. Output ONLY valid JSON:
{"decisions":["choice + WHY"],"next_steps":["ordered actions"],"blockers":["unresolved issues"],"open_questions":["things to revisit"],"files":["paths modified"]}
Max 5 per list. Empty list [] if none. Be specific."""


def api_call(system: str, user: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }).encode()
    req = urllib_request.Request(
        API_URL, data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib_request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["content"][0]["text"]


def load_facts(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_facts(path: Path, facts: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(facts, indent=2))


def get_cwd_from_transcript(transcript_path: str) -> str | None:
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    cwd = entry.get("cwd")
                    if cwd:
                        return cwd
                except (json.JSONDecodeError, AttributeError):
                    continue
    except OSError:
        pass
    return None


def read_transcript(transcript_path: str) -> str:
    lines = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    msg = entry.get("message", {})
                    role = msg.get("role", "")
                    if role not in ("user", "assistant"):
                        continue
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        parts = [
                            b.get("text", "") for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        content = " ".join(parts)
                    if content and isinstance(content, str):
                        text = content[:600].strip()
                        if text:
                            lines.append(f"{role}: {text}")
                except (json.JSONDecodeError, AttributeError):
                    continue
    except OSError as e:
        raise RuntimeError(f"Cannot read transcript: {e}")
    return "\n".join(lines[-80:])


def extract(transcript_path: str):
    if not ANTHROPIC_API_KEY:
        print("[mem0] Set ANTHROPIC_API_KEY in ~/.zshrc to enable extraction", file=sys.stderr)
        return

    cwd = get_cwd_from_transcript(transcript_path)
    if not cwd:
        print("[mem0] Cannot determine project cwd — skipping", file=sys.stderr)
        return

    encoded = cwd.replace("/", "-")
    home = Path.home()
    facts_path = home / ".claude" / "projects" / encoded / "memory" / "facts.json"

    try:
        conversation = read_transcript(transcript_path)
    except RuntimeError as e:
        print(f"[mem0] {e}", file=sys.stderr)
        return

    if len(conversation.strip()) < 100:
        print("[mem0] Conversation too short — skipping", file=sys.stderr)
        return

    try:
        raw = api_call(EXTRACT_SYSTEM, f"Conversation:\n{conversation}")
        new_facts = json.loads(raw)
        if not isinstance(new_facts, list):
            raise ValueError("Expected list")
    except Exception as e:
        print(f"[mem0] Extraction failed: {e}", file=sys.stderr)
        return

    if not new_facts:
        print("[mem0] No memorable facts found", file=sys.stderr)
        return

    existing = load_facts(facts_path)
    existing_summary = (
        "\n".join(f"[{m['id']}] {m['content']}" for m in existing)
        or "(none)"
    )

    try:
        ops_raw = api_call(
            UPDATE_SYSTEM,
            f"Existing memories:\n{existing_summary}\n\nNew facts:\n{json.dumps(new_facts)}"
        )
        ops = json.loads(ops_raw)
        if not isinstance(ops, list):
            raise ValueError("Expected list")
    except Exception as e:
        print(f"[mem0] Classification failed: {e} — adding all as new", file=sys.stderr)
        ops = [{"op": "ADD", "fact": f} for f in new_facts]

    now = datetime.now(timezone.utc).isoformat()
    added = updated = skipped = 0

    for op in ops:
        action = op.get("op", "NOOP")
        if action == "ADD" and op.get("fact"):
            existing.append({
                "id": str(uuid.uuid4()),
                "content": op["fact"],
                "created_at": now,
                "updated_at": now
            })
            added += 1
        elif action == "UPDATE" and op.get("id") and op.get("fact"):
            for mem in existing:
                if mem["id"] == op["id"]:
                    mem["content"] = op["fact"]
                    mem["updated_at"] = now
                    updated += 1
                    break
        else:
            skipped += 1

    save_facts(facts_path, existing)
    print(
        f"[mem0] +{added} added, ~{updated} updated, {skipped} skipped "
        f"→ {len(existing)} total in {facts_path}",
        file=sys.stderr
    )


def handoff(transcript_path: str, date: str):
    if not ANTHROPIC_API_KEY:
        return

    try:
        conversation = read_transcript(transcript_path)
    except RuntimeError as e:
        print(f"[mem0-handoff] {e}", file=sys.stderr)
        return

    if len(conversation.strip()) < 100:
        print("[mem0-handoff] Conversation too short — skipping", file=sys.stderr)
        return

    try:
        raw = api_call(HANDOFF_SYSTEM, f"Conversation:\n{conversation}")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected dict")
    except Exception as e:
        print(f"[mem0-handoff] Failed: {e}", file=sys.stderr)
        return

    session_file = Path.home() / ".claude" / "sessions" / f"{date}-session.tmp"
    if not session_file.exists():
        print(f"[mem0-handoff] Session file not found: {session_file}", file=sys.stderr)
        return

    sections = [
        ("Decisions", "decisions"),
        ("Next steps", "next_steps"),
        ("Blockers", "blockers"),
        ("Open questions", "open_questions"),
        ("Files modified", "files"),
    ]
    lines = []
    for label, key in sections:
        items = data.get(key, [])
        if items:
            lines.append(f"**{label}:** " + "; ".join(str(i) for i in items))

    if lines:
        with open(session_file, "a") as f:
            f.write("\n\n---\n## Handoff\n" + "\n".join(lines) + "\n")
        print(f"[mem0-handoff] Written to {session_file}", file=sys.stderr)
    else:
        print("[mem0-handoff] Nothing to write", file=sys.stderr)


def retrieve(facts_path: Path, global_facts_path: Path | None = None) -> str:
    global_facts = []
    if global_facts_path and global_facts_path.exists() and global_facts_path != facts_path:
        global_facts = load_facts(global_facts_path)
    project_facts = load_facts(facts_path)
    all_facts = global_facts + project_facts
    if not all_facts:
        return ""
    return "\n".join(f"- {m['content']}" for m in all_facts)


def main():
    if len(sys.argv) < 2:
        print("Usage: mem0.py extract <transcript>", file=sys.stderr)
        print("       mem0.py retrieve <facts_path> [global_facts_path]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "extract":
        if len(sys.argv) < 3:
            print("[mem0] extract requires <transcript_path>", file=sys.stderr)
            sys.exit(1)
        extract(sys.argv[2])

    elif cmd == "handoff":
        if len(sys.argv) < 4:
            print("[mem0] handoff requires <transcript_path> <date>", file=sys.stderr)
            sys.exit(1)
        handoff(sys.argv[2], sys.argv[3])

    elif cmd == "retrieve":
        if len(sys.argv) < 3:
            print("[mem0] retrieve requires <facts_path>", file=sys.stderr)
            sys.exit(1)
        global_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        print(retrieve(Path(sys.argv[2]), global_path))

    else:
        print(f"[mem0] Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
