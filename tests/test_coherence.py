"""Tests for queue_validator.coherence — Spec↔Scenario cross-field validation."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'bin'))

from queue_validator.coherence import validate, _stem, _extract_spec_terms


class TestStem:
    def test_removes_common_suffixes(self):
        assert _stem('responses') == 'respons'
        assert _stem('caching') == 'cach'
        assert _stem('reduced') == 'reduc'
        assert _stem('validation') == 'valid'

    def test_preserves_short_words(self):
        assert _stem('cache') == 'cache'
        assert _stem('test') == 'test'
        assert _stem('api') == 'api'

    def test_preserves_unstemable(self):
        assert _stem('auth') == 'auth'
        assert _stem('jwt') == 'jwt'


class TestExtractSpecTerms:
    def test_extracts_after_shall(self):
        terms = _extract_spec_terms("The system SHALL cache API responses so that latency is reduced.")
        assert 'cache' in terms
        assert len(terms) >= 2

    def test_empty_without_shall(self):
        assert _extract_spec_terms("No shall keyword here") == set()

    def test_filters_filler(self):
        terms = _extract_spec_terms("SHALL be in the system for all")
        assert 'the' not in terms
        assert 'for' not in terms


class TestCoherenceValidation:
    def _make_task(self, spec, scenarios, task_type="impl"):
        return {
            "id": "TASK-001",
            "fields": {
                "Status": "queued",
                "Type": task_type,
                "Spec": spec,
                "Scenarios": scenarios,
            },
        }

    def test_matching_spec_scenarios_pass(self):
        task = self._make_task(
            "The system SHALL validate JWT tokens so that unauthorized requests are rejected.",
            ("GIVEN no Authorization header WHEN POST /api/data THEN unauthorized request rejected with status 401 | "
             "GIVEN expired JWT token WHEN POST /api/data THEN request rejected with status 401"),
        )
        errors = validate(task)
        assert not any("coherence" in e.lower() for e in errors)

    def test_completely_mismatched_fails(self):
        task = self._make_task(
            "The system SHALL cache API responses so that latency is reduced.",
            ("GIVEN user logged in WHEN profile page loads THEN avatar displays | "
             "GIVEN admin WHEN dashboard opens THEN metrics render"),
        )
        errors = validate(task)
        assert any("coherence" in e.lower() for e in errors)

    def test_research_tasks_skipped(self):
        task = self._make_task(
            "The system SHALL cache API responses.",
            "GIVEN user WHEN action THEN result",
            task_type="research",
        )
        errors = validate(task)
        assert errors == []

    def test_empty_spec_skipped(self):
        task = self._make_task("", "GIVEN x WHEN y THEN z")
        errors = validate(task)
        assert errors == []

    @patch('queue_validator.coherence._haiku_coherence_check')
    def test_haiku_check_called_after_deterministic_pass(self, mock_haiku):
        mock_haiku.return_value = (True, 'YES — all behaviors covered')
        task = self._make_task(
            "The system SHALL validate JWT tokens so that unauthorized requests are rejected.",
            ("GIVEN no Authorization header WHEN POST /api/data THEN unauthorized request rejected with status 401 | "
             "GIVEN expired JWT token WHEN POST /api/data THEN request rejected with status 401"),
        )
        errors = validate(task)
        mock_haiku.assert_called_once()
        assert errors == []

    @patch('queue_validator.coherence._haiku_coherence_check')
    def test_haiku_failure_blocks(self, mock_haiku):
        mock_haiku.return_value = (False, 'NO — Spec says validate tokens but no scenario tests token validation')
        task = self._make_task(
            "The system SHALL validate JWT tokens so that unauthorized requests are rejected.",
            ("GIVEN no Authorization header WHEN POST /api/data THEN unauthorized request rejected with status 401 | "
             "GIVEN expired JWT token WHEN POST /api/data THEN request rejected with status 401"),
        )
        errors = validate(task)
        assert any("semantic coherence FAIL" in e for e in errors)

    @patch('queue_validator.coherence._haiku_coherence_check')
    def test_haiku_not_called_when_deterministic_fails(self, mock_haiku):
        task = self._make_task(
            "The system SHALL cache API responses so that latency is reduced.",
            ("GIVEN user logged in WHEN profile page loads THEN avatar displays | "
             "GIVEN admin WHEN dashboard opens THEN metrics render"),
        )
        errors = validate(task)
        mock_haiku.assert_not_called()
        assert len(errors) >= 1
