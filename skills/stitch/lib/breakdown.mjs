/**
 * Splits a compound prompt into individual named screens.
 * e.g. "full app: login, dashboard, settings" → [{name:"login", prompt:...}, ...]
 */

const SCREEN_SPLIT_PATTERNS = [
  // "full app: login, dashboard, settings"
  /(?:full app|screens?|pages?|views?)\s*[:—]\s*(.+)/i,
  // "login page, dashboard page, settings page"
  /^(.+(?:page|screen|view).+,.+(?:page|screen|view).*)$/i,
];

const SCREEN_NOUNS = [
  "login", "signin", "sign-in", "signup", "sign-up", "register", "onboarding",
  "dashboard", "home", "landing", "index",
  "settings", "preferences", "profile", "account",
  "checkout", "cart", "payment", "billing",
  "inbox", "messages", "chat", "notifications",
  "search", "results", "explore", "discover",
  "detail", "single", "item", "product",
  "list", "overview", "summary", "report",
  "admin", "cms", "editor", "builder",
  "404", "error", "empty", "loading",
];

/**
 * Returns array of {name, prompt} objects.
 * Single-screen prompts return [{name: slugified, prompt}].
 */
export function breakdownPrompt(rawPrompt) {
  // Check for explicit multi-screen syntax
  for (const pattern of SCREEN_SPLIT_PATTERNS) {
    const match = rawPrompt.match(pattern);
    if (match) {
      const parts = match[1].split(/[,;]+/).map((s) => s.trim()).filter(Boolean);
      if (parts.length > 1) {
        return parts.map((part) => ({
          name: slugify(part),
          prompt: enrichPrompt(part, rawPrompt),
        }));
      }
    }
  }

  // Check if prompt mentions multiple screen nouns
  const foundNouns = SCREEN_NOUNS.filter((noun) =>
    new RegExp(`\\b${noun}\\b`, "i").test(rawPrompt)
  );
  if (foundNouns.length > 1) {
    return foundNouns.map((noun) => ({
      name: noun,
      prompt: enrichPrompt(noun, rawPrompt),
    }));
  }

  // Single screen — derive name from prompt
  const name = foundNouns[0] ?? slugify(rawPrompt.split(" ").slice(0, 3).join(" "));
  return [{ name, prompt: rawPrompt }];
}

function enrichPrompt(screenName, fullPrompt) {
  // If original prompt has global context (colors, style), prepend it
  const styleHints = fullPrompt.match(
    /(?:dark|light|minimal|modern|clean|flat|material|glassmorphism|neumorphism|tailwind|bootstrap).+/i
  );
  const base = `${screenName} screen`;
  return styleHints ? `${base} — ${styleHints[0]}` : base;
}

function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);
}
