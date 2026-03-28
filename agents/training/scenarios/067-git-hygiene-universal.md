# Scenario 067 — Git Hygiene — Universal Pre-Commit Gate (Tier 1)

**Difficulty**: Basic
**Primary failure mode tested**: Impl agent or oms-work commit step allows build artifacts, dependency directories, or sensitive files into the git index on any task type — not just scaffold tasks.
**Criteria tested**: IQ1, IQ2, IQ3

## What This Scenario Covers

Three failure modes, all caught by the same universal pre-commit gate:

| Case | Task Type | Bad Files | Criteria |
|---|---|---|---|
| A | Scaffold / init | `node_modules/`, `.next/`, `dist/` | IQ1 |
| B | Test / coverage | `coverage/` | IQ2 |
| C | Any task | `.env` with real values, files >500KB | IQ3 |

All three are blocked by the same check — not task-type detection, not keyword scanning. The gate runs on every commit.

---

## Case A — Scaffold Missing Gitignore

### Synthetic CEO Intent
> "Initialize the project scaffold — Next.js 14, TypeScript, Tailwind. Create the base app layout, a stub landing page, and Tailwind config. Dev server should start clean on localhost:3000."

### Setup
Scaffold task spec lists 6 source artifacts. No `.gitignore` listed. Impl agent runs `pnpm install`.

### Expected Behavior
- Impl agent recognises project initialization requires `.gitignore` even if spec omits it
- `.gitignore` created before first commit, covering: `node_modules/`, `.next/`, `coverage/`, `*.tsbuildinfo`, `.env`, `.env.local`
- Pre-commit gate runs: `git ls-files | grep -E "^node_modules/|^\.next/|^dist/"` → empty → commit proceeds

### Failure Signal
- `git ls-files | grep node_modules` returns results → IQ1 fail
- Human must run `git rm --cached` to recover → observable corrective action = IQ1 fail

---

## Case B — Test Task Commits Coverage

### Synthetic CEO Intent
> "Write unit tests for the classify route and output templates. 80% coverage minimum."

### Setup
Test task runs `vitest --coverage`. No `.gitignore` entry for `coverage/`. Coverage report written to `coverage/` dir.

### Expected Behavior
- Dev validator runs `git ls-files | grep -E "^coverage/"` before passing → returns empty → PASS
- If `coverage/` is present without gitignore entry: dev validator fires IQ2 FAIL before commit runs
- Pre-commit gate catches it as second safety net

### Failure Signal
- `coverage/*.html`, `coverage/clover.xml`, etc. appear in `git ls-files` → IQ2 fail

---

## Case C — Sensitive or Oversized File Staged

### Synthetic CEO Intent
> "Add environment variable configuration for the LLM fallback classifier."

### Setup
Task creates `.env` with real `ANTHROPIC_API_KEY` value and a reference dataset file (800KB) alongside it.

### Expected Behavior
- Pre-commit gate checks `.env` files — blocks `.env` (not `.env.example`) from being staged
- Pre-commit gate checks file sizes — blocks any file >500KB
- Task marked CTO-STOP, not DONE, until the issue is resolved

### Failure Signal
- `.env` with non-placeholder value in `git ls-files` → IQ3 fail
- File >500KB in staged diff → IQ3 fail

---

## Universal Pass Conditions (all tasks, all projects)

These checks run on every oms-work commit regardless of task type:

```bash
# IQ1/IQ2 — no build/dependency dirs tracked
git ls-files | grep -qE "^node_modules/|^\.next/|^dist/|^out/|^coverage/|^\.pnpm-store/" && FAIL

# IQ3 — no .env with real values staged (allow .env.example)
git diff --cached --name-only | grep -qE "^\.env$|^\.env\." | grep -qv "example" && FAIL

# IQ3 — no files over 500KB
git diff --cached --name-only | while read f; do
  [ -f "$f" ] && [ $(wc -c < "$f") -gt 512000 ] && FAIL
done
```

All three checks must return clean. Any failure → CTO-STOP, not DONE.

---

## Trainer Evaluation Focus

IQ1/IQ2/IQ3 are not task-type-conditional. Trainer must run the universal gate checks after every impl task regardless of what the task spec says. A validator that passes without running `git ls-files` has not completed their check.

The dev validator citation for any IQ failure: "git ls-files returned [path] — pre-commit gate should have blocked this — IQ[N] fail."
