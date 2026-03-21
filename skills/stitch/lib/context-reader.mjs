/**
 * Context reader — scans a project for documents that describe the product,
 * brand, or design intent, then extracts structured signals for the style proposer.
 *
 * Reads (in priority order):
 *   .claude/CLAUDE.md, README.md, PRD.md, docs/**, BRIEF.md, BRAND.md, package.json
 */

import fs from "fs";
import path from "path";

const MAX_FILE_SIZE = 8000; // chars — enough signal without overloading

const SEARCH_PATHS = [
  ".claude/CLAUDE.md",
  "CLAUDE.md",
  "README.md",
  "PRD.md",
  "BRIEF.md",
  "BRAND.md",
  "docs/PRD.md",
  "docs/product.md",
  "docs/brief.md",
  "docs/brand.md",
  "docs/design.md",
  "docs/requirements.md",
  "docs/overview.md",
  "package.json",
];

/**
 * Returns { files: [{path, content}], combined: string } for all found docs.
 */
export function readProjectContext(projectRoot) {
  const files = [];

  // Explicit paths first
  for (const rel of SEARCH_PATHS) {
    const abs = path.join(projectRoot, rel);
    if (fs.existsSync(abs)) {
      const raw = fs.readFileSync(abs, "utf8").slice(0, MAX_FILE_SIZE);
      files.push({ path: rel, content: raw });
    }
  }

  // Any remaining .md in docs/ not already included
  const docsDir = path.join(projectRoot, "docs");
  if (fs.existsSync(docsDir)) {
    for (const f of fs.readdirSync(docsDir)) {
      if (!f.endsWith(".md")) continue;
      const rel = `docs/${f}`;
      if (files.some((x) => x.path === rel)) continue;
      const abs = path.join(projectRoot, rel);
      const raw = fs.readFileSync(abs, "utf8").slice(0, MAX_FILE_SIZE);
      files.push({ path: rel, content: raw });
    }
  }

  const combined = files.map((f) => `### ${f.path}\n${f.content}`).join("\n\n");
  return { files, combined };
}

/**
 * Extracts raw signals from combined document text.
 * Returns a plain object — no LLM call, purely pattern-based.
 */
export function extractSignals(combined) {
  const text = combined.toLowerCase();

  return {
    // Product type
    isMobile: /mobile|ios|android|react native|expo|flutter|capacitor/.test(text),
    isMarketing: /landing page|marketing|promotional|campaign|waitlist|sign.?up page/.test(text),
    isDense: /admin|internal tool|developer tool|data.heavy|analytics|dashboard|cms|backoffice/.test(text),

    // Audience & tone
    isPremium: /luxury|premium|high.end|exclusive|bespoke|boutique|prestige/.test(text),
    isPlayful: /playful|fun|kids|children|casual|friendly|vibrant/.test(text),
    isEnterprise: /enterprise|b2b|corporate|compliance|security|saas/.test(text),
    isTech: /developer|technical|cli|api|open.?source|engineering/.test(text),
    isCreative: /creative|design|art|portfolio|studio|agency/.test(text),

    // Color mentions (crude extraction)
    colorMentions: extractColorMentions(combined),

    // Brand/design references mentioned
    brandMentions: extractBrandMentions(text),

    // Product name (from package.json name or first heading)
    productName: extractProductName(combined),

    // Existing tech stack
    hasNextJs: /next\.js|nextjs/.test(text),
    hasReactNative: /react.native|expo/.test(text),
    hasTailwind: /tailwind/.test(text),

    // Raw keywords (first 20 unique meaningful words from headings)
    headingKeywords: extractHeadingKeywords(combined),
  };
}

function extractColorMentions(text) {
  const colors = [];
  const hexMatches = text.match(/#[0-9a-f]{3,6}\b/gi) ?? [];
  const namedColors = text.match(/\b(navy|teal|emerald|slate|amber|rose|indigo|violet|orange|forest green|sky blue|warm gray|charcoal|ivory|cream|sage|terracotta|cobalt)\b/gi) ?? [];
  return [...new Set([...hexMatches, ...namedColors])].slice(0, 6);
}

function extractBrandMentions(text) {
  const brands = [
    "linear", "notion", "figma", "vercel", "stripe", "github", "railway",
    "loom", "slack", "airbnb", "shopify", "framer", "apple", "google",
  ];
  return brands.filter((b) => text.includes(b));
}

function extractProductName(combined) {
  // From package.json name field
  const pkgMatch = combined.match(/"name":\s*"([^"]+)"/);
  if (pkgMatch) return pkgMatch[1];
  // From first # heading
  const headingMatch = combined.match(/^#\s+(.+)$/m);
  if (headingMatch) return headingMatch[1].trim();
  return null;
}

function extractHeadingKeywords(combined) {
  const headings = combined.match(/^#{1,3}\s+(.+)$/gm) ?? [];
  const words = headings
    .flatMap((h) => h.replace(/^#+\s*/, "").toLowerCase().split(/\W+/))
    .filter((w) => w.length > 3 && !STOP_WORDS.has(w));
  return [...new Set(words)].slice(0, 20);
}

const STOP_WORDS = new Set([
  "this", "that", "with", "from", "have", "will", "your", "their",
  "they", "what", "when", "where", "which", "about", "more", "also",
  "section", "page", "screen", "component", "feature", "overview",
]);
