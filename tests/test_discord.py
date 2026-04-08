"""Unit tests for discord-bot.py pure functions — no Discord API needed."""
import json


class TestExtractSlug:
    def test_simple_line(self, bot_module):
        assert bot_module._extract_slug("My cool project idea") == "my-cool-project-idea"

    def test_first_line_only(self, bot_module):
        idea = "Trading bot\nThis is a long description that should be ignored"
        assert bot_module._extract_slug(idea) == "trading-bot"

    def test_markdown_header_stripped(self, bot_module):
        assert bot_module._extract_slug("# Some Project Name") == "some-project-name"

    def test_special_chars_removed(self, bot_module):
        assert bot_module._extract_slug("Hello, world! (v2)") == "hello-world-v2"

    def test_max_five_words(self, bot_module):
        slug = bot_module._extract_slug("one two three four five six seven")
        words = slug.split('-')
        assert len(words) == 5

    def test_capped_at_40_chars(self, bot_module):
        slug = bot_module._extract_slug("a" * 100)
        assert len(slug) <= 40

    def test_empty_input_gets_timestamp(self, bot_module):
        slug = bot_module._extract_slug("")
        assert slug.startswith("project-")

    def test_whitespace_only(self, bot_module):
        slug = bot_module._extract_slug("   \n  \n  ")
        assert slug.startswith("project-")


class TestSplitForDiscord:
    def test_short_message_unchanged(self, bot_module):
        chunks = bot_module.split_for_discord("hello world")
        assert chunks == ["hello world"]

    def test_splits_at_paragraph(self, bot_module):
        text = "a" * 1000 + "\n\n" + "b" * 500
        chunks = bot_module.split_for_discord(text, limit=1500)
        assert len(chunks) == 2

    def test_splits_at_sentence(self, bot_module):
        text = "A" * 1800 + ". B" * 100
        chunks = bot_module.split_for_discord(text, limit=1900)
        assert len(chunks) >= 2

    def test_never_exceeds_limit(self, bot_module):
        text = "word " * 1000
        chunks = bot_module.split_for_discord(text, limit=100)
        for chunk in chunks:
            assert len(chunk) <= 100


class TestFormatStepUpdate:
    def test_extracts_oms_update(self, bot_module):
        output = "some stuff\n## OMS Update\nTask completed successfully\nmore stuff"
        result = bot_module.format_step_update(output)
        assert "Task completed successfully" in result

    def test_fallback_to_last_line(self, bot_module):
        output = "line1\nline2\nfinal result here"
        result = bot_module.format_step_update(output)
        assert "final result here" in result

    def test_empty_input(self, bot_module):
        result = bot_module.format_step_update("")
        assert result == "Step complete"


class TestParseWorkOutput:
    def test_valid_json(self, bot_module):
        raw = json.dumps({"total_cost_usd": 0.05, "result": "3 tasks completed"})
        output, cost = bot_module._parse_work_output(raw, "test", "work")
        assert output == "3 tasks completed"
        assert cost == 0.05

    def test_invalid_json_passthrough(self, bot_module):
        raw = "plain text output"
        output, cost = bot_module._parse_work_output(raw, "test", "work")
        assert output == "plain text output"
        assert cost is None

    def test_json_without_cost(self, bot_module):
        raw = json.dumps({"result": "done"})
        output, cost = bot_module._parse_work_output(raw, "test", "work")
        assert output == "done"
        assert cost is None

    def test_json_with_content_field(self, bot_module):
        raw = json.dumps({"content": "fallback content"})
        output, _ = bot_module._parse_work_output(raw, "test", "work")
        assert output == "fallback content"


class TestIsRateLimited:
    def test_rate_limit_detected(self, bot_module):
        assert bot_module._is_rate_limited("Error: rate limit exceeded")

    def test_429_detected(self, bot_module):
        assert bot_module._is_rate_limited("HTTP 429 Too Many Requests")

    def test_overloaded_detected(self, bot_module):
        assert bot_module._is_rate_limited("API overloaded, retry later")

    def test_normal_error_not_flagged(self, bot_module):
        assert not bot_module._is_rate_limited("TypeError: undefined is not a function")


class TestGetProjectByChannel:
    def test_finds_project(self, bot_module):
        config = {"projects": {"myapp": {"channel_id": "12345", "path": "/tmp/myapp"}}}
        result = bot_module.get_project_by_channel(config, 12345)
        assert result is not None
        slug, proj = result
        assert slug == "myapp"
        assert proj["path"] == "/tmp/myapp"

    def test_returns_none_for_unknown(self, bot_module):
        config = {"projects": {"myapp": {"channel_id": "12345"}}}
        assert bot_module.get_project_by_channel(config, 99999) is None

    def test_string_channel_id_match(self, bot_module):
        config = {"projects": {"myapp": {"channel_id": "12345"}}}
        result = bot_module.get_project_by_channel(config, "12345")
        assert result is not None


class TestGetProjectByThread:
    def test_finds_project_by_parent(self, bot_module, discord_mock):
        config = {"projects": {"myapp": {"channel_id": "12345"}}}
        thread = type('MockThread', (), {'parent_id': 12345})()
        result = bot_module.get_project_by_thread(config, thread)
        assert result is not None
        assert result[0] == "myapp"

    def test_returns_none_for_no_parent(self, bot_module, discord_mock):
        config = {"projects": {"myapp": {"channel_id": "12345"}}}
        thread = type('MockThread', (), {'parent_id': None})()
        assert bot_module.get_project_by_thread(config, thread) is None
