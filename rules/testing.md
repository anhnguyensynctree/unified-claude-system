# Testing Rules — Always Follow

## Quick Reference
- TDD: RED → GREEN → IMPROVE. Never write implementation before tests.
- 80% coverage minimum. Every public function + every error path tested.
- Done = implementation + tests + tests passing. No exceptions.
- Unit: components, hooks, utils | Integration: API routes, contracts | E2E: user flows (5 categories)

## E2E User Inputs — Always Realistic, Always Non-Technical
All E2E test inputs must read like a real end user typed them — never placeholder text, never developer shorthand.

**Rules:**
- Inputs describe a real-world goal with current situation context: "I run a [type of business/activity] and want to [goal] — currently [current state]"
- No technical jargon, no product internals (e.g. never "tune my model", "optimize CTR", "run inference")
- useCase strings (mock API responses) must also be plain language: "reduce cart abandonment for small online shop", not "optimize conversion funnel"
- One consistent user persona per spec file — don't mix different scenarios across tests in the same file

**Examples of good inputs:**
- `"I run a small online shop and want to understand why customers add items to their cart but don't complete the purchase — I get around 80 visitors a day"`
- `"I teach yoga classes and want more students to rebook after their first session — about 3 out of 10 come back"`
- `"I write a weekly newsletter and want to understand why people unsubscribe after the first email — I have about 600 subscribers"`

**Examples of bad inputs (never use):**
- `"tune my model"`, `"optimize CTR"`, `"run training pipeline"`, `"download training data"`

## Test Type by Artifact
| Artifact | Test Type | What to Cover |
|---|---|---|
| UI component | Unit (React Testing Library) | renders, user interactions, conditional states |
| Hook | Unit | return values, state transitions, side effects |
| Service / utility | Unit | all branches, edge cases, error paths |
| API route / controller | Integration | request/response, auth, validation, error codes |
| API shape | Contract (vitest) | response matches Zod/Pydantic schema |
| Critical user flow | E2E (Playwright) | all 5 categories below |
| Auth project | Security E2E | auth bypass, session expiry, roles, XSS, CSRF |
| Critical flow (real) | Smoke E2E | real backend, no mocks |

## E2E — One File Per Flow
```
e2e/
  auth-login.spec.ts
  checkout.spec.ts
  disputes.spec.ts
e2e/smoke/
  auth.smoke.ts          # real backend, no mocks
  listing-crud.smoke.ts
security.spec.ts         # auth bypass, XSS, CSRF, roles
```
File naming: `e2e/<flow>.spec.ts`. Write when: new page/route, navigation path changed, form submission, URL param contract, auth/payment flow.

## E2E Coverage — 5 Categories Per Spec
| # | Category | Example |
|---|---|---|
| 1 | Happy path | Login → OTP → dashboard |
| 2 | Error states | 500, 422, network timeout → error UI |
| 3 | Empty state | No data → empty state component |
| 4 | Auth edge | Expired session → login redirect |
| 5 | Input edge | 200-char name → truncated, not broken |

All 5 as `test.describe` blocks. If one doesn't apply, add a comment — never silently skip:
```typescript
// N/A (auth edge): this product has no authentication
// N/A (empty state): API always returns at least a fallback — no empty render path
```

**Enforcement rules — always apply when writing E2E specs:**
- Every `e2e/*.spec.ts` must contain exactly 5 `test.describe` blocks, or a `// N/A` comment for each missing one
- N/A categories must surface to the CEO in the milestone briefing — list them under "Skipped E2E categories" with reasons
- When creating a new spec, start from this skeleton and fill every block before marking the task done:

```typescript
test.describe('1 — happy path', () => { ... })
test.describe('2 — error states', () => { ... })
test.describe('3 — empty state', () => { ... })
// N/A (4 — auth edge): no auth in this product
test.describe('5 — input edge', () => { ... })
```

- OMS task specs must reference this skeleton explicitly in their Spec field
- CI: add a grep check `grep -r "test.describe" e2e/ | wc -l` — if a spec has fewer than 3 describes and no N/A comments, flag it in the PR

## Smoke Tests — Real Backend
Mocked e2e proves UI works. Smoke tests prove the system works.
- One smoke spec per critical flow (auth, CRUD, payments) — hits real backend, no mocks
- Lives in `e2e/smoke/`, uses staging/test environment
- Runs at milestone gate + post-deploy only (too slow for dev)
- Smoke fails + e2e passes → config/infra bug, not UI bug

## Contract Tests
- One test per API endpoint: validates response shape matches frontend schema
- Vitest, no browser — fast. Lives in `src/__tests__/contracts/`
- Backend schema changes → contract test fails → frontend updates before merge

## Visual QA — Screenshots in E2E (required for all UI flows)

Every E2E spec that tests a UI page **must** call `page.screenshot()` at key states and save to `qa/screenshots/`. This is how visual QA runs automatically — no separate browse step, no manual trigger. Screenshots get posted to the Discord milestone thread by the milestone gate.

```typescript
test('login flow', async ({ page }) => {
  await page.goto('/login')
  await page.screenshot({ path: 'qa/screenshots/login-initial.png' })

  await page.fill('[name=email]', 'user@example.com')
  await page.fill('[name=password]', 'password')
  await page.click('[type=submit]')
  await page.waitForURL('/dashboard')
  await page.screenshot({ path: 'qa/screenshots/login-success.png' })
})
```

Screenshot naming: `qa/screenshots/<flow>-<state>.png`
- One screenshot per meaningful state: initial render, after interaction, error state, empty state
- `qa/screenshots/` must be in `.gitignore` — cleared before each milestone gate run, browse task screenshots only
- `qa/milestones/` must be in `.gitignore` — permanent archive of Playwright screenshots per milestone, not source

**Visual regression** — use `toHaveScreenshot()` for pixel-level drift detection:
```typescript
// Creates baseline on first run, diffs on every subsequent run
await expect(page).toHaveScreenshot('login-initial.png')
await page.fill('[name=password]', 'wrong')
await page.click('[type=submit]')
await expect(page).toHaveScreenshot('login-error.png')
```
Store baselines in `e2e/snapshots/` (committed). Run `playwright test --update-snapshots` only when intentionally changing UI.

**Coverage target:** every 5-category state must have at least one screenshot + `toHaveScreenshot()` call. Automated visual QA runs in both paths (Python milestone gate runs playwright, screenshots post to Discord). No manual step needed.

## E2E Speed
- **Cookie auth** — inject session via fixture, never login through UI (except auth spec)
- **Parallel workers** — `workers: 4` minimum, specs must be independent
- **Targeted runs** — `playwright test --grep "<flow>"` during dev, full suite at milestone
- **Centralized mocks** — one `mockRoutes()` in `e2e/fixtures.ts`, no inline mocking
- **No `waitForTimeout`** — use `waitForSelector`, `waitForURL`, `waitForResponse`

## Milestone Test Strategy
| Layer | Time | When |
|---|---|---|
| Unit + Contract | ~30s | Every task |
| E2E targeted | ~2-3 min | Every task |
| Visual QA Tier 1 | ~2 min | Every frontend task |
| E2E full suite | ~8-10 min | Milestone gate |
| Smoke tests | ~3-5 min | Milestone gate + post-deploy |
| Visual QA Tier 2 | ~10 min | Milestone gate |

All layers must pass at milestone gate. Fix and re-run on failure.

## Consistency-Critical Tasks
Auth, payments, data migrations, shared utils: 3 consecutive full suite passes (pass^3). Any failure → fix → restart count.

## Mock Stability — React Hooks
Mocks used in `useEffect` deps MUST be stable references:
```ts
// BAD — new object every render → infinite loop
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: mockPush }) }));
// GOOD — stable reference
const mockRouter = { push: mockPush, back: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => mockRouter }));
```

## Multi-file Shared Interface Edits — Always Apply
When a task modifies a shared type, interface, or contract used by N files:
1. Edit ALL N files first — no test runs between individual edits
2. ONE targeted run after all edits land: `vitest run file1.test.ts file2.test.ts ... fileN.test.ts`
3. Full suite only once at the very end — never between individual file edits

**Why:** Running the full suite after each file edit causes N redundant suite runs (expensive and fills context with noise). A shared interface change is atomic — all files must be consistent before any test is meaningful.

**Enforcement:** If you find yourself running `pnpm test` or `vitest run` after editing only 1 of N files that all import the changed interface → stop, finish the remaining edits first, then run.

## Test Quality
- Co-located with source or in `__tests__/` / `*.test.*`
- Names describe behavior: `it('returns null when unauthenticated')`
- One assertion concept per test
- Don't test: implementation details, third-party internals, generated code
