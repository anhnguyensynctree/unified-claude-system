"""Tests for validate-queue.py — P0/P1 enforcement additions."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add bin to path so we can import queue_validator package
sys.path.insert(0, str(Path(__file__).parent.parent / 'bin'))

import queue_validator as vq
from queue_validator.verify import _lint_verify_syntax
from queue_validator.dependencies import validate as _validate_deps_fn
from queue_validator.parser import parse_tasks


def _make_task(tid="TASK-001", overrides=None):
    """Create a minimal valid queued task."""
    fields = {
        "Status": "queued",
        "Feature": "FEATURE-001",
        "Milestone": "auth-revamp",
        "Department": "backend",
        "Type": "impl",
        "Infra-critical": "false",
        "Spec": "The system SHALL validate JWT tokens so that unauthorized requests are rejected.",
        "Scenarios": (
            "GIVEN no Authorization header WHEN POST /api/data THEN unauthorized request rejected with status 401 | "
            "GIVEN expired JWT token WHEN POST /api/data THEN request rejected with status 401"
        ),
        "Artifacts": "src/auth/tokens.ts — exports: verifyToken | tests/test_auth.test.ts",
        "Produces": "src/auth/tokens.ts — exports: verifyToken",
        "Verify": "pytest tests/test_auth.py -v | npx tsc --noEmit",
        "Context": "src/auth/middleware.ts",
        "Activated": "cto, backend-developer",
        "Validation": "dev → qa → em",
        "Depends": "none",
        "File-count": "2",
        "Model-hint": "qwen-coder",
    }
    if overrides:
        fields.update(overrides)
    return {"id": tid, "fields": fields}


# ── Verify syntax linting ──────────────────────────────────────────────

class TestVerifySyntaxLint:
    def test_valid_command_passes(self):
        assert _lint_verify_syntax("pytest tests/ -v") is None

    def test_valid_pipe_passes(self):
        assert _lint_verify_syntax("test -f output.md") is None

    def test_invalid_syntax_returns_error(self):
        err = _lint_verify_syntax("if then fi broken")
        assert err is not None

    def test_unclosed_quote_returns_error(self):
        err = _lint_verify_syntax("echo 'unclosed")
        assert err is not None


# ── Dependency validation ──────────────────────────────────────────────

class TestDependencyValidation:
    def test_valid_depends_passes(self):
        t1 = _make_task("TASK-001", {"Depends": "none"})
        t2 = _make_task("TASK-002", {"Depends": "TASK-001"})
        errors = _validate_deps_fn(t2, all_tasks=[t1, t2])
        assert errors == []

    def test_nonexistent_depends_fails(self):
        t = _make_task("TASK-001", {"Depends": "TASK-999"})
        errors = _validate_deps_fn(t, all_tasks=[t])
        assert any("TASK-999" in e and "does not exist" in e for e in errors)

    def test_circular_depends_detected(self):
        t1 = _make_task("TASK-001", {"Depends": "TASK-002"})
        t2 = _make_task("TASK-002", {"Depends": "TASK-001"})
        errors = _validate_deps_fn(t1, all_tasks=[t1, t2])
        assert any("circular" in e for e in errors)

    def test_deep_chain_detected(self):
        t1 = _make_task("TASK-001", {"Depends": "none"})
        t2 = _make_task("TASK-002", {"Depends": "TASK-001"})
        t3 = _make_task("TASK-003", {"Depends": "TASK-002"})
        t4 = _make_task("TASK-004", {"Depends": "TASK-003"})
        t5 = _make_task("TASK-005", {"Depends": "TASK-004"})
        all_tasks = [t1, t2, t3, t4, t5]
        errors = _validate_deps_fn(t5, all_tasks=all_tasks)
        assert any("depth" in e and "exceeds" in e for e in errors)

    def test_depth_3_is_ok(self):
        t1 = _make_task("TASK-001", {"Depends": "none"})
        t2 = _make_task("TASK-002", {"Depends": "TASK-001"})
        t3 = _make_task("TASK-003", {"Depends": "TASK-002"})
        t4 = _make_task("TASK-004", {"Depends": "TASK-003"})
        all_tasks = [t1, t2, t3, t4]
        errors = _validate_deps_fn(t4, all_tasks=all_tasks)
        assert not any("depth" in e for e in errors)

    def test_none_depends_passes(self):
        t = _make_task("TASK-001", {"Depends": "none"})
        errors = _validate_deps_fn(t, all_tasks=[t])
        assert errors == []


# ── Scenario quality validation ────────────────────────────────────────

class TestScenarioQuality:
    def test_valid_scenarios_pass(self):
        task = _make_task()
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("Scenario" in e for e in errors)

    def test_single_scenario_fails(self):
        task = _make_task(overrides={
            "Scenarios": "GIVEN user WHEN login THEN response is 200"
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("minimum 2" in e for e in errors)

    def test_vague_then_fails(self):
        task = _make_task(overrides={
            "Scenarios": (
                "GIVEN user WHEN login THEN system works correctly | "
                "GIVEN admin WHEN delete THEN action completes properly"
            )
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("vague" in e for e in errors)

    def test_observable_then_passes(self):
        task = _make_task(overrides={
            "Scenarios": (
                "GIVEN no auth header WHEN POST /api THEN response status is 401 | "
                "GIVEN valid token WHEN POST /api THEN response status is 200"
            )
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("vague" in e for e in errors)

    def test_malformed_given_only_fails(self):
        """GIVEN without uppercase WHEN/THEN should fail — either as incomplete parse or count < 2."""
        task = _make_task(overrides={
            "Scenarios": "GIVEN a user exists with valid credentials"
        })
        errors = vq.validate_task(task, all_tasks=[task])
        # Should fail either for no complete GIVEN/WHEN/THEN or for count < 2
        assert any("Scenario" in e for e in errors)


# ── Produces format validation ─────────────────────────────────────────

class TestProducesFormat:
    def test_file_path_passes(self):
        task = _make_task(overrides={"Produces": "src/auth/tokens.ts — exports: verifyToken"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("Produces" in e and "not a file path" in e for e in errors)

    def test_none_passes(self):
        task = _make_task(overrides={"Produces": "none"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("Produces" in e for e in errors)

    def test_prose_produces_fails(self):
        task = _make_task(overrides={"Produces": "database schema design"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("not a file path" in e for e in errors)


# ── Verify prose detection ─────────────────────────────────────────────

class TestVerifyProse:
    def test_valid_verify_passes(self):
        task = _make_task(overrides={"Verify": "pytest tests/ -v | npx tsc --noEmit"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("prose" in e.lower() for e in errors)

    def test_prose_verify_fails(self):
        task = _make_task(overrides={"Verify": "server returns 200 on valid request"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("prose" in e.lower() for e in errors)


# ── Verify syntax lint integration ─────────────────────────────────────

class TestVerifySyntaxInValidation:
    def test_broken_syntax_caught(self):
        task = _make_task(overrides={
            "Verify": "pytest tests/ -v | if then fi"
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("syntax error" in e.lower() for e in errors)

    def test_valid_syntax_passes(self):
        task = _make_task(overrides={
            "Verify": "pytest tests/ -v | test -f output.md"
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("syntax error" in e.lower() for e in errors)


# ── Context file existence ─────────────────────────────────────────────

class TestContextFileExistence:
    def test_existing_file_passes(self, tmp_path):
        (tmp_path / "src" / "auth").mkdir(parents=True)
        (tmp_path / "src" / "auth" / "middleware.ts").write_text("export default {}")
        task = _make_task(overrides={"Context": "src/auth/middleware.ts"})
        errors = vq.validate_task(task, all_tasks=[task], project_root=tmp_path)
        assert not any("Context file not found" in e for e in errors)

    def test_missing_file_fails(self, tmp_path):
        task = _make_task(overrides={"Context": "src/nonexistent/file.ts"})
        errors = vq.validate_task(task, all_tasks=[task], project_root=tmp_path)
        assert any("Context file not found" in e for e in errors)

    def test_prose_context_skipped(self, tmp_path):
        task = _make_task(overrides={"Context": '"design decision rationale"'})
        errors = vq.validate_task(task, all_tasks=[task], project_root=tmp_path)
        assert not any("Context file not found" in e for e in errors)

    def test_new_file_marker_skipped(self, tmp_path):
        task = _make_task(overrides={"Context": "src/new/file.ts [new file]"})
        errors = vq.validate_task(task, all_tasks=[task], project_root=tmp_path)
        assert not any("Context file not found" in e for e in errors)


# ── Cross-field coherence ──────────────────────────────────────────────

class TestCrossFieldCoherence:
    def test_matching_terms_no_warning(self):
        task = _make_task(overrides={
            "Spec": "The system SHALL cache API responses so that latency is reduced.",
            "Scenarios": (
                "GIVEN API response received WHEN cache lookup succeeds THEN cached response returned | "
                "GIVEN cache expired WHEN API called THEN fresh response fetched and cache updated"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("coherence" in e.lower() for e in errors)

    def test_mismatched_spec_scenarios_warns(self):
        task = _make_task(overrides={
            "Spec": "The system SHALL cache API responses so that latency is reduced.",
            "Scenarios": (
                "GIVEN user logged in WHEN profile page loads THEN avatar displays | "
                "GIVEN admin WHEN dashboard opens THEN metrics render"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("coherence" in e.lower() for e in errors)


# ── Full validation integration ────────────────────────────────────────

class TestFullValidation:
    def test_valid_task_has_no_errors(self):
        task = _make_task()
        errors = vq.validate_task(task, all_tasks=[task])
        assert errors == []

    def test_non_queued_task_skipped(self):
        task = _make_task(overrides={"Status": "done"})
        errors = vq.validate_task(task, all_tasks=[task])
        assert errors == []

    def test_missing_fields_caught(self):
        task = _make_task(overrides={"Spec": "", "Type": ""})
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("missing fields" in e for e in errors)


# ── Parse tasks ────────────────────────────────────────────────────────

class TestParseTasks:
    def test_parses_bold_format(self):
        text = """## TASK-001 — Test task
- **Status:** queued
- **Feature:** FEATURE-001
- **Type:** impl
"""
        tasks = vq.parse_tasks(text)
        assert len(tasks) == 1
        assert tasks[0]["id"] == "TASK-001"
        assert tasks[0]["fields"]["Status"] == "queued"

    def test_parses_multiple_tasks(self):
        text = """## TASK-001 — First
- **Status:** queued

## TASK-002 — Second
- **Status:** queued
"""
        tasks = vq.parse_tasks(text)
        assert len(tasks) == 2


# ── NEW: Artifact↔Verify cross-check ──────────────────────────────────

class TestArtifactVerifyCrossCheck:
    def test_matching_stems_pass(self):
        task = _make_task(overrides={
            "Artifacts": "src/auth/tokens.ts | tests/test_auth.test.ts",
            "Verify": "pytest tests/test_auth.py -v",
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("path overlap" in e for e in errors)

    def test_no_overlap_warns(self):
        task = _make_task(overrides={
            "Artifacts": "src/billing/invoice.ts | tests/test_billing.test.ts",
            "Verify": "pytest tests/test_unrelated.py -v",
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("path overlap" in e for e in errors)

    def test_directory_overlap_passes(self):
        task = _make_task(overrides={
            "Artifacts": "src/auth/tokens.ts | tests/auth/test_tokens.test.ts",
            "Verify": "pytest tests/auth/ -v",
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("path overlap" in e for e in errors)

    def test_research_tasks_skip_check(self):
        task = _make_task(overrides={
            "Type": "research",
            "Artifacts": "logs/research/TASK-001.md",
            "Verify": "test -f logs/research/TASK-001.md",
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("path overlap" in e for e in errors)


# ── NEW: THEN observability check ──────────────────────────────────────

class TestThenObservability:
    def test_then_with_status_code_passes(self):
        task = _make_task(overrides={
            "Scenarios": (
                "GIVEN no auth WHEN POST /api THEN response status is 401 | "
                "GIVEN valid auth WHEN POST /api THEN response status is 200"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("observable outcome" in e for e in errors)

    def test_then_with_path_passes(self):
        task = _make_task(overrides={
            "Scenarios": (
                "GIVEN config loaded WHEN app starts THEN src/config.ts exports validated config | "
                "GIVEN invalid config WHEN app starts THEN error logged to stderr"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("observable outcome" in e for e in errors)

    def test_then_with_quoted_string_passes(self):
        task = _make_task(overrides={
            "Scenarios": (
                'GIVEN user input WHEN submitted THEN output contains "success" | '
                "GIVEN no input WHEN submitted THEN error message returned with status 400"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert not any("observable outcome" in e for e in errors)

    def test_vague_then_fails(self):
        task = _make_task(overrides={
            "Scenarios": (
                "GIVEN something WHEN action THEN the system handles it gracefully | "
                "GIVEN other thing WHEN trigger THEN response status is 200"
            ),
        })
        errors = vq.validate_task(task, all_tasks=[task])
        assert any("observable outcome" in e for e in errors)


# ── NEW: Duplicate Spec detection ──────────────────────────────────────

class TestDuplicateDetection:
    def test_identical_specs_detected(self):
        task1 = _make_task("TASK-001")
        task2 = _make_task("TASK-002")
        from queue_validator.spec import validate_duplicates
        warnings = validate_duplicates([task1, task2])
        assert len(warnings) == 1
        assert "similar Specs" in warnings[0]

    def test_different_specs_clean(self):
        task1 = _make_task("TASK-001", overrides={
            "Spec": "The system SHALL cache API responses so that latency is reduced."
        })
        task2 = _make_task("TASK-002", overrides={
            "Spec": "The system SHALL send email notifications so that users are informed."
        })
        from queue_validator.spec import validate_duplicates
        warnings = validate_duplicates([task1, task2])
        assert len(warnings) == 0


# ── NEW: Feature-level validation ──────────────────────────────────────

class TestFeatureValidation:
    def test_draft_feature_missing_fields(self):
        from queue_validator.features import validate_features
        text = """## FEATURE-001 — My Feature
- **Status:** draft
- **Milestone:** test-milestone
- **Type:** product
"""
        errors = validate_features(text)
        # Missing: Departments, Why, Exec-decision, Acceptance, Validation
        assert len(errors) >= 4

    def test_done_feature_skipped(self):
        from queue_validator.features import validate_features
        text = """## FEATURE-001 — My Feature
- **Status:** done
"""
        errors = validate_features(text)
        assert len(errors) == 0

    def test_complete_draft_feature_passes(self):
        from queue_validator.features import validate_features
        text = """## FEATURE-001 — My Feature
- **Status:** draft
- **Milestone:** auth-revamp
- **Type:** product
- **Departments:** backend-developer
- **Why:** Users need secure authentication
- **Exec-decision:** Use JWT with short expiry
- **Acceptance:** Users can log in and stay logged in for 24h
- **Validation:** cpo
"""
        errors = validate_features(text)
        assert len(errors) == 0
