"""Shared fixtures for Discord integration tests."""
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Mock discord module before any bot imports ──────────────────────────────

def _create_discord_mock():
    """Build a mock discord module that satisfies all imports in discord-bot.py."""
    discord = types.ModuleType('discord')

    # Core classes
    discord.Intents = MagicMock()
    discord.Intents.default = MagicMock(return_value=MagicMock())
    discord.TextChannel = type('TextChannel', (), {})
    discord.Thread = type('Thread', (), {})
    discord.Message = type('Message', (), {})
    discord.Guild = type('Guild', (), {})
    discord.Client = MagicMock
    discord.utils = MagicMock()

    # discord.ext.commands
    ext = types.ModuleType('discord.ext')
    commands = types.ModuleType('discord.ext.commands')
    commands.Bot = MagicMock
    commands.bot = MagicMock()
    ext.commands = commands
    discord.ext = ext

    sys.modules['discord'] = discord
    sys.modules['discord.ext'] = ext
    sys.modules['discord.ext.commands'] = commands
    return discord


def _load_module(name: str, filename: str):
    """Load a module from bin/ by file path, avoiding import conflicts."""
    import importlib.util
    path = Path(__file__).resolve().parent.parent / 'bin' / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Install discord mock globally before any test imports
_discord_mock = _create_discord_mock()


@pytest.fixture
def discord_mock():
    return _discord_mock


@pytest.fixture
def bot_module():
    """Load discord-bot.py module with mocked discord."""
    return _load_module('discord_bot', 'discord-bot.py')


@pytest.fixture
def brief_module():
    """Load oms-brief.py module."""
    return _load_module('oms_brief', 'oms-brief.py')


@pytest.fixture
def discord_helper_module():
    """Load oms_discord.py module."""
    return _load_module('oms_discord_helper', 'oms_discord.py')


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary oms-config.json with test data."""
    config = {
        "ideas_channel_id": "111111",
        "updates_channel_id": "222222",
        "claude_channel_id": "333333",
        "projects_base_dir": str(tmp_path / "projects"),
        "projects": {
            "test-project": {
                "path": str(tmp_path / "projects" / "test-project"),
                "channel_id": "444444",
                "active": True,
                "auto_start": True,
                "deploy": None,
                "mobile": None,
            },
            "idle-project": {
                "path": str(tmp_path / "projects" / "idle-project"),
                "channel_id": "555555",
                "active": True,
                "deploy": None,
                "mobile": None,
            },
            "inactive": {
                "path": str(tmp_path / "projects" / "inactive"),
                "active": False,
            },
        },
    }
    config_file = tmp_path / "oms-config.json"
    config_file.write_text(json.dumps(config, indent=2))
    return config_file, config


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with .claude/ structure."""
    proj = tmp_path / "projects" / "test-project"
    proj.mkdir(parents=True)
    (proj / ".claude" / "agents").mkdir(parents=True)
    return proj


@pytest.fixture
def tmp_queue(tmp_project):
    """Create a cleared-queue.md with test task statuses."""
    queue = tmp_project / ".claude" / "cleared-queue.md"
    queue.write_text(
        "## TASK-001 — Setup auth\n"
        "- **Status:** done\n"
        "- **Cost:** $0.0100\n\n"
        "## TASK-002 — Add login page\n"
        "- **Status:** done\n"
        "- **Cost:** $0.0200\n\n"
        "## TASK-003 — Payment integration\n"
        "- **Status:** queued\n\n"
        "## TASK-004 — Fix redirect\n"
        "- **Status:** cto-stop\n\n"
    )
    return queue


@pytest.fixture
def tmp_costs(tmp_project):
    """Create oms-costs.json with test cost records."""
    costs = [
        {"task_id": "TASK-001", "cost_usd": 0.01, "passed": True,
         "first_pass": True, "validators": "dev✓ qa✓", "model_used": "qwen", "ts": "2026-04-06T10:00:00Z"},
        {"task_id": "TASK-002", "cost_usd": 0.02, "passed": True,
         "first_pass": False, "validators": "dev✓ qa↺✓", "model_used": "qwen", "ts": "2026-04-06T11:00:00Z"},
        {"task_id": "TASK-003", "cost_usd": 0.03, "passed": False,
         "first_pass": False, "validators": "dev✓ cto✗", "model_used": "haiku",
         "fail_at": "cto", "ts": "2026-04-06T12:00:00Z"},
    ]
    costs_file = tmp_project / ".claude" / "oms-costs.json"
    costs_file.write_text(json.dumps(costs, indent=2))
    return costs_file
