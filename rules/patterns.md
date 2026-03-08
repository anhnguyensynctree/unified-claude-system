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

## Documentation
- Public functions need docstrings
- Complex logic needs inline explanation of WHY
- Exported types need JSDoc or equivalent
