"""Tests for queue_validator.produces — Produces format + Produces↔Depends chain integrity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'bin'))

from queue_validator.produces import validate


def _make_task(tid="TASK-001", overrides=None):
    fields = {
        "Status": "queued",
        "Produces": "src/auth/tokens.ts — exports: verifyToken",
        "Depends": "none",
        "Context": "src/auth/middleware.ts",
    }
    if overrides:
        fields.update(overrides)
    return {"id": tid, "fields": fields}


class TestProducesFormat:
    def test_file_path_passes(self):
        task = _make_task(overrides={"Produces": "src/auth/tokens.ts"})
        assert not validate(task)

    def test_none_passes(self):
        task = _make_task(overrides={"Produces": "none"})
        assert not validate(task)

    def test_prose_fails(self):
        task = _make_task(overrides={"Produces": "database schema design"})
        errors = validate(task)
        assert any("not a file path" in e for e in errors)

    def test_pipe_separated_paths_pass(self):
        task = _make_task(overrides={"Produces": "src/a.ts | src/b.ts"})
        assert not validate(task)


class TestProducesChain:
    def test_valid_chain_passes(self):
        t1 = _make_task("TASK-001", {"Produces": "src/auth/tokens.ts", "Depends": "none"})
        t2 = _make_task("TASK-002", {
            "Depends": "TASK-001",
            "Context": "src/auth/tokens.ts, config.ts",
            "Produces": "none",
        })
        errors = validate(t2, all_tasks=[t1, t2])
        assert not errors

    def test_missing_context_reference_fails(self):
        t1 = _make_task("TASK-001", {"Produces": "src/auth/tokens.ts", "Depends": "none"})
        t2 = _make_task("TASK-002", {
            "Depends": "TASK-001",
            "Context": "some/other/file.ts",
            "Produces": "none",
        })
        errors = validate(t2, all_tasks=[t1, t2])
        assert any("Context doesn't reference" in e for e in errors)

    def test_upstream_none_produces_skipped(self):
        t1 = _make_task("TASK-001", {"Produces": "none", "Depends": "none"})
        t2 = _make_task("TASK-002", {
            "Depends": "TASK-001",
            "Context": "whatever.ts",
            "Produces": "none",
        })
        errors = validate(t2, all_tasks=[t1, t2])
        assert not errors

    def test_nonexistent_dep_skipped(self):
        """Missing dep ID is handled by dependencies.py, not produces.py."""
        t = _make_task("TASK-001", {"Depends": "TASK-999", "Produces": "none", "Context": ""})
        errors = validate(t, all_tasks=[t])
        assert not any("Context doesn't reference" in e for e in errors)
