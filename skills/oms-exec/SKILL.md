# OMS Exec — Strategic Milestone Planning

Shorthand for `/oms exec`. C-suite selects the next milestone and produces FEATURE drafts ready for `/oms FEATURE-NNN` elaboration.

## Usage
```
/oms-exec                        # C-suite picks next milestone automatically
/oms-exec [milestone name]       # force a specific milestone
```

## Auto-selection behavior
CPO always proposes the next milestone — do NOT stop to ask CEO which milestone to plan. CPO reads:
1. `.claude/agents/product-direction.ctx.md` — milestone list + current status
2. `.claude/cleared-queue.md` — tasks already queued (to avoid duplicating covered work)

CPO selects the highest-priority milestone with no queued coverage and opens with: "Proposing [milestone]: [one-sentence rationale]." C-suite discusses, confirms or pivots, then proceeds.

New FEATURE blocks are **appended** to `cleared-queue.md` as `Status: draft` — never overwrite existing queued tasks.

## Behavior
Delegates to the `exec` mode in `~/.claude/skills/oms/SKILL.md`.

Load and follow all instructions under:
- **Executive Briefing** section — fires after Step 8.5; briefing file includes milestone chosen, features drafted, queue state
- **Exec Mode** section
- **Step 0** — skip the "queue has tasks → require milestone name" gate; auto-selection always runs
- **Steps 1–8.5** with `task_mode: exec`

Roster: CPO (lead), CTO, CRO, CLO, CFO — filtered to active departments per `.claude/agents/company-hierarchy.md`.

## Auto-proceed rule
When synthesis completes with no CEO escalation required — proceed to Step 8.5 automatically. Do NOT ask for confirmation. The only thing that stops the pipeline is an actual CEO escalation flag.

Output: FEATURE-NNN draft blocks appended to `cleared-queue.md`. End with list of features created and "Run /oms FEATURE-NNN to elaborate each into OpenSpec tasks."
