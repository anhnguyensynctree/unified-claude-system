"""Tests for _parse_actions, _build_agent_prompt, _extract_pytest_failures, and related from oms_work package."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'bin'))

# Mock discord before importing oms_work (it imports oms_discord at package level)
import types
discord_mock = types.ModuleType('discord_notify')
discord_mock.DiscordNotifier = type('DiscordNotifier', (), {'__init__': lambda *a, **kw: None})
sys.modules['discord_notify'] = discord_mock

from oms_work.agent import _parse_actions, _build_agent_prompt, _extract_test_failures, _extract_pytest_failures, _format_error_feedback  # noqa: E402
from oms_work.validate import _parse_scenarios, _check_scenario_coverage, _parse_qa_verdicts  # noqa: E402


class TestParseActions:
    """Test _parse_actions with various LLM output formats."""

    def test_write_action(self):
        response = (
            "WRITE src/main.py\n"
            "```\n"
            "print('hello')\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'WRITE'
        assert actions[0]['path'] == 'src/main.py'
        assert "print('hello')" in actions[0]['content']

    def test_run_action(self):
        response = "RUN pip install requests\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'RUN'
        assert actions[0]['cmd'] == 'pip install requests'

    def test_done_action(self):
        response = "DONE All files written and tests pass.\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'DONE'
        assert 'All files written' in actions[0]['summary']

    def test_done_without_summary(self):
        response = "DONE\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'DONE'

    def test_multiple_actions(self):
        response = (
            "WRITE src/config.py\n"
            "```\n"
            "DB_URL = 'sqlite:///test.db'\n"
            "```\n"
            "\n"
            "WRITE src/main.py\n"
            "```\n"
            "from config import DB_URL\n"
            "print(DB_URL)\n"
            "```\n"
            "\n"
            "RUN python src/main.py\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 3
        assert actions[0]['type'] == 'WRITE'
        assert actions[0]['path'] == 'src/config.py'
        assert actions[1]['type'] == 'WRITE'
        assert actions[1]['path'] == 'src/main.py'
        assert actions[2]['type'] == 'RUN'

    def test_write_then_done(self):
        response = (
            "WRITE tests/test_app.py\n"
            "```\n"
            "def test_hello():\n"
            "    assert True\n"
            "```\n"
            "\n"
            "DONE Wrote test file.\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 2
        assert actions[0]['type'] == 'WRITE'
        assert actions[1]['type'] == 'DONE'

    def test_fallback_heading_code_block(self):
        """Fallback: ### path followed by code block should parse as WRITE."""
        response = (
            "### src/utils.py\n"
            "```python\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'WRITE'
        assert actions[0]['path'] == 'src/utils.py'

    def test_fallback_bold_code_block(self):
        """Fallback: **path** followed by code block should parse as WRITE."""
        response = (
            "**src/helpers.py**\n"
            "```python\n"
            "def multiply(a, b):\n"
            "    return a * b\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'WRITE'
        assert actions[0]['path'] == 'src/helpers.py'

    def test_fallback_dollar_command(self):
        """Fallback: $ command should parse as RUN."""
        response = "$ pytest tests/\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'RUN'
        assert actions[0]['cmd'] == 'pytest tests/'

    def test_fallback_completion_phrase(self):
        """Fallback: completion phrases should parse as DONE."""
        response = "I've completed all the required changes.\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'DONE'

    def test_empty_response(self):
        actions = _parse_actions("")
        assert actions == []

    def test_irrelevant_text_ignored(self):
        response = "Let me think about this problem carefully.\nThe approach should be modular.\n"
        actions = _parse_actions(response)
        assert actions == []

    def test_case_insensitive(self):
        response = "write src/app.py\n```\ncode\n```\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'WRITE'

    def test_run_case_insensitive(self):
        response = "run npm test\n"
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'RUN'

    def test_content_preserves_newlines(self):
        response = (
            "WRITE src/multi.py\n"
            "```\n"
            "line1\n"
            "line2\n"
            "line3\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert 'line1\nline2\nline3' in actions[0]['content']

    def test_dotfile_heading_fallback(self):
        """Heading fallback must handle dotfiles like .env.example."""
        response = (
            "### .env.example\n"
            "```\n"
            "API_KEY=your_key\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['type'] == 'WRITE'
        assert actions[0]['path'] == '.env.example'

    def test_dotfile_gitignore_heading(self):
        """Heading fallback must handle .gitignore (one dot, no slash)."""
        response = (
            "### .gitignore\n"
            "```\n"
            "node_modules/\n"
            "```\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 1
        assert actions[0]['path'] == '.gitignore'

    def test_mixed_primary_and_fallback(self):
        """Primary WRITE + fallback $ command should both parse."""
        response = (
            "WRITE src/app.py\n"
            "```\n"
            "app = True\n"
            "```\n"
            "\n"
            "$ python src/app.py\n"
        )
        actions = _parse_actions(response)
        assert len(actions) == 2
        assert actions[0]['type'] == 'WRITE'
        assert actions[1]['type'] == 'RUN'


class TestBuildAgentPrompt:
    """Test _build_agent_prompt constructs prompts correctly."""

    def test_step_zero_includes_system_instructions_and_task(self):
        result = _build_agent_prompt("Do the task", [], 0)
        # System instructions come first
        assert result.startswith("You are an execution agent")
        # Task spec follows after separator
        assert "Do the task" in result
        assert "---" in result  # separator between instructions and task

    def test_step_one_includes_history_and_context(self):
        history = ["[OK] Wrote src/main.py (42 chars)"]
        result = _build_agent_prompt("Do the task", history, 1)
        assert "[OK] Wrote src/main.py" in result
        assert "Continue" in result
        # Must include task context (base prompt) for stateless LLM
        assert "Do the task" in result

    def test_history_capped_at_10(self):
        history = [f"[OK] Step {i}" for i in range(15)]
        result = _build_agent_prompt("Do the task", history, 1)
        # Should only include last 10
        assert "[OK] Step 5" in result
        assert "[OK] Step 14" in result
        assert "[OK] Step 4" not in result

    def test_full_prompt_preserved_on_later_steps(self):
        """Full prompt must be sent on every step — no truncation.
        OMS tasks are 3-4K chars; truncating loses spec/context/artifacts."""
        long_prompt = "x" * 5000
        result = _build_agent_prompt(long_prompt, ["[OK] step"], 1)
        # Full prompt preserved — no truncation
        assert "x" * 5000 in result
        assert "Continue" in result


class TestExtractPytestFailures:
    """Test _extract_pytest_failures with various pytest output formats."""

    def test_extracts_failures_section(self):
        raw = (
            "collected 5 items\n"
            "tests/test_foo.py ..F..\n\n"
            "================================= FAILURES =================================\n"
            "________________________________ test_bar __________________________________\n"
            "    def test_bar():\n"
            ">       assert 1 == 2\n"
            "E       AssertionError: assert 1 == 2\n"
            "tests/test_foo.py:10: AssertionError\n"
            "========================= short test summary info ==========================\n"
            "FAILED tests/test_foo.py::test_bar\n"
            "======================== 1 failed, 4 passed in 0.5s ========================\n"
        )
        result = _extract_pytest_failures(raw)
        assert 'FAILURES' in result
        assert 'assert 1 == 2' in result
        # Should NOT include the short test summary
        assert 'short test summary' not in result

    def test_extracts_assertion_error_lines(self):
        raw = (
            "tests/test_foo.py:10: in test_bar\n"
            "    result = compute()\n"
            ">       assert result == 42\n"
            "E       AssertionError: assert 7 == 42\n"
            "some trailing output\n"
        )
        result = _extract_pytest_failures(raw)
        assert 'assert result == 42' in result
        assert 'assert 7 == 42' in result

    def test_handles_collection_error(self):
        raw = (
            "================================= ERRORS =================================\n"
            "ERROR collecting tests/test_foo.py\n"
            "ModuleNotFoundError: No module named 'missing_dep'\n"
        )
        result = _extract_pytest_failures(raw)
        assert 'ERROR' in result

    def test_fallback_tail_truncation(self):
        raw = "line1\nline2\nline3\nlast line with the actual error"
        result = _extract_pytest_failures(raw, max_chars=50)
        assert 'last line with the actual error' in result

    def test_respects_max_chars(self):
        raw = (
            "= FAILURES =\n"
            + "x" * 5000
            + "\n= short test summary =\n"
        )
        result = _extract_pytest_failures(raw, max_chars=100)
        assert len(result) <= 100

    def test_empty_input(self):
        assert _extract_pytest_failures('') == ''


class TestExtractTestFailuresMultiRunner:
    """Test _extract_test_failures with vitest, jest, tsc, eslint, playwright output."""

    def test_vitest_failure(self):
        raw = (
            " ✓ tests/auth.test.ts (3)\n"
            " FAIL  tests/checkout.test.ts > describe > completes purchase\n"
            "   AssertionError: expected 'pending' to be 'completed'\n"
            "   ❯ tests/checkout.test.ts:15:3\n\n"
            " Test Files  1 failed | 1 passed (2)\n"
            " Tests  1 failed | 3 passed (4)\n"
        )
        result = _extract_test_failures(raw)
        assert 'FAIL' in result
        assert 'pending' in result or 'checkout' in result

    def test_jest_failure(self):
        raw = (
            " FAIL  tests/auth.test.ts\n"
            "  ● describe › returns error on invalid token\n\n"
            "    expect(received).toBe(expected)\n\n"
            "    Expected: 401\n"
            "    Received: 200\n\n"
            "      at Object.<anonymous> (tests/auth.test.ts:25:18)\n\n"
            "Test Suites: 1 failed, 1 total\n"
            "Tests:       1 failed, 2 passed, 3 total\n"
        )
        result = _extract_test_failures(raw)
        assert 'FAIL' in result
        assert 'toBe' in result or 'Expected: 401' in result

    def test_tsc_errors(self):
        raw = (
            "src/api/handler.ts(15,3): error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'.\n"
            "src/api/handler.ts(28,10): error TS2339: Property 'foo' does not exist on type 'Bar'.\n"
            "Found 2 errors in 1 file.\n"
        )
        result = _extract_test_failures(raw)
        assert 'error TS2345' in result
        assert 'error TS2339' in result

    def test_eslint_errors(self):
        raw = (
            "/Users/dev/src/api/handler.ts\n"
            "  15:3  error  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any\n"
            "  28:1  error  Missing return type on function            @typescript-eslint/explicit-function-return-type\n\n"
            "✖ 2 problems (2 errors, 0 warnings)\n"
        )
        result = _extract_test_failures(raw)
        assert 'error' in result
        assert 'Unexpected any' in result or 'no-explicit-any' in result

    def test_playwright_failure(self):
        raw = (
            "  1) [chromium] › tests/checkout.spec.ts:10:5 › completes purchase ──────\n\n"
            "    Error: expect(received).toHaveText(expected)\n\n"
            "    Expected string: \"Order confirmed\"\n"
            "    Received string: \"Error processing\"\n\n"
            "      at tests/checkout.spec.ts:15:20\n\n"
            "  1 failed\n"
            "  [chromium] › tests/checkout.spec.ts:10:5 › completes purchase ──────\n"
        )
        result = _extract_test_failures(raw)
        assert 'Error: expect(' in result or 'toHaveText' in result

    def test_backwards_compat_alias(self):
        """_extract_pytest_failures is an alias for _extract_test_failures."""
        raw = "= FAILURES =\nassert 1 == 2\n========"
        assert _extract_pytest_failures(raw) == _extract_test_failures(raw)


class TestParseScenarios:
    """Test _parse_scenarios with various BDD formats."""

    def test_basic_given_when_then(self):
        result = _parse_scenarios(['GIVEN a user is logged in WHEN they click logout THEN they are redirected to login'])
        assert len(result) == 1
        assert result[0]['given'] == 'a user is logged in'
        assert result[0]['when'] == 'they click logout'
        assert result[0]['then'] == 'they are redirected to login'

    def test_multiple_scenarios(self):
        scenarios = [
            'GIVEN a cart with items WHEN user clicks checkout THEN order is created',
            'GIVEN an empty cart WHEN user clicks checkout THEN error is shown',
            'GIVEN a cart WHEN payment fails THEN cart is preserved',
        ]
        result = _parse_scenarios(scenarios)
        assert len(result) == 3

    def test_handles_malformed(self):
        result = _parse_scenarios(['this is not a BDD scenario', 'just random text'])
        assert len(result) == 0

    def test_case_insensitive(self):
        result = _parse_scenarios(['given X when Y then Z'])
        assert len(result) == 1
        assert result[0]['given'] == 'X'


class TestScenarioCoverage:
    """Test _check_scenario_coverage fuzzy matching."""

    def test_all_covered(self, tmp_path):
        scenarios = [
            {'given': 'user is logged in', 'when': 'click logout', 'then': 'redirected to login', 'raw': '...'},
        ]
        test_file = tmp_path / 'test_auth.py'
        test_file.write_text('def test_logout():\n    # user logged in, click logout button\n    assert redirect == "/login"\n')
        ok, gaps = _check_scenario_coverage(scenarios, [test_file])
        assert ok is True
        assert len(gaps) == 0

    def test_one_missing(self, tmp_path):
        scenarios = [
            {'given': 'user logged in', 'when': 'click logout', 'then': 'redirect login', 'raw': 'sc1'},
            {'given': 'admin panel', 'when': 'delete account', 'then': 'account removed', 'raw': 'sc2'},
        ]
        test_file = tmp_path / 'test_auth.py'
        test_file.write_text('def test_logout():\n    # user logged in, logout\n    assert True\n')
        ok, gaps = _check_scenario_coverage(scenarios, [test_file])
        assert ok is False
        assert len(gaps) == 1
        assert 'Scenario 2' in gaps[0]

    def test_fuzzy_match(self, tmp_path):
        scenarios = [
            {'given': 'the config file exists', 'when': 'app starts', 'then': 'config is loaded', 'raw': '...'},
        ]
        test_file = tmp_path / 'test_config.py'
        test_file.write_text('def test_config_loading():\n    # config file read on startup\n    assert loaded\n')
        ok, gaps = _check_scenario_coverage(scenarios, [test_file])
        assert ok is True

    def test_no_test_files(self):
        scenarios = [{'given': 'x', 'when': 'y', 'then': 'z', 'raw': '...'}]
        ok, gaps = _check_scenario_coverage(scenarios, [])
        assert ok is False
        assert 'no test files' in gaps[0]


class TestParseQaVerdicts:
    """Test _parse_qa_verdicts per-scenario verdict parsing."""

    def test_all_scenarios_present(self):
        output = (
            "Scenario 1: PASS — login form renders correctly\n"
            "Scenario 2: PASS — error shown on invalid credentials\n"
            "Scenario 3: PASS — redirect after successful login\n"
            "PASS — all 3 scenarios verified"
        )
        ok, reason = _parse_qa_verdicts(output, 3)
        assert ok is True
        assert 'all 3' in reason

    def test_missing_scenarios(self):
        output = (
            "Scenario 1: PASS — login works\n"
            "Scenario 2: FAIL — no error handling\n"
            "FAIL — scenario 2 failed"
        )
        ok, reason = _parse_qa_verdicts(output, 3)
        assert ok is False
        assert '2/3' in reason

    def test_mixed_pass_fail_all_addressed(self):
        output = (
            "Scenario 1: PASS — good\n"
            "Scenario 2: FAIL — missing\n"
            "Scenario 3: PASS — good\n"
            "FAIL — scenario 2 failed"
        )
        ok, reason = _parse_qa_verdicts(output, 3)
        assert ok is True  # all 3 addressed even though one failed

    def test_empty_output(self):
        ok, reason = _parse_qa_verdicts('', 3)
        assert ok is False
        assert '0/3' in reason

    def test_case_insensitive(self):
        output = "scenario 1: pass — ok\nscenario 2: fail — bad\n"
        ok, reason = _parse_qa_verdicts(output, 2)
        assert ok is True


class TestFormatErrorFeedback:
    """Test _format_error_feedback produces structured retry prompts."""

    def test_test_phase(self):
        result = _format_error_feedback('assert 1 == 2', 'test')
        assert 'What failed' in result
        assert 'assert 1 == 2' in result
        assert 'TEST files' in result
        assert 'from scratch' in result

    def test_impl_phase(self):
        result = _format_error_feedback('NameError: foo', 'impl')
        assert 'IMPLEMENTATION' in result
        assert 'NameError: foo' in result

    def test_all_phase(self):
        result = _format_error_feedback('multiple issues', 'all')
        assert 'ALL issues' in result


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
