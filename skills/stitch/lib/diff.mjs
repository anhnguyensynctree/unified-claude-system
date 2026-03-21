/**
 * Classifies the nature of a prompt change against an existing screen.
 * Returns: "additive" | "mutative" | "structural" | "none"
 *
 * - additive:  new element added (button, section, field)
 * - mutative:  existing element modified (color, text, size)
 * - structural: layout changed (grid, columns, navigation)
 * - none:      prompts are identical
 */

const STRUCTURAL_KEYWORDS = [
  "layout", "grid", "columns", "sidebar", "navigation", "nav", "header", "footer",
  "split", "two-column", "three-column", "full-width", "responsive", "breakpoint",
  "restructure", "reorganize", "move", "rearrange", "swap",
];

const ADDITIVE_KEYWORDS = [
  "add", "include", "insert", "append", "new", "extra", "additional",
  "also", "plus", "with", "attach", "embed",
];

const MUTATIVE_KEYWORDS = [
  "change", "update", "modify", "replace", "edit", "fix", "adjust",
  "rename", "relabel", "recolor", "resize", "make", "set", "turn",
];

export function classifyChange(existingPrompt, newPrompt) {
  if (existingPrompt.trim() === newPrompt.trim()) return "none";

  const lower = newPrompt.toLowerCase();

  if (STRUCTURAL_KEYWORDS.some((k) => lower.includes(k))) return "structural";
  if (ADDITIVE_KEYWORDS.some((k) => lower.includes(k))) return "additive";
  if (MUTATIVE_KEYWORDS.some((k) => lower.includes(k))) return "mutative";

  // Fallback: check token overlap — low overlap = structural change
  const existingTokens = new Set(existingPrompt.toLowerCase().split(/\W+/));
  const newTokens = newPrompt.toLowerCase().split(/\W+/);
  const overlap = newTokens.filter((t) => existingTokens.has(t)).length;
  const overlapRatio = overlap / newTokens.length;

  if (overlapRatio < 0.3) return "structural";
  if (overlapRatio < 0.6) return "mutative";
  return "additive";
}

/**
 * Returns a human-readable summary of the change classification.
 */
export function describeChange(type) {
  switch (type) {
    case "additive":
      return "Additive change — will use targeted edit (fast)";
    case "mutative":
      return "Mutative change — will use targeted edit (fast)";
    case "structural":
      return "Structural change — layout will be regenerated (confirm before proceeding)";
    case "none":
      return "No change detected";
  }
}
