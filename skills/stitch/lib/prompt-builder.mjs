/**
 * Prompt builder — enriches raw prompts with structured style context before sending to Stitch.
 *
 * Uses the canonical Stitch prompt format from google-labs-code/stitch-skills:
 *   [One-line vibe statement]
 *   DESIGN SYSTEM (REQUIRED): platform, theme, hex palette, typography, components
 *   PAGE STRUCTURE: numbered sections with explicit layout descriptions
 *
 * Stitch has no persistent style memory — context must be injected on every prompt.
 * Prompt limit: 4,500 chars (Stitch truncates at 5,000 and silently drops components).
 */

import fs from "fs";
import path from "path";

// Profile → atmosphere vocabulary (from stitch-skills/design-mappings.md)
const PROFILE_ATMOSPHERE = {
  marketing: {
    theme: "Light, editorial, expressive",
    defaultPalette: {
      background: "Clean White (#ffffff)",
      surface: "Off White (#fafafa) for section backgrounds",
      accent: "defined by brand — no default",
      textPrimary: "Near Black (#111827)",
      textSecondary: "Cool Gray (#6b7280)",
    },
    typography: "Expressive variable serif or Cabinet Grotesk for headlines; clean sans-serif for body",
    buttons: "Contextual — pill for CTAs, sharp-edge for secondary actions",
    cards: "Double-bezel feature cards, asymmetric layout, large hero imagery",
    notStyle: "not an equal-weight 3-column card grid as primary layout, not decorative radial gradient blobs, not generic pill buttons as the only variant",
  },
  product: {
    theme: "Light or Dark, modern minimal, focused",
    defaultPalette: {
      background: "Near White (#f9fafb) or Deep Slate (#0f172a) for dark",
      surface: "White (#ffffff) or Dark Card (#1e293b) for containers",
      accent: "defined by brand — no default",
      textPrimary: "Near Black (#111827) or White (#f8fafc)",
      textSecondary: "Medium Gray (#6b7280) or Muted Slate (#94a3b8)",
    },
    typography: "Geist or Satoshi for headings (500–700 weight); Geist Mono for code and data",
    buttons: "Subtly rounded (8px), precise, full interactive states",
    cards: "Gently rounded (12px), soft shadow, card-based grouping with whitespace hierarchy",
    notStyle: "not decorative scroll animations on functional UI, not eyebrow tags, not oversized section padding",
  },
  dense: {
    theme: "Light or Dark, functional minimal, zero decoration",
    defaultPalette: {
      background: "White (#ffffff) or Near Black (#0a0a0a)",
      surface: "Soft Gray (#f3f4f6) or Dark Surface (#18181b)",
      accent: "Single semantic accent — red/yellow/green for status only",
      textPrimary: "Near Black (#111827) or White (#fafafa)",
      textSecondary: "Muted Gray (#6b7280)",
    },
    typography: "Geist Mono for data columns and IDs; Geist for labels; legibility at 12–13px",
    buttons: "Sharp rounded (4–6px), compact, keyboard-first with visible focus rings",
    cards: "Ruled separators (divide-y) over cards; containers only where containment adds meaning",
    notStyle: "not spring animations, not gradient backgrounds, not pill buttons, not centered layouts, not cards wrapping every section",
  },
};

// Universal hard failures (from design-quality.md) — always injected
const HARD_FAILURES = [
  "no emoji in UI",
  "no gradient text on headlines",
  "no pure black #000000 — use near-black",
  "no decorative radial gradient blobs",
  "no AI purple/indigo defaults (#6366f1, #8b5cf6)",
  "no transition-all utility class",
];

// Vague → professional vocabulary replacements (from stitch-skills/design-mappings.md)
export const VOCAB_MAP = {
  "menu at top": "sticky navigation bar with logo left and nav items right",
  "big photo": "high-impact hero section with full-width imagery and overlay headline",
  "list of things": "responsive card grid with hover states and subtle elevation",
  "button": "primary call-to-action button with micro-interactions and active state",
  "form": "clean form with labeled input fields, validation states, and submit button",
  "sidebar": "collapsible side navigation with icon-label pairings and active highlight",
  "popup": "modal dialog with overlay and smooth entry animation",
  "dark mode": "electric, high-contrast accents on deep slate near-black backgrounds",
  "modern": "clean, minimal, generous whitespace and high-contrast typography",
  "professional": "sophisticated, trustworthy, subtle shadows, restricted premium palette",
  "luxury": "elegant, spacious, fine lines, serif headers, high-fidelity photography",
};

/**
 * Enriches a prompt for screen generation using the canonical Stitch structured format.
 *
 * Output format:
 *   [vibe statement]
 *   DESIGN SYSTEM (REQUIRED): ...
 *   PAGE STRUCTURE: 1. ... 2. ...
 */
export function buildGeneratePrompt(rawPrompt, styleConfig = {}, profile = "product") {
  const atmos = PROFILE_ATMOSPHERE[profile] ?? PROFILE_ATMOSPHERE.product;
  const pal = styleConfig.palette ?? atmos.defaultPalette;

  const lines = [];

  // ── Vibe statement (line 1) ──────────────────────────────────────────────
  const vibeBase = styleConfig.brandReference
    ? `${rawPrompt.trim()}. Design reference: ${styleConfig.brandReference}.`
    : rawPrompt.trim();
  const aesthetic = styleConfig.aestheticAnchor
    ? `${vibeBase} ${styleConfig.aestheticAnchor} aesthetic.`
    : vibeBase;
  lines.push(aesthetic);
  lines.push("");

  // ── DESIGN SYSTEM block ──────────────────────────────────────────────────
  lines.push("DESIGN SYSTEM (REQUIRED):");
  lines.push(`- Platform: ${styleConfig.platform ?? "Web, Desktop-first"}`);
  lines.push(`- Theme: ${styleConfig.theme ?? atmos.theme}`);
  lines.push(`- Background: ${pal.background ?? atmos.defaultPalette.background}`);
  lines.push(`- Surface: ${pal.surface ?? atmos.defaultPalette.surface}`);

  if (pal.accent) {
    lines.push(`- Primary Accent: ${pal.accent}`);
  } else if (styleConfig.colorPalette) {
    lines.push(`- Color Palette: ${styleConfig.colorPalette}`);
  }

  lines.push(`- Text Primary: ${pal.textPrimary ?? atmos.defaultPalette.textPrimary}`);
  lines.push(`- Text Secondary: ${pal.textSecondary ?? atmos.defaultPalette.textSecondary}`);
  lines.push(`- Typography: ${styleConfig.typography ?? atmos.typography}`);
  lines.push(`- Buttons: ${atmos.buttons}`);
  lines.push(`- Cards: ${atmos.cards}`);
  lines.push("");

  // ── Constraints ──────────────────────────────────────────────────────────
  const notStyle = [atmos.notStyle, ...HARD_FAILURES].join("; ");
  lines.push(`Avoid: ${notStyle}.`);

  if (styleConfig.notes) {
    lines.push(`Additional: ${styleConfig.notes}`);
  }

  const prompt = lines.join("\n");

  if (prompt.length > 4500) {
    console.warn(`[prompt-builder] Prompt ${prompt.length} chars — truncating to 4500`);
    return rawPrompt.trim().slice(0, 4500);
  }

  return prompt;
}

/**
 * Structured update prompt — one change only, with layout-preservation phrase.
 * From official Stitch community guide: never bundle unrelated changes.
 */
export function buildUpdatePrompt(rawPrompt, styleConfig = {}) {
  const lines = [];

  lines.push(rawPrompt.trim().replace(/\.$/, ""));
  lines.push("");
  lines.push("Specific changes:");
  lines.push(`- ${rawPrompt.trim()}`);

  if (styleConfig.colorPalette) {
    lines.push(`- Maintain existing color palette: ${styleConfig.colorPalette}`);
  }

  lines.push("");
  lines.push("Context: This is a targeted edit. Please refrain from altering any other functionalities or design elements.");

  return lines.join("\n");
}

/**
 * Reads styleConfig from manifest. Returns empty object if not set.
 */
export function getStyleConfig(manifest) {
  return manifest.styleConfig ?? {};
}

/**
 * Detects design-quality.md profile from project CLAUDE.md content.
 */
export function detectProfile(projectRoot) {
  const claudeMd = path.join(projectRoot, ".claude/CLAUDE.md");
  if (fs.existsSync(claudeMd)) {
    const content = fs.readFileSync(claudeMd, "utf8").toLowerCase();
    if (content.includes("landing page") || content.includes("marketing") || content.includes("promotional")) {
      return "marketing";
    }
    if (content.includes("admin") || content.includes("internal tool") || content.includes("developer tool") || content.includes("data-heavy")) {
      return "dense";
    }
  }
  return "product";
}
