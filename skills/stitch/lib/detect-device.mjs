import fs from "fs";
import path from "path";

const MOBILE_KEYWORDS = [
  "mobile", "ios", "android", "react native", "expo", "capacitor",
  "flutter", "native app", "phone", "smartphone"
];
const TABLET_KEYWORDS = ["tablet", "ipad"];
const DESKTOP_KEYWORDS = [
  "desktop", "web app", "dashboard", "admin", "next.js", "nextjs",
  "remix", "vite", "nuxt", "saas", "portal", "cms"
];
const MOBILE_DEPS = ["react-native", "expo", "@capacitor/core", "flutter"];
const DESKTOP_DEPS = ["next", "remix", "vite", "nuxt", "@nuxtjs/nuxt"];

/**
 * Detect device type from project context.
 * Priority: manifest default → package.json deps → CLAUDE.md keywords → fallback DESKTOP
 */
export function detectDevice(projectRoot) {
  // 1. Check existing manifest default
  const manifestPath = path.join(projectRoot, "design/stitch/manifest.json");
  if (fs.existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      if (manifest.defaultDevice) return manifest.defaultDevice;
    } catch {}
  }

  // 2. Check package.json deps
  const pkgPath = path.join(projectRoot, "package.json");
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
      const deps = Object.keys({
        ...(pkg.dependencies ?? {}),
        ...(pkg.devDependencies ?? {}),
      }).map((d) => d.toLowerCase());
      if (MOBILE_DEPS.some((d) => deps.includes(d))) return "MOBILE";
      if (DESKTOP_DEPS.some((d) => deps.some((dep) => dep.includes(d)))) return "DESKTOP";
    } catch {}
  }

  // 3. Check CLAUDE.md keywords
  const claudeMdPath = path.join(projectRoot, ".claude/CLAUDE.md");
  if (fs.existsSync(claudeMdPath)) {
    const content = fs.readFileSync(claudeMdPath, "utf8").toLowerCase();
    if (TABLET_KEYWORDS.some((k) => content.includes(k))) return "TABLET";
    if (MOBILE_KEYWORDS.some((k) => content.includes(k))) return "MOBILE";
    if (DESKTOP_KEYWORDS.some((k) => content.includes(k))) return "DESKTOP";
  }

  return "DESKTOP";
}
