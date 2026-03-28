import fs from "fs";
import path from "path";
import os from "os";

// Stitch generation can take up to 10 minutes per screen
const TIMEOUT_MS = 700_000;
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 5_000;

function loadApiKey() {
  if (process.env.STITCH_API_KEY) return process.env.STITCH_API_KEY;
  const keyFile = path.join(os.homedir(), ".config/stitch/key");
  if (fs.existsSync(keyFile)) return fs.readFileSync(keyFile, "utf8").trim();
  throw new Error("Stitch API key not found. Set STITCH_API_KEY or create ~/.config/stitch/key");
}

/**
 * Create a single authenticated StitchToolClient + Stitch domain instance.
 * All operations share this client so timeout and auth are consistent.
 */
async function getStitchInstance() {
  const { StitchToolClient, Stitch } = await import("@google/stitch-sdk");
  const client = new StitchToolClient({
    apiKey: loadApiKey(),
    baseUrl: "https://stitch.googleapis.com/mcp",
    timeout: TIMEOUT_MS,
  });
  return { client, stitchApi: new Stitch(client) };
}

/**
 * Retry wrapper for Stitch API calls that may timeout or return transient errors.
 */
async function withRetry(fn, label) {
  let lastErr;
  for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const msg = err.message ?? "";
      // Retry on: timeouts, rate limits, and the Stitch SDK "screens is undefined"
      // crash which occurs when the API returns a partial/unexpected response shape
      const isTransient =
        msg.includes("timed out") ||
        msg.includes("timeout") ||
        msg.includes("screens") ||
        err.code === -32001 ||
        err.code === "RATE_LIMITED" ||
        err.code === "STITCH_NO_DESIGN";
      if (!isTransient || attempt > MAX_RETRIES) break;
      const delay = RETRY_DELAY_MS * attempt;
      console.log(`[stitch] ${label} failed (attempt ${attempt}/${MAX_RETRIES + 1}): ${msg} — retrying in ${delay / 1000}s...`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastErr;
}

/**
 * Generate a new screen. Returns { id, htmlUrl, imageUrl, projectId }.
 *
 * On fresh projects, the Stitch API's first `generate_screen_from_text` call
 * returns design-system initialization components (no `design.screens`).
 * We call callTool directly so we can detect this early and retry before the
 * SDK crashes with "Cannot read properties of undefined (reading 'screens')".
 */
export async function generate({ prompt, deviceType = "DESKTOP", projectId }) {
  const { client, stitchApi } = await getStitchInstance();

  try {
    const proj = projectId
      ? stitchApi.project(projectId)
      : await stitchApi.createProject(path.basename(process.cwd()));

    const resolvedProjectId = proj.id;

    const screen = await withRetry(async () => {
      const raw = await client.callTool("generate_screen_from_text", {
        projectId: resolvedProjectId,
        prompt,
        deviceType,
      });

      // Find the component that contains the actual screen design
      const designComponent = (raw.outputComponents ?? []).find((c) => c.design?.screens?.length > 0);
      if (!designComponent) {
        // API returned init/system components without a screen — retryable
        const types = (raw.outputComponents ?? []).map((c) => Object.keys(c)[0]).join(", ");
        throw Object.assign(
          new Error(`generate_screen_from_text returned no design component (got: ${types}) — screens is undefined`),
          { code: "STITCH_NO_DESIGN" }
        );
      }

      const screenData = { ...designComponent.design.screens[0], projectId: resolvedProjectId };
      const { Screen } = await import("@google/stitch-sdk");
      return new Screen(client, screenData);
    }, "generate");

    return {
      id: screen.screenId ?? screen.id,
      projectId: screen.projectId ?? resolvedProjectId,
      htmlUrl: await screen.getHtml(),
      imageUrl: await screen.getImage(),
    };
  } finally {
    await client.close().catch(() => {});
  }
}

/**
 * Edit an existing screen. Returns { id, htmlUrl, imageUrl }.
 */
export async function edit({ screenId, projectId, prompt, deviceType, modelId }) {
  const { client, stitchApi } = await getStitchInstance();

  try {
    const screen = await stitchApi.project(projectId).getScreen(screenId);
    const updated = await withRetry(
      () => screen.edit(prompt, deviceType, modelId),
      "edit"
    );
    return {
      id: updated.screenId ?? updated.id,
      projectId: updated.projectId ?? projectId,
      htmlUrl: await updated.getHtml(),
      imageUrl: await updated.getImage(),
    };
  } finally {
    await client.close().catch(() => {});
  }
}

/**
 * Generate variants of an existing screen.
 * creativeRange: "REFINE" | "EXPLORE" | "REIMAGINE"
 */
export async function generateVariants({ screenId, projectId, prompt, count = 3, creativeRange = "EXPLORE", aspects }) {
  const { client, stitchApi } = await getStitchInstance();

  try {
    const screen = await stitchApi.project(projectId).getScreen(screenId);
    const variantOptions = { variantCount: count, creativeRange };
    if (aspects) variantOptions.aspects = aspects;
    const variants = await withRetry(
      () => screen.variants(prompt, variantOptions),
      "variants"
    );
    return Promise.all(
      variants.map(async (v) => ({
        id: v.screenId ?? v.id,
        projectId: v.projectId ?? projectId,
        htmlUrl: await v.getHtml(),
        imageUrl: await v.getImage(),
      }))
    );
  } finally {
    await client.close().catch(() => {});
  }
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
