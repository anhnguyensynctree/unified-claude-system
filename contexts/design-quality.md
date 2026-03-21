# Design Quality Standards

## Quick Reference
- Two layers: universal constraints (always) + context profile — select one: `marketing` / `product` / `dense`
- Hard failures (any context): no emojis, no `transition-all`, no gradient text, no `ease-in`, no pure `#000000`
- All 4 interaction states required: loading (skeletal), empty (composed), error (inline), active (`scale-[0.97]`)
- Animation: `transform`/`opacity` only; `prefers-reduced-motion` must yield — no exceptions
- Spacing: 4px base grid — every value a multiple of 4; no arbitrary values

Applies alongside `ui-ux.md` for all frontend output. Two layers: universal constraints (always), context profiles (select one).

---

## Universal Constraints — Always Apply

### Hard Failures (any context)
- **Emojis:** never in code, markup, or alt text — use Phosphor/Radix icons or inline SVG
- **`transition-all`:** never as a utility class — always name the specific property (`transition-opacity`, `transition-transform`)
- **Gradient text:** no `bg-clip-text` gradient on headlines — decoration that obscures content
- **`ease-in` easing:** accelerates toward end — opposite of physical intuition, always wrong for UI
- **Animate layout properties:** never animate `top`, `left`, `width`, `height` — only `transform` and `opacity`
- **`backdrop-blur` on scrolling containers:** fixed/sticky elements only
- **`#000000` pure black:** use `zinc-950` or `gray-950` — pure black is harsh against any background
- **`will-change: transform` globally:** sparingly, only on actively animating elements

### Typography (any context)
- Minimum 3 font weights in use — 400 (body), 500–600 (UI labels), 700 (headlines); never just 400 + 700
- Headlines above `text-3xl`: always `tracking-tighter` — never default tracking on large type
- Body line-height `1.6–1.7` for reading; `1.2–1.3` for UI labels — never one value for both
- Warm and cool grays must not mix within the same project

### Color (any context)
- Max 1 accent color per project, saturation < 80%
- Shadows tinted to background hue — never `rgba(0,0,0,0.3)` generic drops
- No purple/blue AI aesthetic (`#6366f1`, `#8b5cf6`) — the default AI palette

### Spacing (any context)
- 4px base grid — every spacing value a multiple of 4 (4, 8, 12, 16, 24, 32, 48, 64) — no arbitrary values

### Interaction States — Mandatory on Every Component
- **Loading:** skeletal loader matching layout geometry — no generic spinners
- **Empty:** composed state showing how to populate data — not just "No data yet"
- **Error:** inline remediation text below the triggering element — not a toast for inline errors
- **Active/Tactile:** `scale-[0.97]` or `-translate-y-[1px]` on `:active` — instant tactile feedback

### Animation (any context)
- `ease-out` for enter/exit; `ease-in-out` for elements repositioning — never `ease-in`
- Never animate from `scale(0)` — start from `scale(0.95)` minimum
- `transform-origin` at the trigger location — dropdowns from button, tooltips from anchor, never center
- `@media (prefers-reduced-motion: reduce)`: all transitions must yield — no exceptions

### Z-index (any context)
- Systemic layers only: sticky nav, modals, overlays, tooltips — no ad hoc z-index stacking

---

## Context Profiles — Select One Per Task

Router selects profile from task context. When uncertain: `product`.

---

### Profile: `marketing`
*Landing pages, promotional pages, feature showcases*

**Permitted:**
- Expressive typography — Variable Serif on massive display headings, Satoshi/Cabinet Grotesk for body
- Centered hero layouts, large section padding (`py-24` minimum)
- Theatrical animation (300–600ms), scroll reveals with `IntersectionObserver` or Framer `whileInView`
- Spring physics: `type: "spring", stiffness: 100, damping: 20` for interactive elements
- Asymmetric grids, split-screen, zig-zag layouts above `md:`
- Double-bezel nested cards for feature highlights
- Eyebrow tags preceding major headings: `rounded-full px-3 py-1 text-[10px] uppercase tracking-[0.2em]`
- Stagger reveal on lists: `animation-delay: calc(var(--index) * 100ms)`
- Grain/noise overlays: `position: fixed; pointer-events: none` pseudo-element only

**Required:**
- Asymmetric layouts collapse to `w-full px-4 py-8` below 768px
- Max page width `max-w-7xl` or `max-w-[1400px] mx-auto`
- `min-h-[100dvh]` for full-height sections — never `h-screen`
- Font: Geist, Satoshi, Outfit, or Cabinet Grotesk — not Inter/Roboto/Arial

**Banned:**
- 3-column equal-weight card grid as primary layout structure
- Rounded-full pill buttons as the only button variant (use contextually)
- Decorative radial gradient blobs (`from-indigo-500/20 to-transparent`) as background texture

---

### Profile: `product`
*SaaS apps, dashboards with brand presence, consumer tools, onboarding flows*

**Permitted:**
- Motion as communication — state transitions 150–200ms, spring physics on draggable/interactive surfaces
- Moderate whitespace, card-based grouping where elevation communicates hierarchy
- One expressive font for headings (Geist, Satoshi); monospace for code/data
- Subtle color presence — accent color visible but not dominant

**Required:**
- Font: Geist + Geist Mono or Satoshi + JetBrains Mono
- Icons: Phosphor Light or Radix — not thick Lucide stroke-width-2
- Card radius size-appropriate — `rounded-xl` for large surfaces, `rounded-md` for inputs/badges — never uniform `rounded-2xl` everywhere
- State transitions: explicit property only — `transition-opacity duration-150`, never `transition-all`
- Buttons: `scale-[0.97]` on `:active` — no layout shift

**Banned:**
- `transition-all duration-300 ease-in-out` as a global utility
- Decorative scroll animations on functional UI elements (tables, forms, inputs)
- Eyebrow tags / double-bezel cards — marketing patterns in product context
- `py-24` section padding inside app layouts — use `py-6` to `py-12` maximum

---

### Profile: `dense`
*Admin panels, internal tools, developer tools, data-heavy dashboards, CLIs with web UI*

**Permitted:**
- Tables, `divide-y`, `border-t` separators instead of cards — cards only when containment adds meaning
- Tight spacing (`py-2`, `py-3`) — density is a feature, not a failure
- Muted palette — single semantic accent (red/yellow/green for status), neutral everything else
- Monospace font for data columns, code, IDs
- Keyboard-first patterns — focus rings, shortcut labels visible in UI

**Required:**
- Zero decorative animation — state changes via color/opacity only, `duration-100` maximum
- Font: Geist + Geist Mono — legibility at small sizes, not brand expression
- Right-aligned number columns with consistent width — never left-aligned numeric data
- Icons: Radix or Phosphor at size 16 — not decorative, functional only

**Banned:**
- Spring physics, scroll reveals, stagger animations — noise in a functional context
- Gradient backgrounds, grain overlays, radial blob textures
- Pill-shaped buttons — use `rounded-md` for compact action density
- Centered layouts — always left-anchored or full-width
- Cards wrapping every section — use negative space and ruled lines

---

## Stitch Prompt Engineering — Always Apply When Generating UI

Stitch has no persistent style memory. Style context must be injected into every prompt via `stitch init` + prompt-builder. The prompt-builder handles this automatically — these rules apply when you craft prompts manually.

### Canonical Prompt Format (from google-labs-code/stitch-skills)

```
[One-line vibe + purpose statement. Design reference: <brand>. <aesthetic> aesthetic.]

DESIGN SYSTEM (REQUIRED):
- Platform: Web, Desktop-first
- Theme: Light, modern minimal, focused
- Background: Descriptive Name (#hex)
- Surface: Descriptive Name (#hex) for containers
- Primary Accent: Descriptive Name (#hex) for CTAs and links
- Text Primary: Descriptive Name (#hex)
- Text Secondary: Descriptive Name (#hex)
- Typography: [font name + weight] for headings; [font] for body
- Buttons: [shape + radius], [interaction note]
- Cards: [radius + shadow description]

Avoid: [negative constraints]

PAGE STRUCTURE:
1. Header: [explicit layout description]
2. Hero Section: [headline + CTA]
3. [Section]: [component breakdown]
```

### Vocabulary: Vague → Professional

| Vague | Professional |
|---|---|
| "menu at top" | "sticky navigation bar with logo left and nav items right" |
| "big photo" | "high-impact hero section with full-width imagery and overlay headline" |
| "list of things" | "responsive card grid with hover states and subtle elevation" |
| "button" | "primary call-to-action button with micro-interactions and active state" |
| "sidebar" | "collapsible side navigation with icon-label pairings and active highlight" |
| "modern" | "clean, minimal, generous whitespace, high-contrast typography" |
| "professional" | "sophisticated, trustworthy, subtle shadows, restricted premium palette" |
| "luxury" | "elegant, spacious, fine lines, serif headers, high-fidelity photography" |
| "dark mode" | "electric, high-contrast accents on deep slate near-black backgrounds" |

### Aesthetic Anchors (encode color + type + mood simultaneously)
- `marketing`: `"editorial"`, `"Japandi"`, `"vibrant editorial"`, `"bold typographic"`
- `product`: `"modern minimal"`, `"dark minimal"`, `"warm professional"`, `"focused"`
- `dense`: `"functional minimal"`, `"developer-focused"`, `"monochrome precise"`

### Brand References (compressed style packages)
- `"similar to Linear"` — dark, focused, grid-based, strong type hierarchy
- `"similar to Notion"` — minimal, clean, monochrome, information-dense
- `"similar to Vercel"` — high-contrast dark, editorial, precise spacing
- `"similar to Stripe"` — clean, trustworthy, balanced color, premium

### Variants Workflow
```
REIMAGINE → early ideation, dramatic exploration (use first)
EXPLORE   → moderate variation, finding direction (default)
REFINE    → conservative polish of near-final layout
```
Usage: `stitch variants <screen> --range REIMAGINE --count 3`
Then promote the best with: `stitch update <screen> "<refinement>"`

### Update Rules (prevents full layout regeneration)
- One change per update prompt — never combine layout + content + style changes
- prompt-builder appends `"Please refrain from altering any other functionalities or design elements"` automatically
- Prompt limit: 4,500 chars (Stitch truncates at 5,000 and silently drops components)

## Pre-Output Checklist

- [ ] Profile selected: `marketing` / `product` / `dense`
- [ ] No universal hard failures present (gradient text, ease-in, transition-all, emoji in markup)
- [ ] All 4 interaction states defined: loading, empty, error, active
- [ ] `prefers-reduced-motion` respected — all transitions yield
- [ ] Font weight scale uses minimum 3 weights
- [ ] Animation via `transform` / `opacity` only
- [ ] `backdrop-blur` not on any scrolling container
- [ ] Profile-specific banned patterns absent
- [ ] Output reads as intentional design for its context — not a template
