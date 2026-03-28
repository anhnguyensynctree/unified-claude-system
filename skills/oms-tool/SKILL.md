# /oms-tool — System Improvement via External Research

Researches external tools, papers, articles, or repos and compares them against the full unified Claude system to find gaps worth improving.

## Usage
```
/oms-tool                        # scan GitHub + Reddit + HN this week, find candidates, evaluate top hits
/oms-tool <url>                  # evaluate a specific repo, article, or paper
/oms-tool <url1> <url2>          # evaluate multiple sources together
```

---

## Step 0 — Map the full unified Claude system

Before fetching anything external, read the complete system. This is the baseline everything gets compared against.

**Claude Code layer** (how Claude itself operates):
1. `~/.claude/CLAUDE.md` — tools table, Switching Modes, all active rules
2. `~/.claude/rules/patterns.md` — code patterns, fetch approach, API conventions
3. `~/.claude/rules/agents.md` — agent delegation model, model selection
4. `~/.claude/rules/performance.md` — token budget, ctx-exec, bun-exec usage
5. List `~/.claude/bin/` — every script/tool available
6. List `~/.claude/skills/` — every skill available

**OMS orchestration layer** (the autonomous AI company):
7. `~/.claude/oms-overview.md` — **the full OMS ecosystem**: mental model, all entry points, discussion pipeline, tier system, company hierarchy, task lifecycle, Discord integration, learning loop, key files. This is the single source of truth for understanding the whole system.
8. `~/.claude/agents/router/persona.md` — **the orchestration brain**: read this immediately after the overview. The router is the conductor — it classifies every task, selects agents, sets tier, and builds agent_briefings. Any improvement that touches routing, agent activation, or briefing construction must be evaluated here first.

Build a system map before proceeding:

```
## Current system map

### Claude Code tools
- External URL fetching: [tool + trigger rule]
- Parallel API calls: [tool + when]
- Large output filtering: [tool + when]
- Skills available: [list]
- Bin scripts: [list]

### OMS orchestration
- Discussion pipeline: [steps 1–8 from overview]
- Router logic: [how it classifies, what it activates, how briefings are built]
- Tier system: [0–3, agent caps, round caps]
- Task lifecycle: [feature draft → queue → worktree → done/cto-stop]
- Escalation path: [CEO gate, when it blocks]
- Feedback loop: [trainer → lessons → shared-lessons → future rounds]
- Learning quality: [training scenarios, nightly run]
- Discord wiring: [what triggers what]

### Known constraints or gaps
- [anything currently limited or absent]
```

Read the overview first for the big picture, then the router for how the system actually routes decisions. Everything else (individual personas, SKILL.md implementation detail) is consulted only if the source material is relevant to that specific agent or step.

---

## Step 1 — Get source material

**If URL(s) provided:**
Use `browse fetch <url>` for each URL. Extract content as clean text.

**If no URL provided — run radar scan:**
Write `/tmp/radar-fetch.ts` and run with `~/.claude/bin/bun-exec.sh`:

```typescript
const KEYWORDS = ['llm', 'claude', 'mcp', 'ai-agents', 'autonomous-agents', 'llm-tools'];
const REDDIT_SUBS = ['LocalLLaMA', 'ClaudeAI', 'LLMDevs', 'MachineLearning', 'SideProject'];
const weekAgo = new Date(Date.now() - 7 * 86400 * 1000);
const weekAgoStr = weekAgo.toISOString().slice(0, 10);
const weekTs = Math.floor(weekAgo.getTime() / 1000);

const [ghRaw, ...rest] = await Promise.all([
  fetch(
    `https://api.github.com/search/repositories?q=${KEYWORDS.slice(0,5).join('+')}+stars:>30+created:>${weekAgoStr}&sort=stars&order=desc&per_page=8`,
    { headers: { Accept: 'application/vnd.github.v3+json', 'User-Agent': 'oms-radar/1.0' } }
  ).then(r => r.json()).catch(() => ({ items: [] })),
  ...REDDIT_SUBS.slice(0,4).map(sub =>
    fetch(`https://www.reddit.com/r/${sub}/hot.json?limit=8`, { headers: { 'User-Agent': 'oms-radar/1.0' } })
      .then(r => r.json()).catch(() => ({ data: { children: [] } }))
  ),
  fetch(`https://hn.algolia.com/api/v1/search?query=show+hn+llm+agent+claude&tags=show_hn&hitsPerPage=6&numericFilters=created_at_i>${weekTs}`)
    .then(r => r.json()).catch(() => ({ hits: [] })),
]);
const hnRaw = rest.pop() as any;
const redditRaw = rest;

const gh = (ghRaw.items || []).slice(0, 6).map((r: any) => ({
  name: r.full_name, url: r.html_url, stars: r.stargazers_count,
  desc: (r.description || '').slice(0, 100), topics: (r.topics || []).slice(0, 4),
}));

const kws = new Set(['claude', 'llm', 'agent', 'open-source', 'tool', 'mcp', 'rag']);
const reddit: any[] = [];
redditRaw.forEach((raw: any, i: number) => {
  for (const c of (raw?.data?.children || [])) {
    const p = c.data;
    if ([...kws].some(k => p.title?.toLowerCase().includes(k)))
      reddit.push({ title: p.title, url: `https://reddit.com${p.permalink}`, score: p.score, sub: REDDIT_SUBS[i] });
  }
});
reddit.sort((a, b) => b.score - a.score);

const hn = (hnRaw?.hits || []).slice(0, 4).map((h: any) => ({ title: h.title, url: h.url || '', points: h.points || 0 }));

console.log(JSON.stringify({ data: { gh, reddit: reddit.slice(0,5), hn }, error: null }));
```

**Pre-screen the radar results against our current system map** (from Step 0).
Classify each result: `→ investigate` / `→ already covered` / `→ not relevant`

Show the list with classifications, then pick the top 1-3 `→ investigate` items. Use `browse fetch <url>` to fetch their content.

---

## Step 2 — Extract what's genuinely novel

For each source (URL or radar pick), read the content and extract only what matters:

```
## [Tool / Article name]

### Core mechanism
[How it actually works — the technique, not the pitch]

### Problem it solves
[What breaks without this — specific, not vague]

### Key design choices
- [specific decision 1 and why it matters]
- [specific decision 2]

### Evidence
[benchmarks / community adoption / comparisons — or "none found"]
```

Discard: marketing copy, feature lists, install noise, boilerplate.

---

## Step 3 — Gap analysis against our system

Compare the extracted innovations against the current system map from Step 0.

For each innovation:

| What they do | What we do | Gap? |
|---|---|---|
| [specific mechanism] | [our current approach + file] | none / partial / missing |

Then synthesize:

```
## Gaps worth improving
- **[gap name]**: they [do X], we [do Y via file Z], gap because [concrete reason]
  Effort: low / medium / high
  Impact: low / medium / high

## Already covered
- [innovation] → we handle this via [tool/file]

## Not applicable
- [innovation] → doesn't fit our setup because [reason]
```

Only flag gaps that are:
- Concretely better (not just different)
- Applicable to our stack (Python, TypeScript, Claude Code, OMS)
- Worth the implementation cost

---

## Step 4 — Propose improvements

For each gap rated worth improving:

```
## Proposed improvement: [name]

What changes: [exact file(s)]
How: [1-2 sentences on approach]
Minimal version: [smallest thing that delivers the value]
Risk: [what could break or regress]
```

---

## Step 5 — Decision

```
## Summary

Sources reviewed: [N]
Gaps found: [N worth improving] / [N already covered] / [N not applicable]

Top improvement (highest impact/effort):
→ [name]: [one sentence]

Implement? (yes / pick / skip)
  yes   = implement top improvement now
  pick  = list all, you choose
  skip  = stop here
```

Wait for confirmation. If yes or pick: implement via standard dev flow (read → edit → verify). No files written before confirmation.

---

## Step 6 — Update oms-overview.md (if anything changed)

After any implementation completes, check whether `~/.claude/oms-overview.md` needs updating:

- New workflow or command added → update Entry Points section
- Agent added, removed, or renamed → update Company Hierarchy section
- Discussion pipeline changed (steps, tiers, round caps) → update Open Discussion Format section
- New tool wired into Claude Code layer → update Key Files or Mental Model section
- Discord integration changed → update Discord Integration section
- Learning/quality loop changed → update Learning & Quality section

If nothing in the OMS system changed (e.g. improvement was Claude Code tooling only, not OMS orchestration) → skip this step.

Update the `Last updated:` date at the top of the file.

Do not add a section for the source tool/article itself — only update what actually changed in our system.
