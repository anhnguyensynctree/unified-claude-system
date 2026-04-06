#!/usr/bin/env python3
"""
Discord notification helper for oms-work.
Reads bot token from ~/.config/discord/token.
Posts only final task status — no intermediate steps.
"""
from __future__ import annotations
import json
import uuid
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


def post_to_thread(thread_id: str, content: str) -> bool:
    """Post to a thread. Returns True on success, False if thread is archived/deleted."""
    result = _request('POST', f'/channels/{thread_id}/messages', {'content': content})
    return result is not None


def get_or_create_thread(channel_id: str, threads_file: Path, milestone: str) -> str | None:
    """Look up or create a Discord thread for a milestone. Persists thread_id to threads_file.
    If stored thread is archived/deleted, creates a new one."""
    threads: dict[str, str] = {}
    if threads_file.exists():
        try:
            threads = json.loads(threads_file.read_text())
        except Exception:
            pass

    if milestone in threads:
        # Verify thread is still alive by trying to post (Discord archives threads after 7 days)
        # We'll validate on first actual post — just return the ID here
        return threads[milestone]

    thread_id = create_thread(channel_id, f'Milestone: {milestone}')
    if thread_id:
        threads[milestone] = thread_id
        threads_file.write_text(json.dumps(threads, indent=2))
    return thread_id


def post_to_thread_or_recreate(channel_id: str, threads_file: Path,
                                milestone: str, content: str) -> None:
    """Post to milestone thread. If thread is dead, create a new one and retry."""
    thread_id = get_or_create_thread(channel_id, threads_file, milestone)
    if not thread_id:
        post_message(channel_id, content)
        return

    if not post_to_thread(thread_id, content):
        # Thread is archived/deleted — create new one
        print(f'[discord] Thread {thread_id} dead — creating new thread for {milestone}', flush=True)
        new_id = create_thread(channel_id, f'Milestone: {milestone}')
        if new_id:
            threads: dict[str, str] = {}
            if threads_file.exists():
                try:
                    threads = json.loads(threads_file.read_text())
                except Exception:
                    pass
            threads[milestone] = new_id
            threads_file.write_text(json.dumps(threads, indent=2))
            post_to_thread(new_id, content)
        else:
            post_message(channel_id, content)  # fallback to channel


def notify_task(channel_id: str, threads_file: Path,
                milestone: str | None, task_id: str, title: str,
                passed: bool | None, notes: str) -> None:
    """Post task status. passed=None for running, True for done, False for cto-stop."""
    if passed is None:
        icon, status = '▶', 'running'
    elif passed:
        icon, status = '✓', 'done'
    else:
        icon, status = '⚑', 'cto-stop'
    short_notes = notes[:180] if notes else ''
    msg = f'{icon} **{task_id}** — {title} `{status}`'
    if short_notes:
        msg += f'\n> {short_notes}'

    if milestone and milestone.lower() != 'none':
        post_to_thread_or_recreate(channel_id, threads_file, milestone, msg)
        return

    post_message(channel_id, msg)


_DISCORD_LIMIT = 8 * 1024 * 1024  # 8MB — standard server limit

_MIME: dict[str, str] = {
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif':  'image/gif',
    '.webm': 'video/webm',
    '.mp4':  'video/mp4',
}


def post_media_to_thread(thread_id: str, caption: str, paths: list[Path]) -> None:
    """Upload up to 8 media files (images or videos) as Discord attachments.
    Files over 8MB are skipped with a note appended to caption."""
    token = _token()
    if not token:
        return

    skipped: list[str] = []
    files: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.stat().st_size > _DISCORD_LIMIT:
            skipped.append(p.name)
            continue
        files.append(p)
        if len(files) == 8:
            break

    if not files and not skipped:
        return

    full_caption = caption[:1800]
    if skipped:
        full_caption += f'\n*(videos too large for Discord: {", ".join(skipped)} — see qa/videos/)*'

    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    b = boundary.encode()

    parts.append(b'--' + b + b'\r\n')
    parts.append(b'Content-Disposition: form-data; name="payload_json"\r\n')
    parts.append(b'Content-Type: application/json\r\n\r\n')
    parts.append(json.dumps({'content': full_caption}).encode() + b'\r\n')

    for i, path in enumerate(files):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        mime = _MIME.get(path.suffix.lower(), 'application/octet-stream')
        parts.append(b'--' + b + b'\r\n')
        parts.append(f'Content-Disposition: form-data; name="files[{i}]"; filename="{path.name}"\r\n'.encode())
        parts.append(f'Content-Type: {mime}\r\n\r\n'.encode())
        parts.append(data + b'\r\n')

    parts.append(b'--' + b + b'--\r\n')
    body = b''.join(parts)

    req = urllib.request.Request(
        f'{API}/channels/{thread_id}/messages',
        data=body,
        method='POST',
        headers={
            'Authorization': f'Bot {token}',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'DiscordBot (https://github.com/lewis/oms, 1.0)',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60):
            pass
    except Exception as e:
        print(f'[discord] post_media failed: {e}', flush=True)


# Alias — old callers still work
def post_images_to_thread(thread_id: str, caption: str, image_paths: list[Path]) -> None:
    post_media_to_thread(thread_id, caption, image_paths)


def post_media_batched(thread_id: str, caption: str, paths: list[Path], batch_size: int = 8) -> None:
    """Post all media files to a thread, batching into groups of batch_size (Discord max = 8)."""
    if not paths:
        return
    for i in range(0, len(paths), batch_size):
        batch = paths[i:i + batch_size]
        batch_caption = caption if i == 0 else f'{caption} (cont. {i // batch_size + 1})'
        post_media_to_thread(thread_id, batch_caption, batch)


def post_visual_qa_report(channel_id: str, threads_file: Path,
                          milestone: str,
                          groups: list[dict]) -> None:
    """Post grouped visual QA screenshots to a milestone thread.

    groups: list of dicts with keys:
      - title: str          e.g. "Home Entry"
      - description: str    e.g. "initial render + validation error state"
      - paths: list[Path]   screenshots for this group
    """
    thread_id = get_or_create_thread(channel_id, threads_file, milestone)
    if not thread_id:
        return

    # Header message
    post_to_thread(thread_id, f'**Visual QA — {milestone}**')

    for group in groups:
        title = group.get('title', '')
        description = group.get('description', '')
        paths = [Path(p) for p in group.get('paths', [])]
        paths = [p for p in paths if p.exists()]
        if not paths:
            continue

        # Build caption: bold title + description + bullet per image
        lines = [f'**{title}** — {description}']
        for p in paths:
            # Convert filename to readable label: sim-panel-open → sim panel open
            label = p.stem.replace('-', ' ')
            lines.append(f'  • {label}')
        caption = '\n'.join(lines)
        post_media_to_thread(thread_id, caption, paths)


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
