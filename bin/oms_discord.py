#!/usr/bin/env python3
"""
Discord notification helper for oms-work.
Reads bot token from ~/.config/discord/token.
Posts only final task status — no intermediate steps.
"""
import json
import urllib.request
import urllib.error
from pathlib import Path

TOKEN_FILE = Path.home() / '.config' / 'discord' / 'token'
API = 'https://discord.com/api/v10'


def _token() -> str:
    return TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else ''


def _request(method: str, path: str, body: dict | None = None) -> dict | None:
    token = _token()
    if not token:
        return None
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f'{API}{path}', data=data, method=method,
        headers={
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'DiscordBot (https://github.com/lewis/oms, 1.0)',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f'[discord] {method} {path} → {e.code}: {e.read()[:120]}', flush=True)
        return None
    except Exception:
        return None


def post_message(channel_id: str, content: str) -> str | None:
    """Post to a channel. Returns message_id or None."""
    r = _request('POST', f'/channels/{channel_id}/messages', {'content': content})
    return r['id'] if r else None


def create_thread(channel_id: str, name: str) -> str | None:
    """Create a public thread in a text channel. Returns thread_id or None."""
    r = _request('POST', f'/channels/{channel_id}/threads', {
        'name': name[:100],
        'auto_archive_duration': 10080,  # 7 days
        'type': 11,                       # PUBLIC_THREAD
    })
    return r['id'] if r else None


def post_to_thread(thread_id: str, content: str) -> None:
    _request('POST', f'/channels/{thread_id}/messages', {'content': content})


def get_or_create_thread(channel_id: str, threads_file: Path, milestone: str) -> str | None:
    """Look up or create a Discord thread for a milestone. Persists thread_id to threads_file."""
    threads: dict[str, str] = {}
    if threads_file.exists():
        try:
            threads = json.loads(threads_file.read_text())
        except Exception:
            pass

    if milestone in threads:
        return threads[milestone]

    thread_id = create_thread(channel_id, f'Milestone: {milestone}')
    if thread_id:
        threads[milestone] = thread_id
        threads_file.write_text(json.dumps(threads, indent=2))
    return thread_id


def notify_task(channel_id: str, threads_file: Path,
                milestone: str | None, task_id: str, title: str,
                passed: bool, notes: str) -> None:
    """Post final task status. Uses milestone thread if milestone is set."""
    icon = '✓' if passed else '⚑'
    status = 'done' if passed else 'cto-stop'
    short_notes = notes[:180] if notes else ''
    msg = f'{icon} **{task_id}** — {title} `{status}`'
    if short_notes and not passed:
        msg += f'\n> {short_notes}'

    if milestone and milestone.lower() != 'none':
        thread_id = get_or_create_thread(channel_id, threads_file, milestone)
        if thread_id:
            post_to_thread(thread_id, msg)
            return

    post_message(channel_id, msg)


def post_brief_to_thread(channel_id: str, threads_file: Path,
                         milestone: str, tldr_lines: list[str],
                         what_was_done: list[str] | None = None) -> None:
    """Post executive brief (TL;DR + What Was Done) to a milestone thread."""
    if not tldr_lines:
        return
    parts = ['**📊 Session Summary**']
    for line in tldr_lines:
        parts.append(f'• {line}')
    if what_was_done:
        parts.append('')
        parts.append('**Built:**')
        for item in what_was_done:
            parts.append(f'  {item}')
    msg = '\n'.join(parts)
    thread_id = get_or_create_thread(channel_id, threads_file, milestone)
    if thread_id:
        post_to_thread(thread_id, msg)
    else:
        post_message(channel_id, msg)
