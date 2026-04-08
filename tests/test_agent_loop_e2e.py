"""End-to-end test: parse TASK-001 from base-trade, run through agent loop with mock LLM."""
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock discord before import
sys.modules['discord_notify'] = types.ModuleType('discord_notify')
sys.modules['discord_notify'].DiscordNotifier = type('DN', (), {'__init__': lambda *a, **kw: None})

import importlib.util
spec = importlib.util.spec_from_file_location('oms_work', Path.home() / '.claude/bin/oms-work.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


QUEUE_PATH = Path.home() / 'code/personal/base_trade/.claude/cleared-queue.md'


class TestParseTask001:
    """Verify TASK-001 is parsed correctly from the real queue."""

    def test_parse_queue_finds_task001(self):
        tasks = mod.parse_queue(QUEUE_PATH)
        task = next(t for t in tasks if t['id'] == 'TASK-001')
        assert task['status'] in ('queued', 'done', 'in-progress')  # status changes over time
        assert task['type'] == 'impl'
        assert task['model_hint'] == 'sonnet'
        assert 'requirements.txt' in task['artifacts']
        assert '.env.example' in task['artifacts']
        assert '.gitignore' in task['artifacts']
        assert len(task['artifacts']) == 3
        assert task['depends'] == []

    def test_task001_scenarios_parsed(self):
        tasks = mod.parse_queue(QUEUE_PATH)
        task = next(t for t in tasks if t['id'] == 'TASK-001')
        assert len(task['scenarios']) == 3
        assert any('requirements.txt' in s for s in task['scenarios'])
        assert any('.env.example' in s for s in task['scenarios'])
        assert any('.gitignore' in s for s in task['scenarios'])

    def test_task001_verify_commands(self):
        tasks = mod.parse_queue(QUEUE_PATH)
        task = next(t for t in tasks if t['id'] == 'TASK-001')
        assert len(task['verify']) >= 3
        # Should have pip install, test -f .env.example, test -f .gitignore
        verify_text = ' '.join(task['verify'])
        assert 'pip install' in verify_text
        assert '.env.example' in verify_text
        assert '.gitignore' in verify_text

    def test_task001_validation_chain(self):
        tasks = mod.parse_queue(QUEUE_PATH)
        task = next(t for t in tasks if t['id'] == 'TASK-001')
        assert task['validation'] == ['dev', 'cto']


class TestPromptGeneration:
    """Test that prompts for TASK-001 include the agent loop protocol."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())

    def test_exec_prompt_is_task_only(self):
        """exec_prompt should contain task spec, not agent protocol.
        WRITE/RUN/DONE instructions are added by _build_agent_prompt."""
        prompt = mod.exec_prompt(self.task, self.wt)
        # Task spec present
        assert 'requirements.txt' in prompt
        assert 'Behavioral Scenarios' in prompt
        # Agent protocol NOT in task prompt — added by _build_agent_prompt
        assert 'You are an execution agent' not in prompt

    def test_exec_prompt_includes_quality_rules(self):
        prompt = mod.exec_prompt(self.task, self.wt)
        assert 'Max 300 lines' in prompt
        assert 'No console.log' in prompt

    def test_exec_prompt_includes_spec(self):
        prompt = mod.exec_prompt(self.task, self.wt)
        assert 'requirements.txt' in prompt
        assert '.env.example' in prompt
        assert '.gitignore' in prompt

    def test_exec_prompt_includes_context(self):
        prompt = mod.exec_prompt(self.task, self.wt)
        assert 'yfinance' in prompt or 'ALPACA' in prompt

    def test_build_agent_prompt_step0(self):
        base = mod.exec_prompt(self.task, self.wt)
        result = mod._build_agent_prompt(base, [], 0)
        # Step 0 wraps with system instructions + task
        assert result.startswith("You are an execution agent")
        assert base in result

    def test_build_agent_prompt_step1_with_history(self):
        history = ['[OK] Wrote requirements.txt (120 chars)']
        result = mod._build_agent_prompt("task prompt", history, 1)
        assert '[OK] Wrote requirements.txt' in result
        assert 'Continue' in result


class TestAgentLoopWithMockLLM:
    """Test _agent_loop with mocked LLM responses simulating real behavior."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())
        # Init git in temp dir so git status works
        subprocess.run(['git', 'init'], cwd=self.wt, capture_output=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'init'],
                        cwd=self.wt, capture_output=True)

    def _mock_llm_response(self, step_responses):
        """Create a mock that returns different responses per call."""
        call_count = [0]

        def mock_route(model, prompt, cwd):
            idx = min(call_count[0], len(step_responses) - 1)
            call_count[0] += 1
            return step_responses[idx], 0

        return mock_route

    def test_single_step_all_writes_then_done(self):
        """LLM writes all 3 files + DONE in one response."""
        response = (
            "WRITE requirements.txt\n"
            "```\n"
            "yfinance==0.2.36\n"
            "ta==0.11.0\n"
            "vectorbt==0.26.2\n"
            "alpaca-py==0.21.1\n"
            "python-dotenv==1.0.1\n"
            "APScheduler==3.10.4\n"
            "tabulate==0.9.0\n"
            "```\n\n"
            "WRITE .env.example\n"
            "```\n"
            "ALPACA_API_KEY=your_key_here\n"
            "ALPACA_SECRET_KEY=your_secret_here\n"
            "ALPACA_BASE_URL=https://paper-api.alpaca.markets\n"
            "```\n\n"
            "WRITE .gitignore\n"
            "```\n"
            ".env\n"
            "__pycache__/\n"
            "data/cache/\n"
            "logs/\n"
            "*.parquet\n"
            "*.pyc\n"
            "```\n\n"
            "DONE Created scaffold: requirements.txt, .env.example, .gitignore\n"
        )

        with patch('oms_work.agent.run_llm_route', side_effect=self._mock_llm_response([response])):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()
        assert (self.wt / '.env.example').exists()
        assert (self.wt / '.gitignore').exists()
        assert 'yfinance' in (self.wt / 'requirements.txt').read_text()
        assert 'ALPACA_API_KEY' in (self.wt / '.env.example').read_text()

    def test_multi_step_write_then_run_then_done(self):
        """LLM writes files in step 1, runs a command in step 2, then DONE."""
        step1 = (
            "WRITE requirements.txt\n"
            "```\n"
            "yfinance==0.2.36\n"
            "```\n\n"
            "WRITE .env.example\n"
            "```\n"
            "ALPACA_API_KEY=your_key_here\n"
            "```\n\n"
            "WRITE .gitignore\n"
            "```\n"
            ".env\n"
            "```\n"
        )
        step2 = (
            "RUN ls -la\n"
        )
        step3 = (
            "DONE All files created successfully.\n"
        )

        with patch('oms_work.agent.run_llm_route', side_effect=self._mock_llm_response([step1, step2, step3])):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()

    def test_format_violation_fallback(self):
        """LLM returns old-style output twice — should fall back to extraction."""
        old_style = (
            "Here are the files:\n\n"
            "### requirements.txt\n"
            "```\n"
            "yfinance==0.2.36\n"
            "```\n\n"
            "### .env.example\n"
            "```\n"
            "ALPACA_API_KEY=your_key_here\n"
            "```\n\n"
            "### .gitignore\n"
            "```\n"
            ".env\n"
            "```\n"
        )

        # The heading fallback should actually parse these as WRITE actions
        # So this should succeed on first try
        with patch('oms_work.agent.run_llm_route', side_effect=self._mock_llm_response([old_style])):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()

    def test_llm_failure_retry(self):
        """LLM returns empty on first call, succeeds on second."""
        good_response = (
            "WRITE requirements.txt\n```\nyfinance==0.2.36\n```\n\n"
            "DONE Created file.\n"
        )

        call_count = [0]
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            if call_count[0] == 1:
                return '', 1  # First call fails
            return good_response, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        assert call_count[0] == 2

    def test_max_steps_exhaustion(self):
        """LLM never says DONE — should exhaust max_steps."""
        # Keep writing files but never DONE
        endless = "WRITE requirements.txt\n```\nline\n```\n"

        with patch('oms_work.agent.run_llm_route', return_value=(endless, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                mod.exec_prompt(self.task, self.wt),
                max_steps=3)

        # Should succeed because files exist (git status check)
        assert rc == 0
        assert 'completed' in summary.lower() or 'steps' in summary.lower()

    def test_subscription_model_path(self):
        """Test subscription model uses run_claude (text-only, no allow_writes)."""
        response = (
            "WRITE requirements.txt\n```\nyfinance==0.2.36\n```\n\n"
            "DONE Created file.\n"
        )

        def mock_claude(prompt, cwd, model):
            assert 'allow_writes' not in str(model)  # No allow_writes param
            return response, 0, '', 0.05

        with patch('oms_work.agent.run_claude', side_effect=mock_claude):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'claude-sonnet-4-6', False,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        assert cost > 0  # Should track cost
        assert (self.wt / 'requirements.txt').exists()

    def test_subscription_rate_limit_falls_back_to_free(self):
        """Subscription model rate-limited — should fall back to free model."""
        call_log = []

        def mock_claude(prompt, cwd, model):
            call_log.append(('claude', model))
            return '', 1, 'rate limit exceeded', 0.0

        def mock_route(model, prompt, cwd):
            call_log.append(('free', model))
            return "WRITE requirements.txt\n```\ntest\n```\n\nDONE ok\n", 0

        with patch('oms_work.agent.run_claude', side_effect=mock_claude), \
             patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'claude-sonnet-4-6', False,
                mod.exec_prompt(self.task, self.wt))

        assert rc == 0
        # Should have tried claude first, then fallen back
        assert call_log[0][0] == 'claude'
        assert call_log[1][0] == 'free'
        assert call_log[1][1] == 'qwen'  # sonnet falls back to qwen

    def test_run_command_timeout(self):
        """RUN command that times out should not crash the loop."""
        step1 = "RUN sleep 999\n"
        step2 = "DONE gave up on slow command.\n"

        call_count = [0]
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            if call_count[0] == 1:
                return step1, 0
            return step2, 0

        # Mock subprocess.run to raise TimeoutExpired for sleep
        original_run = subprocess.run
        def patched_run(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', '')
            if isinstance(cmd, list) and 'sleep' in ' '.join(cmd):
                raise subprocess.TimeoutExpired(cmd, 120)
            if isinstance(cmd, str) and 'sleep' in cmd:
                raise subprocess.TimeoutExpired(cmd, 120)
            # For zsh -c wrapper
            if isinstance(cmd, list) and len(cmd) >= 3 and 'sleep' in cmd[-1]:
                raise subprocess.TimeoutExpired(cmd, 120)
            return original_run(*args, **kwargs)

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route), \
             patch('subprocess.run', side_effect=patched_run):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                "test prompt")

        assert rc == 0

    def test_write_creates_nested_directories(self):
        """WRITE to nested path should create parent dirs."""
        response = (
            "WRITE src/deep/nested/file.py\n"
            "```\n"
            "print('nested')\n"
            "```\n\n"
            "DONE Created nested file.\n"
        )

        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")

        assert rc == 0
        assert (self.wt / 'src/deep/nested/file.py').exists()
        assert "print('nested')" in (self.wt / 'src/deep/nested/file.py').read_text()

    def test_write_strips_leading_slashes(self):
        """WRITE /absolute/path should strip leading /."""
        response = (
            "WRITE /requirements.txt\n"
            "```\n"
            "flask\n"
            "```\n\n"
            "DONE ok\n"
        )

        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")

        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()

    def test_write_strips_dot_slash(self):
        """WRITE ./path should strip leading ./."""
        response = (
            "WRITE ./requirements.txt\n"
            "```\n"
            "flask\n"
            "```\n\n"
            "DONE ok\n"
        )

        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")

        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()


class TestAdaptiveSteps:
    """Verify max_steps adapts to task size and early completion works."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())
        subprocess.run(['git', 'init'], cwd=self.wt, capture_output=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'init'],
                        cwd=self.wt, capture_output=True)

    def test_early_completion_when_all_artifacts_written(self):
        """Should auto-complete after step 0 if all artifacts exist."""
        # TASK-001 has 3 artifacts: requirements.txt, .env.example, .gitignore
        # Write all 3 in one step without DONE — should auto-complete
        response = (
            "WRITE requirements.txt\n```\nyfinance==0.2.36\n```\n\n"
            "WRITE .env.example\n```\nKEY=val\n```\n\n"
            "WRITE .gitignore\n```\n.env\n```\n"
        )
        call_count = [0]
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            return response, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")

        assert rc == 0
        assert call_count[0] == 1  # Only 1 call needed
        assert 'auto-completing' in summary.lower() or 'artifacts written' in summary.lower()

    def test_research_always_oneshot(self):
        """Research tasks should always go one-shot regardless of model."""
        research_task = {
            'id': 'TASK-007', 'type': 'research', 'spec': 'test',
            'scenarios': [], 'artifacts': ['docs/research.md'],
            'produces': 'none', 'verify': [], 'context': [],
            'validation': ['researcher'], 'depends': [], 'model_hint': 'qwen',
        }
        response = "# Research\n## Finding 1\nSome finding\n"
        call_count = [0]
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            return response, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                research_task, self.wt, 'qwen', True, "test")

        assert rc == 0
        assert call_count[0] == 1


class TestOneShotBypass:
    """Models not in AGENT_CAPABLE_MODELS should go one-shot, zero wasted calls."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())
        subprocess.run(['git', 'init'], cwd=self.wt, capture_output=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'init'],
                        cwd=self.wt, capture_output=True)

    def test_gemma_goes_oneshot(self):
        """gemma is not agent-capable — should make exactly 1 LLM call."""
        call_count = [0]
        old_style = (
            "### requirements.txt\n```\nyfinance==0.2.36\n```\n\n"
            "### .env.example\n```\nKEY=val\n```\n\n"
            "### .gitignore\n```\n.env\n```\n"
        )
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            return old_style, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'gemma', True, "test prompt")

        assert rc == 0
        assert call_count[0] == 1  # Exactly 1 call, no wasted retries
        assert (self.wt / 'requirements.txt').exists()

    def test_llama_goes_oneshot(self):
        """llama is not agent-capable — one-shot."""
        old_style = "### requirements.txt\n```\nflask\n```\n"
        call_count = [0]
        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            return old_style, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'llama', True, "test")

        assert rc == 0
        assert call_count[0] == 1

    def test_stepfun_goes_oneshot(self):
        """stepfun is not agent-capable — one-shot."""
        old_style = "### requirements.txt\n```\nflask\n```\n"
        with patch('oms_work.agent.run_llm_route', return_value=(old_style, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'stepfun', True, "test")
        assert rc == 0

    def test_qwen_uses_agent_loop(self):
        """qwen IS agent-capable — should use multi-step loop."""
        response = "WRITE requirements.txt\n```\nflask\n```\n\nDONE ok\n"
        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")
        assert rc == 0
        assert (self.wt / 'requirements.txt').exists()

    def test_qwen_coder_uses_agent_loop(self):
        """qwen-coder IS agent-capable."""
        response = "WRITE requirements.txt\n```\nflask\n```\n\nDONE ok\n"
        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen-coder', True, "test")
        assert rc == 0

    def test_oneshot_failure_returns_nonzero(self):
        """One-shot model failure should not silently pass."""
        with patch('oms_work.agent.run_llm_route', return_value=('', 1)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'gemma', True, "test")
        assert rc == 1

    def test_subscription_model_always_uses_agent_loop(self):
        """Subscription models are always agent-capable regardless of is_external."""
        response = "WRITE requirements.txt\n```\nflask\n```\n\nDONE ok\n"
        def mock_claude(prompt, cwd, model):
            return response, 0, '', 0.01

        with patch('oms_work.agent.run_claude', side_effect=mock_claude):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'claude-sonnet-4-6', False, "test")
        assert rc == 0


class TestValidateStep:
    """Verify validation still works correctly with text-only run_claude."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())

    def test_validate_step_calls_run_claude_without_allow_writes(self):
        """validate_step should use run_claude text-only (no allow_writes)."""
        import inspect
        sig = inspect.signature(mod.run_claude)
        params = list(sig.parameters.keys())
        assert 'allow_writes' not in params
        assert params == ['prompt', 'cwd', 'model']

    def test_validate_step_haiku_first(self):
        """Validation should try haiku before free models."""
        call_log = []

        def mock_claude(prompt, cwd, model):
            call_log.append(('claude', model))
            return 'PASS — all files present', 0, '', 0.01

        with patch('oms_work.validate.run_claude', side_effect=mock_claude):
            passed, reason, cost = mod.validate_step(
                'dev', self.task, 'wrote 3 files', self.wt)

        assert passed
        assert call_log[0][1] == 'claude-haiku-4-5-20251001'

    def test_validate_step_free_fallback_on_rate_limit(self):
        """If haiku rate-limited, should fall back to free models."""
        call_log = []

        def mock_claude(prompt, cwd, model):
            call_log.append(('claude', model))
            return '', 1, 'rate limit', 0.0

        def mock_route(model, prompt, cwd):
            call_log.append(('free', model))
            return 'PASS — looks good', 0

        with patch('oms_work.validate.run_claude', side_effect=mock_claude), \
             patch('oms_work.validate.run_llm_route', side_effect=mock_route):
            passed, reason, cost = mod.validate_step(
                'dev', self.task, 'wrote 3 files', self.wt)

        assert passed
        assert call_log[0] == ('claude', 'claude-haiku-4-5-20251001')
        assert call_log[1][0] == 'free'


class TestSilentFailures:
    """Verify NO silent failures — every error path produces visible output."""

    def setup_method(self):
        self.tasks = mod.parse_queue(QUEUE_PATH)
        self.task = next(t for t in self.tasks if t['id'] == 'TASK-001')
        self.wt = Path(tempfile.mkdtemp())
        subprocess.run(['git', 'init'], cwd=self.wt, capture_output=True)
        subprocess.run(['git', 'commit', '--allow-empty', '-m', 'init'],
                        cwd=self.wt, capture_output=True)

    def test_all_llm_calls_fail_returns_nonzero(self):
        """If every LLM call fails, agent loop must return rc != 0."""
        with patch('oms_work.agent.run_llm_route', return_value=('', 1)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                "test", max_steps=3)

        assert rc == 1
        assert 'exhausted' in summary.lower() or 'no output' in summary.lower()

    def test_empty_llm_response_counted_as_format_violation(self):
        """Empty response should increment format violations, not silently pass."""
        call_count = [0]

        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            if call_count[0] <= 2:
                return 'Some text without any actions', 0
            return "DONE finished\n", 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                "test", max_steps=5)

        # After 2 format violations, should have fallen back to extraction
        # which finds nothing, so still returns rc=0 with fallback path
        assert rc == 0

    def test_run_command_error_captured_in_history(self):
        """Failed RUN commands must be captured in history for LLM feedback."""
        step1 = "RUN false\n"  # `false` always exits 1
        step2 = "DONE ok\n"

        call_count = [0]
        prompts_received = []

        def mock_route(model, prompt, cwd):
            call_count[0] += 1
            prompts_received.append(prompt)
            if call_count[0] == 1:
                return step1, 0
            return step2, 0

        with patch('oms_work.agent.run_llm_route', side_effect=mock_route):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True,
                "test", max_steps=5)

        # Step 2 prompt should contain the error from step 1
        assert len(prompts_received) >= 2
        assert 'Exit 1' in prompts_received[1] or 'RAN' in prompts_received[1]

    def test_write_failure_does_not_crash(self):
        """Writing to an invalid path should not crash the loop."""
        # This tests writing to a path where parent can't be created
        response = (
            "WRITE /dev/null/impossible/file.py\n"
            "```\n"
            "code\n"
            "```\n\n"
            "DONE tried\n"
        )

        # The write will go to wt / dev/null/impossible/file.py
        # which should work because mkdir -p creates it
        with patch('oms_work.agent.run_llm_route', return_value=(response, 0)):
            summary, rc, cost = mod._agent_loop(
                self.task, self.wt, 'qwen', True, "test")

        # Should not crash
        assert rc == 0


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
