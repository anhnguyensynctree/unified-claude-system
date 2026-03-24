#!/usr/bin/env python3
"""
OMS post-step processor — called by oms-dispatcher.sh after each claude invocation.
Parses JSON output, extracts result text, updates cost log, budget, and checkpoint.

Usage: oms-post-step.py <tmpjson> <project_path> <task_id> <step> <slug>
Prints the result text to stdout. Updates files atomically.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone


def main():
    if len(sys.argv) < 6:
        sys.exit(1)

    tmpjson, project_path, task_id, step, slug = sys.argv[1:6]
    costs_dir = os.path.expanduser("~/.claude/oms-costs")
    budget_file = os.path.expanduser("~/.claude/oms-budget.json")
    cp_path = os.path.join(project_path, ".claude/oms-checkpoint.json")

    # --- Parse JSON output ---
    try:
        raw = open(tmpjson).read()
        try:
            data = json.loads(raw)
        except Exception:
            data = None
            for m in reversed(list(re.finditer(r"^\{", raw, re.MULTILINE))):
                try:
                    data = json.loads(raw[m.start():])
                    break
                except Exception:
                    continue
        if data is None:
            for line in raw.splitlines():
                s = line.strip()
                if s and not s.startswith("{") and not (s.startswith('"') and ":" in s):
                    print(s)
            sys.exit(0)
    except Exception:
        sys.exit(0)

    result = data.get("result", "")
    cost = data.get("total_cost_usd", 0) or 0
    new_session_id = data.get("session_id", "")
    effective_task = task_id or (new_session_id[:16] if new_session_id else "unknown")

    usage = data.get("usage", {})
    tokens_in = (usage.get("input_tokens", 0) or 0) + (usage.get("cache_read_input_tokens", 0) or 0)
    tokens_cache_write = usage.get("cache_creation_input_tokens", 0) or 0
    tokens_out = usage.get("output_tokens", 0) or 0

    # --- Atomic cost log update ---
    os.makedirs(costs_dir, exist_ok=True)
    cost_file = os.path.join(costs_dir, f"{slug}-{effective_task}.json")
    try:
        cdata = json.load(open(cost_file)) if os.path.exists(cost_file) else \
                {"task_id": effective_task, "slug": slug, "steps": [], "total_usd": 0}
        cdata["steps"].append({
            "step": step,
            "cost_usd": round(cost, 6),
            "ts": datetime.now(timezone.utc).isoformat(),
            "tokens_in": tokens_in,
            "tokens_cache_write": tokens_cache_write,
            "tokens_out": tokens_out,
        })
        cdata["total_usd"] = round(sum(s["cost_usd"] for s in cdata["steps"]), 6)
        tmp = cost_file + ".tmp"
        json.dump(cdata, open(tmp, "w"))
        os.replace(tmp, cost_file)
    except Exception:
        pass

    # --- Atomic budget update (session window + weekly) ---
    if os.path.exists(budget_file):
        try:
            b = json.load(open(budget_file))
            now = datetime.now(timezone.utc)

            # --- Session window (5h rolling) ---
            window_hours = b.get("session_window_hours", 5)
            session_start_raw = b.get("current_session_start", "")
            session_reset = False
            if session_start_raw:
                try:
                    ss = datetime.fromisoformat(session_start_raw)
                    if ss.tzinfo is None:
                        ss = ss.replace(tzinfo=timezone.utc)
                    if now - ss > timedelta(hours=window_hours):
                        session_reset = True
                except Exception:
                    session_reset = True
            else:
                session_reset = True

            if session_reset:
                b["current_session_start"] = now.isoformat()
                b["current_session_spend_usd"] = round(cost, 6)
            else:
                b["current_session_spend_usd"] = round(
                    b.get("current_session_spend_usd", 0) + cost, 6
                )

            # --- Weekly window (7d rolling) ---
            week_start_raw = b.get("current_week_start", "")
            if week_start_raw:
                try:
                    ws = datetime.fromisoformat(week_start_raw)
                    if ws.tzinfo is None:
                        ws = ws.replace(tzinfo=timezone.utc)
                    if now - ws > timedelta(days=7):
                        b["current_week_start"] = now.isoformat()
                        b["current_week_spend_usd"] = round(cost, 6)
                    else:
                        b["current_week_spend_usd"] = round(
                            b.get("current_week_spend_usd", 0) + cost, 6
                        )
                except Exception:
                    b["current_week_spend_usd"] = round(
                        b.get("current_week_spend_usd", 0) + cost, 6
                    )
            else:
                b["current_week_start"] = now.isoformat()
                b["current_week_spend_usd"] = round(cost, 6)

            b["last_updated"] = now.isoformat()
            tmp = budget_file + ".tmp"
            json.dump(b, open(tmp, "w"))
            os.replace(tmp, budget_file)
        except Exception:
            pass

    # --- Update checkpoint: session_id + steps_written ---
    if new_session_id and os.path.exists(cp_path):
        try:
            cp = json.load(open(cp_path))
            cp["session_id"] = new_session_id
            if step and step not in ("", "done", "complete", "waiting_ceo", "pipeline_frozen"):
                written = cp.get("steps_written", [])
                if step not in written:
                    written.append(step)
                cp["steps_written"] = written
            tmp = cp_path + ".tmp"
            json.dump(cp, open(tmp, "w"))
            os.replace(tmp, cp_path)
        except Exception:
            pass

    print(result)


if __name__ == "__main__":
    main()
