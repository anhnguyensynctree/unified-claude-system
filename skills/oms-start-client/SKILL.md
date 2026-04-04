---
name: oms-start-client
description: Initialize a new client marketing site from the client-marketing-template. Runs research, populates all config + ctx files, and hands off to the OMS agent team.
---

# Skill: oms-start-client

Bootstraps a new client marketing project. Faster than `/oms-start` because the stack, section architecture, media system, and task queue are pre-built in the template. You provide the client basics — the skill handles the rest.

## When to Use
Starting any new client website project: construction, salon, restaurant, retail, blog, portfolio, or any local business.
Not for internal tools, SaaS products, or projects that need custom architecture — use `/oms-start` for those.

## Step 1 — Collect Minimum Input

Ask for only what cannot be researched:

```
Client name:      [business name]
City / location:  [city, state]
Primary goal:     [ get calls ] [ get bookings ] [ show our work ] [ just need a site ]
Google Drive:     [folder URL — or "not yet"]
Anything to know: [optional free text]
```

Accept answers in any format — numbered list, sentence, one word. Do not re-ask.
If the user says "go" or provides no extra context: proceed with research defaults.

## Step 2 — Research Pass (parallel agents)

Run research agent and web fetcher in parallel. Given only name + city, find:

| Source | Extract |
|---|---|
| Google Business Profile | Category, phone, address, hours, rating, review snippets |
| Existing website (if any) | Colors, copy tone, services listed, missing sections |
| Instagram / Facebook | Visual style, caption language, hashtags, engagement |
| Yelp / industry directories | Services, customer language in reviews, pain points praised |
| Top 2 competitors (same city) | What they lead with, what they're missing |

Output: `client-profile.json` saved to the new project root. Fields:
```json
{
  "business": { "name", "industry", "tagline", "phone", "address", "website", "email" },
  "researchFindings": { "competitorGaps", "customerLanguage", "localKeywords", "visualInspiration" },
  "tokenPresetRecommendation": "warm-earthy",
  "tokenPresetReason": "Restaurant industry, warm review language, earthy Instagram aesthetic",
  "confidence": { "tagline": "inferred", "colors": "found", "services": "found" }
}
```

Low-confidence fields get a reasonable default — never block on them.

## Step 3 — Token Preset Selection

Auto-select from `design/tokens/` based on industry + visual research.
If the user specified a preference in Step 1: override with their choice.

Show the selection in one line:
```
Preset: warm-earthy — matches restaurant industry + earthy tones found on Instagram
```

Do not ask for confirmation unless research was inconclusive (confidence: "none" on both industry and visual).

## Step 4 — Clone Template + Run init-client

```bash
# 1. Copy template to new project directory
cp -r ~/.claude/templates/client-marketing-template ~/code/clients/[client-slug]
cd ~/code/clients/[client-slug]

# 2. Write client-intake.json from research findings
# (generated from client-profile.json + Step 1 answers)

# 3. Run init-client
pnpm init:client
```

`init-client.ts` generates:
- `apps/web/config/client.ts` — CLIENT const with all business data + section config
- `apps/web/config/tokens.ts` — active preset re-export
- `apps/web/app/globals.css` — CSS vars from preset
- `.claude/agents/*.ctx.md` — all OMS context files populated
- `.claude/agents/cleared-queue.md` — M1–M4 task queue with client name + variants filled in

## Step 5 — Section Configuration

Based on the client's goal + industry, set enabled sections and choose variants:

| Goal | Recommended sections |
|---|---|
| leads | hero + about + services + testimonials + contact |
| bookings | hero + about + services + gallery + testimonials + contact |
| portfolio | hero + about + gallery + portfolio + testimonials + contact |
| credibility | hero + about + services + process + testimonials + contact |
| replace-site | hero + about + services + gallery + testimonials + contact |

Variant C (creative) is the default for: photography, editorial, fashion, art.
Variant A (safe) is the default for: construction, legal, finance, medical.
Variant B (standard) is the default for: everything else.

## Step 6 — Confirm + Hand Off to OMS

Output a single summary:

```
✓ Client project initialised: [Client Name]
  Location:  ~/code/clients/[client-slug]
  Preset:    [preset name] ([reason])
  Sections:  [list of enabled sections with variants]
  Drive:     [linked / not yet — run pnpm sync:media when ready]
  Queue:     11 tasks across M1–M4 ready in cleared-queue.md

Next: run /oms-work to start M1 tasks.
```

Then immediately trigger `/oms-work` — do not wait for CEO input.

## Step 7 — Research Findings → ctx files

After `/oms-work` picks up M1, the research agent reads `client-profile.json` and appends findings to:
- `research.ctx.md` — competitor gaps, customer language, local keywords
- `company-belief.ctx.md` — operating belief refined from real review language

This runs async during M1 — Engineering does not wait for it.

## Rules
- Never ask more than 5 questions total — research handles the rest
- Never block on Drive folder — media is M3, not M1
- Template path: `~/.claude/templates/client-marketing-template/`
- Client projects path: `~/code/clients/[client-slug]/`
- Slug: lowercase, hyphens, no spaces (e.g., "pho-saigon-88", "nails-by-lisa")
- Always run `/oms-work` at the end — do not leave the CEO with a queue and no momentum
- If the template does not exist at the expected path: tell CEO to clone it first
