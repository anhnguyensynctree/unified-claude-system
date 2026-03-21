import fs from "fs";
import path from "path";

const MANIFEST_REL = "design/stitch/manifest.json";

export function manifestPath(projectRoot) {
  return path.join(projectRoot, MANIFEST_REL);
}

export function readManifest(projectRoot) {
  const p = manifestPath(projectRoot);
  if (!fs.existsSync(p)) {
    return { projectId: null, defaultDevice: "DESKTOP", screens: [] };
  }
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

export function writeManifest(projectRoot, manifest) {
  const p = manifestPath(projectRoot);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(manifest, null, 2));
}

export function findScreen(manifest, name) {
  return manifest.screens.find(
    (s) => s.name.toLowerCase() === name.toLowerCase()
  );
}

export function upsertScreen(manifest, screen) {
  const idx = manifest.screens.findIndex(
    (s) => s.name.toLowerCase() === screen.name.toLowerCase()
  );
  if (idx === -1) {
    manifest.screens.push(screen);
  } else {
    manifest.screens[idx] = screen;
  }
  return manifest;
}

export function buildScreenEntry({ id, name, prompt, deviceType, htmlPath, imagePath, version = 1 }) {
  return {
    id,
    name,
    prompt,
    deviceType,
    version,
    updatedAt: new Date().toISOString(),
    htmlPath,
    imagePath,
  };
}
