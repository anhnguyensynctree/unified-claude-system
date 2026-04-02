import { mkdirSync, existsSync } from "fs";
import { resolve } from "path";
import type { Browser, BrowserContext, Page } from "playwright";

export const SCREENSHOTS_DIR = resolve(process.cwd(), "qa/screenshots");
export const VIDEOS_DIR = resolve(process.cwd(), "qa/videos");
export const STATE_FILE = resolve(import.meta.dir, ".state.json");

export interface ContextEntry {
  context: BrowserContext;
  pages: Page[];
  activeTab: number;
  consoleErrors: Array<{ type: string; text: string; ts: number }>;
  networkErrors: Array<{
    url: string;
    status: number;
    method: string;
    ts: number;
  }>;
}

export interface RecordingState {
  contextName: string;
  recordingPage: Page;
}

export interface BrowseState {
  browser: Browser;
  contexts: Map<string, ContextEntry>;
  active: string;
  recording: RecordingState | null;
}

export const browse: BrowseState = {
  browser: null as any,
  contexts: new Map(),
  active: "default",
  recording: null,
};

export function activePage(): Page {
  const ctx = browse.contexts.get(browse.active)!;
  return ctx.pages[ctx.activeTab];
}

export function activeCtx(): ContextEntry {
  return browse.contexts.get(browse.active)!;
}

export function attachListeners(name: string, page: Page): void {
  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warn") {
      browse.contexts.get(name)?.consoleErrors.push({
        type: msg.type(),
        text: msg.text(),
        ts: Date.now(),
      });
    }
  });

  page.on("requestfailed", (req) => {
    browse.contexts.get(name)?.networkErrors.push({
      url: req.url(),
      status: -1,
      method: req.method(),
      ts: Date.now(),
    });
  });

  page.on("response", async (res) => {
    if (res.status() >= 400) {
      browse.contexts.get(name)?.networkErrors.push({
        url: res.url(),
        status: res.status(),
        method: res.request().method(),
        ts: Date.now(),
      });
    }
  });
}

export async function createContext(name: string): Promise<ContextEntry> {
  const context = await browse.browser.newContext();
  const page = await context.newPage();
  const entry: ContextEntry = {
    context,
    pages: [page],
    activeTab: 0,
    consoleErrors: [],
    networkErrors: [],
  };
  browse.contexts.set(name, entry);
  attachListeners(name, page);
  return entry;
}

export function ensureScreenshotsDir(): void {
  if (!existsSync(SCREENSHOTS_DIR))
    mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

export function ensureVideosDir(): void {
  if (!existsSync(VIDEOS_DIR)) mkdirSync(VIDEOS_DIR, { recursive: true });
}
