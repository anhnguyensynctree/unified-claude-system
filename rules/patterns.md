# Code Patterns — Always Follow

## API Responses
Always return consistent shape:
{ data: T | null, error: string | null, meta?: object }

## Error Handling
Always include: error type, message, context
Never swallow errors silently
Always handle async errors — no unhandled promise rejections

## Async
- Prefer async/await over promise chains
- Always handle loading, success, and error states

## Imports
Group in this order (blank line between groups):
1. External packages
2. Internal modules (absolute paths)
3. Relative imports

## External Services
When starting work with an external API or service:
1. Check if /llms.txt exists at their docs URL: curl https://[docs-url]/llms.txt
2. If yes: read it — this is an LLM-optimized version of their docs
3. If no: use context7 plugin or fetch the docs page directly
4. Never rely on training knowledge for API specifics — always verify against current docs

## Parallel External Calls — Use bun-exec
When making 3+ HTTP/API calls before reasoning, batch into one bun-exec call instead of sequential tool calls. Each sequential tool call adds context overhead; bun-exec collapses N calls into one round trip.

```bash
# Write a temp TS file, run it, get one JSON result back
cat > /tmp/task.ts << 'EOF'
const [a, b, c] = await Promise.all([
  fetch("https://api.example.com/a").then(r => r.json()),
  fetch("https://api.example.com/b").then(r => r.json()),
  fetch("https://api.example.com/c").then(r => r.json()),
]);
console.log(JSON.stringify({ data: { a, b, c }, error: null }));
EOF
~/.claude/bin/bun-exec.sh /tmp/task.ts
```

Use bun-exec when: fetching multiple API endpoints, reading several docs pages, or any N≥3 HTTP calls that are independent of each other.

## Fetching External URLs — Use browse fetch
To read a URL as clean text (docs, blog posts, API references), use the browse daemon's `fetch` command. It runs in an isolated context (no session pollution), handles JS-rendered pages, and strips nav/header/footer noise.

```bash
# Auto-start browse daemon first (see ~/.claude/skills/browse/llms.txt)
curl -s -X POST http://127.0.0.1:$PORT/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "fetch https://docs.example.com/api/webhooks"}'
# Returns: { ok, url, title, text }
```

Never use the built-in WebFetch tool for content extraction — it returns raw HTML overhead and cannot handle JS-rendered pages.

## Documentation
- Public functions need docstrings
- Complex logic needs inline explanation of WHY
- Exported types need JSDoc or equivalent
