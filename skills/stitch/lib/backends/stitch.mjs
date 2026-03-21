import fs from "fs";
import path from "path";
import os from "os";

function loadApiKey() {
  if (process.env.STITCH_API_KEY) return process.env.STITCH_API_KEY;
  const keyFile = path.join(os.homedir(), ".config/stitch/key");
  if (fs.existsSync(keyFile)) return fs.readFileSync(keyFile, "utf8").trim();
  throw new Error("Stitch API key not found. Set STITCH_API_KEY or create ~/.config/stitch/key");
}

async function getClient() {
  const { StitchToolClient } = await import("@google/stitch-sdk");
  return new StitchToolClient({
    apiKey: loadApiKey(),
    baseUrl: "https://stitch.googleapis.com/mcp",
    timeout: 600_000,
  });
}

async function getStitch() {
  const { stitch } = await import("@google/stitch-sdk");
  // Inject API key before use
  process.env.STITCH_API_KEY = loadApiKey();
  return stitch;
}

/**
 * Generate a new screen. Returns { id, htmlUrl, imageUrl, projectId }.
 */
export async function generate({ prompt, deviceType = "DESKTOP", projectId }) {
  const stitchApi = await getStitch();
  const proj = projectId
    ? stitchApi.project(projectId)
    : await createProject();

  const screen = await proj.generate(prompt, deviceType);
  return {
    id: screen.screenId ?? screen.id,
    projectId: screen.projectId ?? proj.id,
    htmlUrl: await screen.getHtml(),
    imageUrl: await screen.getImage(),
  };
}

/**
 * Edit an existing screen. Returns { id, htmlUrl, imageUrl }.
 */
export async function edit({ screenId, projectId, prompt, deviceType, modelId }) {
  const stitchApi = await getStitch();
  const screen = await stitchApi.project(projectId).getScreen(screenId);
  const updated = await screen.edit(prompt, deviceType, modelId);
  return {
    id: updated.screenId ?? updated.id,
    projectId: updated.projectId ?? projectId,
    htmlUrl: await updated.getHtml(),
    imageUrl: await updated.getImage(),
  };
}

/**
 * Create a new Stitch project for this repo.
 */
async function createProject() {
  const client = await getClient();
  const result = await client.callTool("create_project", {
    title: path.basename(process.cwd()),
  });
  await client.close();
  // stitch SDK returns project object — extract id
  const id = result?.projectId ?? result?.id ?? result;
  const stitchApi = await getStitch();
  return stitchApi.project(id);
}

/**
 * Generate variants of an existing screen.
 * creativeRange: "REFINE" | "EXPLORE" | "REIMAGINE"
 *   REIMAGINE → early ideation, dramatic exploration
 *   EXPLORE   → moderate variation, finding direction (default)
 *   REFINE    → conservative, polishing a near-final layout
 * aspects: ["COLOR_SCHEME", "LAYOUT", "IMAGES", "TEXT_FONT", "TEXT_CONTENT"]
 */
export async function generateVariants({ screenId, projectId, prompt, count = 3, creativeRange = "EXPLORE", aspects }) {
  const stitchApi = await getStitch();
  const screen = await stitchApi.project(projectId).getScreen(screenId);
  const variantOptions = { variantCount: count, creativeRange };
  if (aspects) variantOptions.aspects = aspects;
  const variants = await screen.variants(prompt, variantOptions);
  return Promise.all(
    variants.map(async (v) => ({
      id: v.screenId ?? v.id,
      projectId: v.projectId ?? projectId,
      htmlUrl: await v.getHtml(),
      imageUrl: await v.getImage(),
    }))
  );
}

/**
 * Download content from a URL and save to disk.
 */
export async function downloadFile(url, destPath) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: ${res.status} ${url}`);
  const buffer = await res.arrayBuffer();
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  fs.writeFileSync(destPath, Buffer.from(buffer));
}
