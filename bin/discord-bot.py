#!/usr/bin/env python3
"""
OMS Discord Bot — always-on bridge between Discord and oms-work.py
Runs as launchd daemon. Monitors project channels, routes messages to oms-work.

UX: one thread per task. Main channel = task feed (started / done).
Thread = all step updates + blocking questions + observer Q&A.
"""

import asyncio
import json
import logging
import re
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands

# --- Config ---
HOME = Path.home()
CONFIG_FILE = HOME / ".claude/oms-config.json"
TOKEN_FILE = HOME / ".config/discord/token"
LOG_DIR = HOME / ".claude/logs"
PENDING_DIR = HOME / ".claude/oms-pending"
PENDING_RESUMES_FILE = HOME / ".claude/oms-pending-resumes.json"
BUDGET_FILE = HOME / ".claude/oms-budget.json"
LLM_ROUTE = HOME / ".claude/bin/llm-route.sh"

LOG_DIR.mkdir(parents=True, exist_ok=True)
PENDING_DIR.mkdir(parents=True, exist_ok=True)

_root = logging.getLogger()
if not _root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Note: FileHandler omitted — launchd StandardOutPath already captures stdout to log file
        ],
    )
log = logging.getLogger("oms-bot")


# --- Thread registry: "slug:task_id" → discord.Thread ---
task_threads: dict[str, discord.Thread] = {}
_first_ready = True  # suppress repeated "bot online" on Discord gateway reconnects
_config_cache: dict = {}           # cached config — reloaded only when file changes
_config_mtime: float = 0.0
_processed_messages: set[int] = set()  # dedup: message IDs already handled


def load_config() -> dict:
    """Load config, using mtime cache to avoid disk reads on every poll tick."""
    global _config_cache, _config_mtime
    if not CONFIG_FILE.exists():
        log.error("oms-config.json not found — run /init-oms in Claude Code")
        sys.exit(1)
    mtime = CONFIG_FILE.stat().st_mtime
    if mtime != _config_mtime:
        _config_cache = json.loads(CONFIG_FILE.read_text())
        _config_mtime = mtime
    return _config_cache


def get_project_by_channel(config: dict, channel_id: int) -> tuple[str, dict] | None:
    for slug, proj in config.get("projects", {}).items():
        if str(proj.get("channel_id", "")) == str(channel_id):
            return slug, proj
    return None


def get_project_by_thread(config: dict, thread: discord.Thread) -> tuple[str, dict] | None:
    """Find project whose channel is the parent of this thread."""
    parent_id = thread.parent_id
    if parent_id is None:
        return None
    return get_project_by_channel(config, parent_id)


def is_blocking_question_pending(project_slug: str) -> bool:
    return (PENDING_DIR / f"{project_slug}.question").exists()


def write_answer(project_slug: str, answer: str):
    (PENDING_DIR / f"{project_slug}.answer").write_text(answer)
    log.info(f"Answer written for {project_slug}: {answer[:80]}")


def clear_question(project_slug: str):
    (PENDING_DIR / f"{project_slug}.question").unlink(missing_ok=True)
    (PENDING_DIR / f"{project_slug}.answer").unlink(missing_ok=True)


def read_checkpoint(proj: dict) -> dict:
    proj_path = proj.get("path")
    if not proj_path:
        return {}
    cp = Path(proj_path) / ".claude/oms-checkpoint.json"
    if cp.exists():
        try:
            return json.loads(cp.read_text())
        except Exception:
            pass
    return {}


async def get_or_create_task_thread(
    slug: str,
    task_id: str,
    channel: discord.TextChannel,
    description: str = "",
) -> discord.Thread:
    """Return existing thread for this task, or create one with a starter message."""
    key = f"{slug}:{task_id}"
    if key in task_threads:
        return task_threads[key]

    thread_name = task_id[:100]

    # Search active (non-archived) threads first — fast, no API call
    try:
        for thread in channel.threads:
            if thread.name == thread_name:
                task_threads[key] = thread
                return thread
    except Exception as e:
        log.warning(f"Failed to search active threads for {key}: {e}")

    # Search archived threads — survives bot restart and thread auto-archive
    try:
        async for thread in channel.archived_threads(limit=100):
            if thread.name == thread_name:
                task_threads[key] = thread
                return thread
    except Exception as e:
        log.warning(f"Failed to search archived threads for {key}: {e}")

    # Create new: post starter message in main channel, attach thread to it
    label = f" — {description}" if description else ""
    starter = await channel.send(f"📋 **{task_id}**{label}")
    thread = await starter.create_thread(
        name=thread_name,
        auto_archive_duration=10080,  # 7 days
    )
    task_threads[key] = thread
    log.info(f"Created thread for {key}")
    return thread




def _get_text_channel(channel_id: str | int | None) -> discord.TextChannel | None:
    """Return a TextChannel by ID, or None for non-text channel types."""
    if not channel_id:
        return None
    ch = bot.get_channel(int(channel_id))
    return ch if isinstance(ch, discord.TextChannel) else None


def _get_sendable(channel_id: str | int | None) -> discord.TextChannel | discord.Thread | None:
    """Return a sendable channel/thread by ID, or None for unsendable types."""
    if not channel_id:
        return None
    ch = bot.get_channel(int(channel_id))
    return ch if isinstance(ch, (discord.TextChannel, discord.Thread)) else None


def split_for_discord(text: str, limit: int = 1900) -> list[str]:
    """Split at paragraph → sentence → word boundary. Never cuts mid-word."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # Prefer paragraph break
        cut = text.rfind("\n\n", 0, limit)
        if cut == -1:
            # Sentence boundary
            for sep in (". ", "! ", "? ", "\n"):
                cut = text.rfind(sep, 0, limit)
                if cut != -1:
                    cut += len(sep)
                    break
        if cut <= 0:
            cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return chunks


def format_step_update(output: str) -> str:
    """Extract the ## OMS Update line from step output."""
    lines = output.strip().split("\n")
    capture = False
    for line in lines:
        if line.strip() == "## OMS Update":
            capture = True
            continue
        if capture and line.strip():
            return line.strip()[:400]
    # Fallback: last non-empty line that isn't raw JSON
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("{") and not stripped.startswith('"'):
            return stripped[:400]
    return "Step complete"



def _parse_work_output(raw: str, slug: str, label: str = "work") -> tuple[str, float | None]:
    """Parse oms-work.py JSON output. Returns (display_text, cost_usd_or_none)."""
    session_cost: float | None = None
    output = raw
    try:
        parsed = json.loads(raw)
        session_cost = parsed.get("total_cost_usd")
        output = parsed.get("result", "") or parsed.get("content", "") or raw
    except (json.JSONDecodeError, AttributeError):
        pass
    if session_cost is not None:
        _record_work_session_cost(slug, session_cost)
        log.info(f"[{label}] {slug} — done, cost ${session_cost:.4f}")
    else:
        log.info(f"[{label}] {slug} — done (no cost data)")
    return output, session_cost


def _unblock_ceo_gate(proj: dict, slug: str = "") -> None:
    """
    Advance checkpoint from waiting_ceo → synthesis when CEO answers a blocking question.
    Only fires for real CEO gate blocks — never for pipeline_frozen (stuck step).
    Also clears any stale stuck-step counter for the step that was waiting.
    """
    proj_path = proj.get("path", "")
    if not proj_path:
        return
    cp_path = Path(proj_path) / ".claude/oms-checkpoint.json"
    try:
        cp = json.loads(cp_path.read_text()) if cp_path.exists() else {}
        if cp.get("next") == "waiting_ceo":
            task_id = cp.get("task_id", "")
            cp["next"] = "synthesis"
            tmp = str(cp_path) + ".tmp"
            Path(tmp).write_text(json.dumps(cp))
            Path(tmp).replace(cp_path)
    except Exception:
        pass





# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
config: dict = {}


BRIEF_LAST_FILE = HOME / ".claude" / "oms-brief-last.txt"
OMS_BRIEF = HOME / ".claude" / "bin" / "oms-brief.py"
BRIEF_HOUR_LOCAL = 6  # 6am local time (system timezone handles PST/PDT)


def _brief_sent_today() -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        return BRIEF_LAST_FILE.exists() and BRIEF_LAST_FILE.read_text().strip() == today
    except Exception:
        return False


def _mark_brief_sent() -> None:
    try:
        BRIEF_LAST_FILE.write_text(datetime.now().strftime("%Y-%m-%d"))
    except Exception:
        pass


async def poll_brief():
    """Check every 60s if it's 6am local time and brief hasn't been sent today.
    Runs inside the bot — fires even if the Mac was asleep at 6am, as long as
    the bot process is running (kept alive by the OMS heartbeat + caffeinate).
    """
    while True:
        await asyncio.sleep(60)
        try:
            now = datetime.now()
            if now.hour >= BRIEF_HOUR_LOCAL and not _brief_sent_today():
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(OMS_BRIEF),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
                if proc.returncode == 0:
                    _mark_brief_sent()
                    log.info("[brief] daily brief posted")
                else:
                    log.error(f"[brief] failed: {stderr.decode()[:200]}")
        except Exception as exc:
            log.error(f"[poll_brief] {exc}")


@bot.event
async def on_ready():
    global config, _first_ready
    config = load_config()
    log.info(f"OMS bot online as {bot.user}")
    if _first_ready:
        _first_ready = False
        updates_id = config.get("updates_channel_id")
        if updates_id:
            ch = bot.get_channel(int(updates_id))
            if isinstance(ch, discord.TextChannel):
                await ch.send("🤖 OMS bot online")
        pass  # daily brief is handled by com.lewis.oms-brief launchd job




def _record_work_session_cost(slug: str, cost_usd: float) -> None:
    """Append a !work session total to oms-budget.json week/session spend."""
    import datetime as _dt
    budget_file = HOME / ".claude/oms-budget.json"
    tmp = budget_file.with_suffix(".tmp")
    try:
        b = json.loads(budget_file.read_text()) if budget_file.exists() else {}
        now = _dt.datetime.now(_dt.timezone.utc)

        # Session window reset
        window_hours = b.get("session_window_hours", 5)
        start_raw = b.get("current_session_start", "")
        if start_raw:
            ss = _dt.datetime.fromisoformat(start_raw)
            if ss.tzinfo is None:
                ss = ss.replace(tzinfo=_dt.timezone.utc)
            if (now - ss) >= _dt.timedelta(hours=window_hours):
                b["current_session_spend_usd"] = 0.0
                b["current_session_start"] = now.isoformat()
        else:
            b["current_session_start"] = now.isoformat()

        # Week reset
        week_start_raw = b.get("current_week_start", "")
        if week_start_raw:
            ws = _dt.datetime.fromisoformat(week_start_raw)
            if ws.tzinfo is None:
                ws = ws.replace(tzinfo=_dt.timezone.utc)
            if (now - ws).days >= 7:
                b["current_week_spend_usd"] = 0.0
                b["current_week_start"] = now.isoformat()
        else:
            b["current_week_start"] = now.isoformat()

        b["current_session_spend_usd"] = b.get("current_session_spend_usd", 0.0) + cost_usd
        b["current_week_spend_usd"] = b.get("current_week_spend_usd", 0.0) + cost_usd
        b.setdefault("work_sessions", []).append({
            "slug": slug,
            "cost_usd": cost_usd,
            "ts": now.isoformat(),
        })

        tmp.write_text(json.dumps(b, indent=2))
        tmp.replace(budget_file)
    except Exception as exc:
        log.error(f"[work] budget update failed: {exc}")


def _budget_summary() -> str:
    """Read oms-budget.json and cost files, return formatted summary."""
    budget_file = HOME / ".claude/oms-budget.json"
    costs_dir = HOME / ".claude/oms-costs"
    try:
        b = json.loads(budget_file.read_text()) if budget_file.exists() else {}
        limit = b.get("weekly_limit_usd", 50)
        spend = b.get("current_week_spend_usd", 0)
        pct = (spend / limit * 100) if limit > 0 else 0
        week_start = b.get("current_week_start", "")[:10] or "unknown"

        # Per-project breakdown from cost files
        lines = [f"**Weekly budget**: ${spend:.2f} / ${limit:.0f} ({pct:.1f}%) — week of {week_start}"]
        if costs_dir.exists():
            by_slug: dict[str, float] = {}
            for f in sorted(costs_dir.glob("*.json")):
                try:
                    d = json.loads(f.read_text())
                    slug = d.get("slug", f.stem.split("-")[0])
                    by_slug[slug] = by_slug.get(slug, 0) + d.get("total_usd", 0)
                except Exception:
                    pass
            if by_slug:
                lines.append("**Per project:**")
                for slug, total in sorted(by_slug.items(), key=lambda x: -x[1]):
                    lines.append(f"  • {slug}: ${total:.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not read budget: {e}"



async def handle_idea_thread_reply(message: discord.Message, content: str, thread: discord.Thread, known_slug: str = "", known_path: str = ""):
    """
    Ideas thread handler — Q&A only.
    Appends each reply to IDEA.md so oms-start (REPL) gets full context.
    Answers questions using gemma (free) with haiku fallback.
    """
    # Resolve slug + path
    if known_slug and known_path:
        slug = known_slug
        project_path = Path(known_path)
    else:
        slug = thread.name.removeprefix("oms-start: ").removeprefix("idea: ").strip()
        slug = slug.replace(" ", "-").lower()
        project_path = HOME / "code" / "personal" / slug

    # Append this message to IDEA.md (keeps full discussion for oms-start)
    if project_path.exists():
        idea_file = project_path / "IDEA.md"
        try:
            existing = idea_file.read_text() if idea_file.exists() else f"# {slug}\n"
            idea_file.write_text(existing.rstrip() + f"\n\n## Discussion\n**User:** {content}\n")
        except Exception as e:
            log.error(f"[idea] failed to append to IDEA.md: {e}")

    # Build Q&A prompt with thread context
    history_lines = []
    async for msg in thread.history(limit=50, oldest_first=True):
        if msg.author.bot and msg.content in ("⏳",):
            continue
        role = "Assistant" if msg.author.bot else "User"
        history_lines.append(f"{role}: {msg.content}")
    conversation = "\n".join(history_lines)

    prompt = (
        f"Project: {slug}\n\n"
        f"Thread conversation:\n{conversation}\n\n"
        f"User just said: {content}\n\n"
        "Answer directly and concisely. Help refine the project idea. "
        "Do not run oms-start. Do not write files."
    )
    qa_cwd = str(project_path) if project_path.exists() else str(HOME)

    await message.add_reaction("⏳")
    try:
        response = ""
        try:
            response, rc = await _run_llm_route('gemma', prompt, qa_cwd, timeout=120)
        except Exception as e:
            log.error(f"[idea-qa] gemma failed: {e}")
            rc = 1
        if rc != 0 or not response.strip():
            log.info(f"[idea-qa] gemma failed (rc={rc}), falling back to haiku")
            proc = await asyncio.create_subprocess_exec(
                str(HOME / ".local/bin/claude"),
                "--print", "--bare", "--permission-mode", "auto",
                "--model", "claude-haiku-4-5-20251001",
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=qa_cwd,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            response = stdout.decode().strip()

        if response:
            for chunk in split_for_discord(response):
                await thread.send(chunk)
        else:
            await thread.send("_(no response — try again)_")
        if bot.user:
            await message.remove_reaction("⏳", bot.user)
    except asyncio.TimeoutError:
        log.error(f"[idea-qa] timed out for {slug}")
        await thread.send("⏱️ Timed out — reply again to continue")
        if bot.user:
            await message.remove_reaction("⏳", bot.user)
    except Exception as e:
        log.error(f"[idea-qa] error for {slug}: {e}")
        await thread.send(f"❌ {e}")
        if bot.user:
            await message.remove_reaction("⏳", bot.user)


async def handle_claude_thread_reply(content: str, thread: discord.Thread):
    """Continue a #claude conversation thread with full history. Uses free models first."""
    if not content:
        return

    # Fetch thread history (up to 20 messages, oldest first, skip bot's ⏳ indicator)
    history = []
    async for msg in thread.history(limit=20, oldest_first=True):
        if msg.author.bot and msg.content == "⏳":
            continue
        role = "Assistant" if msg.author.bot else "User"
        history.append(f"{role}: {msg.content}")

    # Build prompt with conversation context
    conversation = "\n".join(history[:-1])  # exclude the latest message (already in content)
    if conversation:
        prompt = f"Conversation so far:\n{conversation}\n\nUser: {content}\n\nContinue the conversation."
    else:
        prompt = content

    await thread.send("⏳")
    try:
        response, rc = await _run_llm_route('gemma', prompt, str(HOME), timeout=120)
        if rc != 0 or not response.strip():
            log.info(f"[claude-qa] gemma failed (rc={rc}), falling back to haiku")
            proc = await asyncio.create_subprocess_exec(
                str(HOME / ".local/bin/claude"),
                "--print", "--bare", "--permission-mode", "auto",
                "--model", "claude-haiku-4-5-20251001",
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(HOME),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
            response = stdout.decode().strip()
        response = response or "_(no response)_"
    except asyncio.TimeoutError:
        response = "⏱️ Timed out (5min)"
    except Exception as e:
        log.error(f"[claude-qa] thread reply error: {e}")
        response = f"❌ Error: {e}"

    for chunk in split_for_discord(response):
        await thread.send(chunk)


async def handle_claude_message(message: discord.Message, content: str):
    """Direct Claude access from #claude channel. Uses free models first."""
    if not content:
        return
    # /budget shortcut — no Claude needed
    if content.lower().strip() in ("/budget", "budget"):
        await message.reply(_budget_summary(), mention_author=False)
        return

    thread = await message.create_thread(name=content[:80])
    await thread.send("⏳")
    try:
        response, rc = await _run_llm_route('gemma', content, str(HOME), timeout=120)
        if rc != 0 or not response.strip():
            log.info(f"[claude-qa] gemma failed (rc={rc}), falling back to haiku")
            proc = await asyncio.create_subprocess_exec(
                str(HOME / ".local/bin/claude"),
                "--print", "--bare", "--permission-mode", "auto",
                "--model", "claude-haiku-4-5-20251001",
                "-p", content,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(HOME),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
            response = stdout.decode().strip()
        response = response or "_(no response)_"
    except asyncio.TimeoutError:
        response = "⏱️ Timed out (5min)"
    except Exception as e:
        response = f"❌ Error: {e}"

    for chunk in split_for_discord(response):
        await thread.send(chunk)


@bot.command(name="budget")
async def budget_cmd(ctx):
    """Show weekly OMS budget usage in any channel."""
    await ctx.reply(_budget_summary(), mention_author=False)



@bot.command(name="next")
async def next_cmd(ctx):
    """Trigger completion report + start next task for current project channel."""
    channel = ctx.channel
    cfg = load_config()
    result = get_project_by_channel(cfg, channel.id)
    if not result:
        await ctx.reply("Not a project channel.", mention_author=False)
        return
    slug, proj = result
    cp = read_checkpoint(proj)
    nxt = cp.get("next", "")
    task_id = cp.get("task_id", "")
    if nxt not in ("done", "complete"):
        await ctx.reply(
            f"Task `{task_id}` is still in progress (next: `{nxt}`). "
            "Use `!next` only after a task is complete.",
            mention_author=False,
        )
        return
    await ctx.reply("Use `/work` in Discord to trigger oms-work for this project.", mention_author=False)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Dedup: Discord gateway can deliver the same message twice on reconnect
    if message.id in _processed_messages:
        return
    _processed_messages.add(message.id)
    # Keep set bounded — only track last 500 messages
    if len(_processed_messages) > 500:
        _processed_messages.clear()

    channel = message.channel
    content = message.content.strip()

    # --- Thread message ---
    if isinstance(channel, discord.Thread):
        # #claude conversation thread — continue with full history
        claude_channel_id = config.get("claude_channel_id")
        if claude_channel_id and channel.parent_id == int(claude_channel_id):
            await handle_claude_thread_reply(content, channel)
            return
        # Ideas thread — continue oms-start conversation
        ideas_id = config.get("ideas_channel_id")
        if ideas_id and channel.parent_id == int(ideas_id):
            await handle_idea_thread_reply(message, content, channel)
            return
        # OMS task/idea thread
        result = get_project_by_thread(config, channel)
        if result:
            slug, proj = result
            await handle_thread_message(message, slug, proj, content, channel)
            return
        await bot.process_commands(message)
        return

    # --- Project main channel ---
    result = get_project_by_channel(config, channel.id)
    if result:
        slug, proj = result
        await handle_project_message(message, slug, proj, content)
        return

    # --- Ideas channel ---
    ideas_id = config.get("ideas_channel_id")
    if ideas_id and str(channel.id) == str(ideas_id):
        await handle_idea(message, content)
        return

    # --- #claude general channel ---
    claude_channel_id = config.get("claude_channel_id")
    if claude_channel_id and str(channel.id) == str(claude_channel_id):
        await handle_claude_message(message, content)
        return

    await bot.process_commands(message)


async def handle_thread_message(
    message: discord.Message,
    slug: str,
    proj: dict,
    content: str,
    thread: discord.Thread,
):
    """Handle CEO messages inside a task thread."""

    raw_parent = thread.parent
    channel = raw_parent if isinstance(raw_parent, discord.TextChannel) else None

    # Blocking question answer
    if is_blocking_question_pending(slug):
        write_answer(slug, content)
        clear_question(slug)
        _unblock_ceo_gate(proj, slug)
        await message.add_reaction("✅")
        await thread.send("Got it — re-run `/work` to resume OMS.")
        return

    # /oms <task> in a thread → start a new OMS task (same as main channel)
    if content.lower().startswith("/oms") or content.lower().startswith("!oms"):
        if channel:
            await handle_project_message(message, slug, proj, content)
        return

    # Observer Q&A — direct claude call, read-only
    await handle_thread_qa(message, proj, content)


async def handle_project_message(
    message: discord.Message, slug: str, proj: dict, content: str
):
    """Route CEO messages in the main project channel."""
    if not isinstance(message.channel, discord.TextChannel):
        return
    channel = message.channel

    # Blocking question answer posted to main channel (fallback — ideally answered in thread)
    if is_blocking_question_pending(slug):
        write_answer(slug, content)
        clear_question(slug)
        _unblock_ceo_gate(proj, slug)
        await message.add_reaction("✅")
        await message.reply("Got it — run `/work` to resume.", mention_author=False)
        return

    # !work — run cleared-queue tasks for this project via skill
    if content.strip().lower() in ("!work", "/work", "!oms-work", "/oms-work"):
        queue_path = Path(proj.get("path", "")) / ".claude" / "cleared-queue.md"
        if not queue_path.exists():
            await message.reply(
                "No cleared-queue.md found. Run /oms session first to generate tasks.",
                mention_author=False,
            )
            return
        log.info(f"[work] {slug} — started")
        await message.add_reaction("⚙️")

        # Call oms-work.py directly (Python script, not Claude skill)
        use_fallback = False
        raw = ""
        err = ""
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3",
                str(HOME / ".claude" / "bin" / "oms-work.py"),
                slug,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(HOME),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=14400)
            raw = stdout.decode().strip()
            err = stderr.decode().strip()

            # Check if rate limited — if so, retry with fallback
            if proc.returncode != 0 and _is_rate_limited(err):
                use_fallback = True
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                use_fallback = True
            else:
                raise

        # Rate-limited: schedule auto-resume (oms-work.py already falls back to
        # free models internally — if it still fails, we wait for session reset)
        if use_fallback:
            log.info(f"[work] {slug} — rate limited, scheduling auto-resume")
            reset_iso = _rate_limit_reset_iso()
            _save_pending_resume(slug, str(channel.id), reset_iso)
            import datetime as _dt
            rt = _dt.datetime.fromisoformat(reset_iso).astimezone()
            await message.reply(
                f"⏸ Rate limit hit (oms-work.py already tried free models). "
                f"Auto-resume at `{rt.strftime('%H:%M %Z')}`.",
                mention_author=False,
            )
            if bot.user:
                await message.remove_reaction("⚙️", bot.user)
            return

        if bot.user:
            await message.remove_reaction("⚙️", bot.user)

        output, _ = _parse_work_output(raw, slug, "work")

        if proc and proc.returncode != 0 and err:
            if _is_rate_limited(err):
                reset_iso = _rate_limit_reset_iso()
                _save_pending_resume(slug, str(channel.id), reset_iso)
                import datetime as _dt
                rt = _dt.datetime.fromisoformat(reset_iso).astimezone()
                await channel.send(
                    f"⏸ `{slug}` hit Claude rate limit — will auto-resume at "
                    f"`{rt.strftime('%H:%M %Z')}` when session window resets."
                )
            else:
                await channel.send(f"[{slug}] oms-work error: {err[:500]}")
            return
        await channel.send(output or f"[{slug}] oms-work: no tasks ran")
        return

    # /oms with no task → auto-pick from backlog
    # All other messages → observer Q&A (read-only)
    await handle_thread_qa(message, proj, content)


async def handle_thread_qa(
    message: discord.Message, proj: dict, content: str
):
    """CEO observer Q&A — uses free models first, Haiku fallback. Read-only."""
    proj_path = proj.get("path", "")
    prompt = (
        f"CEO observer question (do NOT run OMS steps, do NOT modify files): {content}\n\n"
        "Read the relevant task logs in logs/tasks/ and answer directly. No preamble."
    )
    qa_cwd = proj_path or str(HOME)
    await message.add_reaction("💬")
    try:
        # Try free model first (gemma — fast Q&A)
        response = ""
        rc = 1
        try:
            response, rc = await _run_llm_route('gemma', prompt, qa_cwd, timeout=120)
        except Exception as e:
            log.error(f"[thread-qa] gemma failed: {e}")
        # Fallback to subscription haiku if free model fails
        if rc != 0 or not response.strip():
            log.info(f"[thread-qa] gemma failed (rc={rc}), falling back to haiku")
            proc = await asyncio.create_subprocess_exec(
                str(HOME / ".local/bin/claude"),
                "--print", "--bare", "--permission-mode", "auto",
                "--model", "claude-haiku-4-5-20251001",
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=qa_cwd,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
            response = stdout.decode().strip()
        response = response or "_(no response)_"
    except asyncio.TimeoutError:
        response = "⏱️ Timed out (2min)"
    except Exception as e:
        response = f"❌ {e}"
    for chunk in split_for_discord(response):
        await message.reply(chunk, mention_author=False)
    try:
        if bot.user:
            await message.remove_reaction("💬", bot.user)
    except Exception:
        pass



def _extract_slug(idea: str) -> str:
    """Extract project slug from first line of idea text. No LLM call — pure text."""
    # Use first line (or first sentence before a period/newline)
    first_line = idea.strip().split('\n')[0].strip()
    # Remove markdown headers
    first_line = re.sub(r'^#+\s*', '', first_line)
    # Take up to first 5 words for the slug
    words = re.findall(r'[a-zA-Z0-9]+', first_line)[:5]
    if words:
        slug = '-'.join(w.lower() for w in words)
        return slug[:40]  # cap at 40 chars
    return f"project-{int(datetime.now(timezone.utc).timestamp())}"



async def handle_idea(message: discord.Message, content: str):
    """
    New idea in #ideas — capture only:
    1. Extract slug from first line (no LLM call)
    2. Create project dir + write IDEA.md to disk
    3. Reply in thread confirming capture + REPL instructions
    """
    if not message.guild:
        return
    await message.add_reaction("⏳")

    try:
        slug = _extract_slug(content)
        project_path = HOME / "code" / "personal" / slug
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / ".claude" / "agents").mkdir(parents=True, exist_ok=True)

        idea_body = f"# {slug}\n\n{content}\n"
        (project_path / "IDEA.md").write_text(idea_body)
        (project_path / "README.md").write_text(idea_body)

        # Create thread for follow-up discussion
        thread = await message.create_thread(
            name=f"idea: {slug}",
            auto_archive_duration=10080,
        )
        await thread.send(
            f"Captured idea as `{slug}/`\n"
            f"Path: `{project_path}`\n\n"
            f"Run `/oms-start` in Claude Code REPL to initialize the project.\n"
            f"Reply here to refine the idea — your messages will be appended to IDEA.md."
        )

        if bot.user:
            await message.remove_reaction("⏳", bot.user)
        await message.add_reaction("✅")
        log.info(f"[idea] captured: {slug} at {project_path}")
    except Exception as e:
        log.error(f"[idea] failed to capture idea: {e}")
        await message.reply(f"Failed to capture idea: {e}", mention_author=False)
        if bot.user:
            await message.remove_reaction("⏳", bot.user)


# --- Rate-limit retry helpers ---

_RATE_LIMIT_PATTERNS = (
    "rate limit", "rate_limit", "usage limit", "claude max", "overloaded",
    "429", "529", "exceeded", "quota",
)


async def _run_llm_route(model: str, prompt: str, cwd: str | Path, timeout: int = 180) -> tuple[str, int]:
    """Run llm-route.sh async. Returns (stdout, returncode)."""
    proc = await asyncio.create_subprocess_exec(
        str(LLM_ROUTE), model,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
    )
    stdout, _ = await asyncio.wait_for(
        proc.communicate(input=prompt.encode()), timeout=timeout
    )
    return stdout.decode().strip(), proc.returncode or 0


def _is_rate_limited(err: str) -> bool:
    low = err.lower()
    return any(p in low for p in _RATE_LIMIT_PATTERNS)


def _rate_limit_reset_iso() -> str:
    """Return ISO timestamp of when the current session window resets."""
    import datetime as _dt
    try:
        if BUDGET_FILE.exists():
            b = json.loads(BUDGET_FILE.read_text())
            start_raw = b.get("current_session_start", "")
            window_h = b.get("session_window_hours", 5)
            if start_raw:
                ss = _dt.datetime.fromisoformat(start_raw)
                if ss.tzinfo is None:
                    ss = ss.replace(tzinfo=_dt.timezone.utc)
                reset = ss + _dt.timedelta(hours=window_h)
                # If already past, reset is now + 5 minutes (handles edge cases)
                now = _dt.datetime.now(_dt.timezone.utc)
                if reset <= now:
                    reset = now + _dt.timedelta(minutes=5)
                return reset.isoformat()
    except Exception:
        pass
    # Fallback: 5h from now
    import datetime as _dt2
    return (_dt2.datetime.now(_dt2.timezone.utc) + _dt2.timedelta(hours=5)).isoformat()


def _save_pending_resume(slug: str, channel_id: str, reset_iso: str) -> None:
    try:
        data: dict = {}
        if PENDING_RESUMES_FILE.exists():
            data = json.loads(PENDING_RESUMES_FILE.read_text())
        data[slug] = {"channel_id": channel_id, "reset_at": reset_iso}
        PENDING_RESUMES_FILE.write_text(json.dumps(data))
    except Exception as exc:
        log.error(f"[rate-limit] Failed to save pending resume for {slug}: {exc}")


def _clear_pending_resume(slug: str) -> None:
    try:
        if not PENDING_RESUMES_FILE.exists():
            return
        data = json.loads(PENDING_RESUMES_FILE.read_text())
        data.pop(slug, None)
        PENDING_RESUMES_FILE.write_text(json.dumps(data))
    except Exception:
        pass


async def poll_pending_resumes():
    """
    Check oms-pending-resumes.json every 60s.
    When a project's reset_at time has passed, auto-trigger oms-work for it.
    """
    import datetime as _dt
    while True:
        await asyncio.sleep(60)
        try:
            if not PENDING_RESUMES_FILE.exists():
                continue
            data: dict = json.loads(PENDING_RESUMES_FILE.read_text())
            if not data:
                continue
            now = _dt.datetime.now(_dt.timezone.utc)
            for slug, entry in list(data.items()):
                reset_raw = entry.get("reset_at", "")
                channel_id = entry.get("channel_id", "")
                if not reset_raw or not channel_id:
                    continue
                try:
                    reset_dt = _dt.datetime.fromisoformat(reset_raw)
                    if reset_dt.tzinfo is None:
                        reset_dt = reset_dt.replace(tzinfo=_dt.timezone.utc)
                except Exception:
                    continue
                if now < reset_dt:
                    continue
                # Window has reset — fire oms-work
                ch = _get_sendable(channel_id)
                if ch:
                    await ch.send(f"⏰ Session window reset — auto-resuming `{slug}` OMS queue…")
                _clear_pending_resume(slug)
                cfg = load_config()
                proj = cfg.get("projects", {}).get(slug, {})
                queue_path = Path(proj.get("path", "")) / ".claude" / "cleared-queue.md"
                if not queue_path.exists():
                    if ch:
                        await ch.send(f"[{slug}] No cleared-queue.md found — skipping auto-resume.")
                    continue
                log.info(f"[work] {slug} — auto-resume started")
                proc = await asyncio.create_subprocess_exec(
                    "python3",
                    str(HOME / ".claude" / "bin" / "oms-work.py"),
                    slug,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(HOME),
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=14400)
                except asyncio.TimeoutError:
                    if ch:
                        await ch.send(f"[{slug}] auto-resume timed out (2h)")
                    continue
                raw = stdout.decode().strip()
                err = stderr.decode().strip()
                output, _ = _parse_work_output(raw, slug, "auto-resume")
                if proc.returncode != 0 and err:
                    if _is_rate_limited(err):
                        # Still rate limited — reschedule
                        new_reset = _rate_limit_reset_iso()
                        _save_pending_resume(slug, channel_id, new_reset)
                        if ch:
                            import datetime as _dt3
                            rt = _dt3.datetime.fromisoformat(new_reset).astimezone()
                            await ch.send(
                                f"[{slug}] Still rate limited — will retry at "
                                f"`{rt.strftime('%H:%M %Z')}`"
                            )
                    else:
                        if ch:
                            await ch.send(f"[{slug}] auto-resume error: {err[:500]}")
                else:
                    if ch:
                        await ch.send(output or f"[{slug}] auto-resume: no tasks ran")
        except Exception as exc:
            log.error(f"[poll_pending_resumes] {exc}")


# --- Blocking question polling ---
async def poll_and_post_questions():
    """
    OMS writes blocking questions to PENDING_DIR/[slug].question.
    Post them to the task thread. CEO replies in thread to unblock.
    """
    posted: set[str] = set()
    while True:
        await asyncio.sleep(5)
        try:
            cfg = load_config()
            for slug, proj in cfg.get("projects", {}).items():
                q_file = PENDING_DIR / f"{slug}.question"
                if not q_file.exists():
                    posted.discard(slug)
                    continue

                data = json.loads(q_file.read_text())
                task_id = data.get("task_id", "")
                question = data.get("question", "")
                asked_at = data.get("asked_at", "")

                if slug in posted:
                    # Remind once per 24h — use last_reminded field to avoid spurious repeats
                    if asked_at:
                        asked = datetime.fromisoformat(asked_at)
                        elapsed = (datetime.now(timezone.utc) - asked).total_seconds()
                        last_reminded = data.get("last_reminded", 0)
                        now_ts = datetime.now(timezone.utc).timestamp()
                        if elapsed > 86400 and now_ts - last_reminded > 86400:
                            thread = task_threads.get(f"{slug}:{task_id}")
                            target = thread
                            if target is None:
                                ch_id = proj.get("channel_id")
                                target = _get_sendable(ch_id)
                            if target:
                                await target.send(
                                    f"⏰ Still waiting for your answer to resume OMS. "
                                    f"(waiting {int(elapsed / 3600)}h)"
                                )
                            # Update last_reminded in the question file
                            try:
                                data["last_reminded"] = now_ts
                                q_file.write_text(json.dumps(data))
                            except Exception:
                                pass
                    continue

                # Post to task thread if available, else fall back to main channel
                thread = task_threads.get(f"{slug}:{task_id}")
                if thread is None:
                    ch_id = proj.get("channel_id")
                    ch = _get_text_channel(ch_id)
                    if ch and task_id:
                        thread = await get_or_create_task_thread(slug, task_id, ch)

                target: discord.Thread | discord.TextChannel | None = thread
                if target is None:
                    target = _get_text_channel(proj.get("channel_id"))

                if target:
                    header = "⚠️ **CEO decision required** — OMS is blocked until you reply\n\n"
                    body = question if question else "_No question text written — check task log._"
                    footer = "\n\n_Reply in this thread to unblock OMS._"
                    full = header + body + footer
                    for chunk in split_for_discord(full):
                        await target.send(chunk)
                    posted.add(slug)
                    log.info(f"Posted blocking question for {slug} in thread")

        except Exception as e:
            log.error(f"Poll error: {e}")


@bot.event
async def setup_hook():
    bot.loop.create_task(poll_and_post_questions())
    bot.loop.create_task(poll_pending_resumes())
    bot.loop.create_task(poll_brief())


_shutdown_fired = False

async def _post_offline():
    """Post offline notice then close bot. Runs at most once."""
    global _shutdown_fired
    if _shutdown_fired:
        return
    _shutdown_fired = True
    updates_id = config.get("updates_channel_id") if config else None
    if updates_id:
        ch = _get_text_channel(updates_id)
        if ch:
            try:
                await ch.send("🔴 OMS bot offline")
            except Exception:
                pass
    await bot.close()


def _handle_shutdown(sig, frame):  # pyright: ignore[reportUnusedParameter]
    if _shutdown_fired:
        return
    log.info(f"Received signal {sig} — shutting down")
    loop = asyncio.get_event_loop()
    loop.create_task(_post_offline())


# --- Entry point ---
PID_FILE = HOME / ".claude/discord-bot.pid"

if __name__ == "__main__":
    if not TOKEN_FILE.exists():
        log.error("Discord token not found at ~/.config/discord/token")
        log.error("Run /init-oms in Claude Code to set up.")
        sys.exit(1)

    # Kill any existing bot process before starting
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            import os as _os
            _os.kill(old_pid, signal.SIGTERM)
            log.info(f"Killed previous bot (pid {old_pid})")
            import time; time.sleep(2)  # wait for old bot to disconnect
        except (ProcessLookupError, ValueError):
            pass

    PID_FILE.write_text(str(__import__('os').getpid()))

    token = TOKEN_FILE.read_text().strip()
    log.info("Starting OMS Discord bot...")

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _handle_shutdown)

    try:
        bot.run(token)
    finally:
        PID_FILE.unlink(missing_ok=True)
