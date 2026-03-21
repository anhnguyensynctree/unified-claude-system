# Design System Rules — Always Follow

## Source of Truth

`design/stitch/` is the canonical design system for every front-end project. It is generated and managed exclusively by the `/stitch` skill — never edited manually.

## Before Implementing Any UI

1. Check `design/stitch/manifest.json` — if a screen exists for the route or view you are building, open it
2. Extract colors, typography, spacing, and layout patterns from the generated HTML
3. Match component structure to the Stitch output — do not invent patterns that contradict it
4. If no screen exists for the view: generate one with `/stitch generate <description>` before writing component code

## Updating Designs

- Additive / mutative changes: use `/stitch update <name> <prompt>` — targets only the changed screen
- Structural changes: confirm before running — these regenerate the full layout
- After update: re-read the HTML and sync any affected components

## Folder Layout (per project)

```
design/
└── stitch/
    ├── manifest.json       # screen registry — source of truth for all screen IDs and versions
    ├── <name>.html         # latest generated HTML
    ├── <name>.png          # screenshot
    └── <name>.v<n>.html    # archived previous versions (never delete)
```

## Allowed File Operations

- Read: always allowed — reference freely during implementation
- Write: only via `/stitch` skill — never edit HTML files directly
- Delete: never — old versions are archives, not dead weight

## Device Types

Auto-detected per project: MOBILE / TABLET / DESKTOP / AGNOSTIC.
Override by setting `defaultDevice` in `design/stitch/manifest.json`.
Use AGNOSTIC only for component libraries with no target viewport.
