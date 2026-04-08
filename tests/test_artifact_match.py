"""Tests for queue_validator.artifacts and oms_work.validate._check_artifact_match."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'bin'))

from queue_validator.artifacts import validate as validate_artifacts


def _make_task(tid="TASK-001", overrides=None):
    fields = {
        "Status": "queued",
        "Type": "impl",
        "Spec": "The system SHALL validate tokens so that auth works.",
        "Artifacts": "src/auth/tokens.ts | tests/test_auth.test.ts",
    }
    if overrides:
        fields.update(overrides)
    return {"id": tid, "fields": fields}


class TestArtifactsValidation:
    def test_impl_with_tests_passes(self):
        task = _make_task()
        errors = validate_artifacts(task)
        assert not any("no test files" in e for e in errors)

    def test_impl_without_tests_fails(self):
        task = _make_task(overrides={"Artifacts": "src/auth/tokens.ts"})
        errors = validate_artifacts(task)
        assert any("no test files" in e for e in errors)

    def test_research_without_tests_ok(self):
        task = _make_task(overrides={"Type": "research", "Artifacts": "logs/research/TASK-001.md"})
        errors = validate_artifacts(task)
        assert not any("no test files" in e for e in errors)


class TestSpecArtifactsAlignment:
    def test_spec_path_in_artifacts_passes(self):
        task = _make_task(overrides={
            "Spec": "SHALL create src/auth/tokens.ts for token validation.",
            "Artifacts": "src/auth/tokens.ts | tests/test_auth.test.ts",
        })
        errors = validate_artifacts(task)
        assert not any("not in Artifacts" in e for e in errors)

    def test_spec_path_missing_from_artifacts_fails(self):
        task = _make_task(overrides={
            "Spec": "SHALL create src/auth/middleware.ts for request filtering.",
            "Artifacts": "src/auth/tokens.ts | tests/test_auth.test.ts",
        })
        errors = validate_artifacts(task)
        assert any("not in Artifacts" in e for e in errors)

    def test_spec_without_paths_passes(self):
        task = _make_task(overrides={
            "Spec": "SHALL validate JWT tokens so that unauthorized requests are rejected.",
        })
        errors = validate_artifacts(task)
        assert not any("not in Artifacts" in e for e in errors)


class TestArtifactMatchExecution:
    """Tests for _check_artifact_match (oms_work.validate)."""

    def test_all_artifacts_present(self, tmp_path):
        from oms_work.validate import _check_artifact_match
        (tmp_path / "src" / "auth").mkdir(parents=True)
        (tmp_path / "src" / "auth" / "tokens.ts").write_text("export {}")
        ok, issues = _check_artifact_match(tmp_path, ["src/auth/tokens.ts"], "impl")
        assert ok
        assert not issues

    def test_missing_artifact_fails(self, tmp_path):
        from oms_work.validate import _check_artifact_match
        ok, issues = _check_artifact_match(tmp_path, ["src/auth/tokens.ts"], "impl")
        assert not ok
        assert any("not found" in i for i in issues)

    def test_research_skipped(self, tmp_path):
        from oms_work.validate import _check_artifact_match
        ok, issues = _check_artifact_match(tmp_path, ["anything.ts"], "research")
        assert ok
