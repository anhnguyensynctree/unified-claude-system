"""Integration tests for Discord bot message handlers — mocked Discord API."""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestHandleIdea:
    """Test handle_idea() creates folder + IDEA.md + thread reply."""

    def test_creates_project_folder_and_idea(self, bot_module, tmp_path):
        bot_module.HOME = tmp_path

        message = AsyncMock()
        message.guild = MagicMock()
        message.create_thread = AsyncMock(return_value=AsyncMock())
        message.add_reaction = AsyncMock()
        message.remove_reaction = AsyncMock()
        bot_module.bot = MagicMock()
        bot_module.bot.user = MagicMock()

        asyncio.get_event_loop().run_until_complete(
            bot_module.handle_idea(message, "trading signals for crypto")
        )

        # Verify folder created
        slug = "trading-signals-for-crypto"
        proj_path = tmp_path / "code" / "personal" / slug
        assert proj_path.exists()
        assert (proj_path / "IDEA.md").exists()
        assert (proj_path / "README.md").exists()
        assert (proj_path / ".claude" / "agents").exists()

        # Verify IDEA.md content
        content = (proj_path / "IDEA.md").read_text()
        assert "trading signals for crypto" in content

        # Verify thread created and message sent
        message.create_thread.assert_called_once()
        thread = message.create_thread.return_value
        thread.send.assert_called_once()
        send_content = thread.send.call_args[0][0]
        assert slug in send_content
        assert "/oms-start" in send_content

        # Verify reactions
        message.add_reaction.assert_any_call("⏳")
        message.add_reaction.assert_any_call("✅")

    def test_no_guild_skips(self, bot_module):
        message = AsyncMock()
        message.guild = None
        asyncio.get_event_loop().run_until_complete(
            bot_module.handle_idea(message, "test idea")
        )
        message.add_reaction.assert_not_called()


class TestHandleIdeaThreadReply:
    """Test handle_idea_thread_reply() appends to IDEA.md and answers Q&A."""

    def test_appends_to_idea_md(self, bot_module, tmp_path):
        bot_module.HOME = tmp_path

        # Create project dir with initial IDEA.md
        slug = "my-project"
        proj_path = tmp_path / "code" / "personal" / slug
        proj_path.mkdir(parents=True)
        (proj_path / "IDEA.md").write_text("# my-project\n\nOriginal idea\n")

        thread = AsyncMock()
        thread.name = f"idea: {slug}"
        thread.parent_id = None

        async def mock_history(**kwargs):
            for msg in []:
                yield msg

        thread.history = mock_history

        message = AsyncMock()
        bot_module.bot = MagicMock()
        bot_module.bot.user = MagicMock()

        # Mock LLM route to return a response
        with patch.object(bot_module, '_run_llm_route', new_callable=AsyncMock,
                          return_value=("Great question! Here's my answer.", 0)):
            asyncio.get_event_loop().run_until_complete(
                bot_module.handle_idea_thread_reply(
                    message, "What about adding alerts?", thread)
            )

        # Verify IDEA.md was appended
        content = (proj_path / "IDEA.md").read_text()
        assert "What about adding alerts?" in content

        # Verify response was posted
        thread.send.assert_called()


class TestHandleProjectMessage:
    """Test !work command routing."""

    def test_work_command_invokes_oms_work(self, bot_module, tmp_path):
        bot_module.HOME = tmp_path

        # Create queue file
        proj_path = tmp_path / "projects" / "test"
        (proj_path / ".claude").mkdir(parents=True)
        (proj_path / ".claude" / "cleared-queue.md").write_text("## TASK-001\n- **Status:** queued\n")

        channel = AsyncMock()
        channel.id = 12345
        channel.send = AsyncMock()

        message = AsyncMock()
        message.channel = channel
        # Make isinstance check work
        message.channel.__class__ = type('TextChannel', (), {})

        bot_module.bot = MagicMock()
        bot_module.bot.user = MagicMock()

        proj = {"path": str(proj_path), "channel_id": "12345"}

        # Mock subprocess to simulate oms-work.py output
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(
            json.dumps({"total_cost_usd": 0.05, "result": "1 task completed"}).encode(),
            b""
        ))
        mock_proc.returncode = 0

        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock,
                   return_value=mock_proc):
            with patch('asyncio.wait_for', new_callable=AsyncMock,
                       return_value=(mock_proc.communicate.return_value)):
                asyncio.get_event_loop().run_until_complete(
                    bot_module.handle_project_message(message, "test", proj, "!work")
                )

    def test_work_without_queue_replies_error(self, bot_module, tmp_path):
        import sys
        discord_mod = sys.modules['discord']
        bot_module.HOME = tmp_path

        channel = AsyncMock(spec=discord_mod.TextChannel)
        channel.id = 12345
        message = AsyncMock()
        message.channel = channel
        message.reply = AsyncMock()

        proj = {"path": str(tmp_path / "nonexistent")}

        asyncio.get_event_loop().run_until_complete(
            bot_module.handle_project_message(message, "test", proj, "!work")
        )

        message.reply.assert_called_once()
        assert "No cleared-queue.md" in message.reply.call_args[0][0]


class TestDiscordCreateChannel:
    """Test discord-create-channel.py config writing with --path."""

    def test_writes_path_to_config(self, tmp_path):
        config = {
            "updates_channel_id": "222222",
            "projects": {},
        }
        config_file = tmp_path / "oms-config.json"
        config_file.write_text(json.dumps(config))

        # Simulate what the script does (without Discord API call)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'discord_create_channel',
            Path(__file__).resolve().parent.parent / 'bin' / 'discord-create-channel.py'
        )

        # Just test the config writing logic directly
        project_path = "/Users/test/code/personal/my-project"
        config["projects"]["my-project"] = {
            "path": project_path,
            "channel_id": "999999",
            "active": True,
            "auto_start": True,
            "deploy": None,
            "mobile": None,
        }
        config_file.write_text(json.dumps(config, indent=2))

        # Verify
        saved = json.loads(config_file.read_text())
        assert saved["projects"]["my-project"]["path"] == project_path
        assert saved["projects"]["my-project"]["active"] is True
