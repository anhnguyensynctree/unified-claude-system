import { join } from "path";
import {
  browse,
  activePage,
  activeCtx,
  createContext,
  attachListeners,
  SCREENSHOTS_DIR,
  VIDEOS_DIR,
  ensureVideosDir,
} from "./state";
import { buildResponse, flushErrors, translateError } from "./shaper";

function parseCommand(input: string): { cmd: string; args: string[] } {
  const parts: string[] = [];
  let current = "";
  let inQuote = false;

  for (const char of input.trim()) {
    if (char === '"' && !inQuote) {
      inQuote = true;
      continue;
    }
    if (char === '"' && inQuote) {
      inQuote = false;
      continue;
    }
    if (char === " " && !inQuote) {
      if (current) {
        parts.push(current);
        current = "";
      }
    } else {
      current += char;
    }
  }
  if (current) parts.push(current);

  return { cmd: parts[0] ?? "", args: parts.slice(1) };
}

export async function executeCommand(
  input: string,
): Promise<Record<string, unknown>> {
  const { cmd, args } = parseCommand(input);
  const page = activePage();
  const ctx = activeCtx();

  try {
    switch (cmd) {
      // ── Context management ──────────────────────────────────────────────
      case "ctx:create": {
        const name = args[0] ?? `ctx-${Date.now()}`;
        await createContext(name);
        browse.active = name;
        return buildResponse({ created: name, active: name });
      }
      case "ctx:list":
        return buildResponse({
          contexts: [...browse.contexts.keys()],
          active: browse.active,
        });
      case "ctx:switch": {
        const name = args[0];
        if (!browse.contexts.has(name))
          return { ok: false, error: `Context '${name}' not found` };
        browse.active = name;
        return buildResponse({ active: name }, activeCtx());
      }
      case "ctx:destroy": {
        const name = args[0];
        if (name === "default")
          return { ok: false, error: "Cannot destroy default context" };
        const entry = browse.contexts.get(name);
        if (!entry) return { ok: false, error: `Context '${name}' not found` };
        await entry.context.close();
        browse.contexts.delete(name);
        if (browse.active === name) browse.active = "default";
        return buildResponse({ destroyed: name });
      }

      // ── Navigation ──────────────────────────────────────────────────────
      case "go": {
        const url = args[0];
        if (!url) return { ok: false, error: "go requires a URL" };
        await page.goto(url.startsWith("http") ? url : `https://${url}`);
        await page.waitForLoadState("networkidle").catch(() => {});
        return buildResponse({ navigated: url }, ctx);
      }
      case "reload":
        await page.reload();
        await page.waitForLoadState("networkidle").catch(() => {});
        return buildResponse({ reloaded: true }, ctx);
      case "back":
        await page.goBack();
        await page.waitForLoadState("networkidle").catch(() => {});
        return buildResponse({ navigated: "back" }, ctx);
      case "forward":
        await page.goForward();
        await page.waitForLoadState("networkidle").catch(() => {});
        return buildResponse({ navigated: "forward" }, ctx);

      // ── Interaction ──────────────────────────────────────────────────────
      case "click": {
        const sel = args[0];
        if (!sel) return { ok: false, error: "click requires a selector" };
        await page.click(sel);
        await page
          .waitForLoadState("networkidle", { timeout: 3000 })
          .catch(() => {});
        return buildResponse({ clicked: sel }, ctx);
      }
      case "fill": {
        const [sel, ...rest] = args;
        const value = rest.join(" ");
        if (!sel || value === undefined)
          return { ok: false, error: "fill requires selector and value" };
        await page.fill(sel, value);
        return buildResponse({ filled: sel, value }, ctx);
      }
      case "select": {
        const [sel, value] = args;
        if (!sel || !value)
          return { ok: false, error: "select requires selector and value" };
        await page.selectOption(sel, value);
        return buildResponse({ selected: sel, value }, ctx);
      }
      case "hover":
        await page.hover(args[0]);
        return buildResponse({ hovered: args[0] }, ctx);
      case "key":
        await page.keyboard.press(args.join("+"));
        await page
          .waitForLoadState("networkidle", { timeout: 2000 })
          .catch(() => {});
        return buildResponse({ pressed: args.join("+") }, ctx);
      case "scroll": {
        const target = args[0] ?? "bottom";
        if (target === "top") await page.evaluate(() => window.scrollTo(0, 0));
        else if (target === "bottom")
          await page.evaluate(() =>
            window.scrollTo(0, document.body.scrollHeight),
          );
        else await page.locator(target).scrollIntoViewIfNeeded();
        return buildResponse({ scrolled: target }, ctx);
      }

      // ── Reading ──────────────────────────────────────────────────────────
      case "screenshot":
      case "screenshot:full": {
        // args[0] optional: absolute path or relative path (resolved from cwd)
        let screenshotPath: string;
        if (args[0]) {
          screenshotPath = args[0].startsWith("/")
            ? args[0]
            : join(process.cwd(), args[0]);
          // ensure parent dir exists
          const { mkdirSync: mkdir, existsSync: exists } = await import("fs");
          const parent = screenshotPath.substring(
            0,
            screenshotPath.lastIndexOf("/"),
          );
          if (parent && !exists(parent)) mkdir(parent, { recursive: true });
        } else {
          const filename = `screenshot-${Date.now()}${cmd === "screenshot:full" ? "-full" : ""}.png`;
          screenshotPath = join(SCREENSHOTS_DIR, filename);
        }
        await page.screenshot({
          path: screenshotPath,
          fullPage: cmd === "screenshot:full",
        });
        return buildResponse(
          {
            screenshot: screenshotPath,
            hint: `Use Read tool on this path to display the image`,
          },
          ctx,
        );
      }
      case "text":
        return buildResponse({ text: await page.innerText("body") }, ctx);
      case "html": {
        const html = await page.innerHTML(args[0] ?? "body");
        return buildResponse({ html: html.slice(0, 5000) }, ctx);
      }
      case "console-errors": {
        const errors = flushErrors(ctx.consoleErrors);
        return { ok: true, console_errors: errors, count: errors.length };
      }
      case "network-errors": {
        const errors = flushErrors(ctx.networkErrors);
        return { ok: true, network_errors: errors, count: errors.length };
      }

      // ── Inspection ───────────────────────────────────────────────────────
      case "exists":
        return { ok: true, exists: (await page.locator(args[0]).count()) > 0 };
      case "visible":
        return {
          ok: true,
          visible: await page
            .locator(args[0])
            .isVisible()
            .catch(() => false),
        };
      case "value":
        return buildResponse({ value: await page.inputValue(args[0]) }, ctx);
      case "attr":
        return buildResponse(
          { value: await page.getAttribute(args[0], args[1]) },
          ctx,
        );
      case "count":
        return { ok: true, count: await page.locator(args[0]).count() };

      // ── Viewport ─────────────────────────────────────────────────────────
      case "viewport": {
        const [w, h] = args.map(Number);
        if (!w || !h)
          return { ok: false, error: "viewport requires width and height" };
        await page.setViewportSize({ width: w, height: h });
        return buildResponse({ viewport: { width: w, height: h } }, ctx);
      }

      // ── Tabs ──────────────────────────────────────────────────────────────
      case "new-tab": {
        const newPage = await ctx.context.newPage();
        ctx.pages.push(newPage);
        ctx.activeTab = ctx.pages.length - 1;
        attachListeners(browse.active, newPage);
        if (args[0]) {
          await newPage.goto(
            args[0].startsWith("http") ? args[0] : `https://${args[0]}`,
          );
          await newPage.waitForLoadState("networkidle").catch(() => {});
        }
        return buildResponse({ tab: ctx.activeTab }, ctx);
      }
      case "switch-tab": {
        const idx = parseInt(args[0]);
        if (isNaN(idx) || idx < 0 || idx >= ctx.pages.length) {
          return {
            ok: false,
            error: `Tab ${args[0]} not found. Tabs: 0–${ctx.pages.length - 1}`,
          };
        }
        ctx.activeTab = idx;
        return buildResponse({ active_tab: idx }, ctx);
      }
      case "close-tab": {
        if (ctx.pages.length === 1)
          return { ok: false, error: "Cannot close last tab" };
        await ctx.pages[ctx.activeTab].close();
        ctx.pages.splice(ctx.activeTab, 1);
        ctx.activeTab = Math.max(0, ctx.activeTab - 1);
        return buildResponse({ active_tab: ctx.activeTab }, ctx);
      }
      case "tabs": {
        const tabs = await Promise.all(
          ctx.pages.map(async (p, i) => ({
            index: i,
            url: p.url(),
            title: await p.title(),
          })),
        );
        return { ok: true, tabs };
      }

      // ── Video recording ──────────────────────────────────────────────────
      case "record:start": {
        if (browse.recording) {
          return {
            ok: false,
            error: `Already recording in context '${browse.recording.contextName}'. Run record:stop first.`,
          };
        }
        // args[0] optional name/path. If absolute or contains /, use as dir; else use VIDEOS_DIR
        const recName = args[0] ?? `rec-${Date.now()}`;
        let videoDir: string;
        if (recName.startsWith("/")) {
          videoDir = recName;
        } else if (recName.includes("/")) {
          videoDir = join(process.cwd(), recName);
        } else {
          videoDir = VIDEOS_DIR;
        }
        const { mkdirSync: mkdirV, existsSync: existsV } = await import("fs");
        if (!existsV(videoDir)) mkdirV(videoDir, { recursive: true });
        const recCtxName = `__rec__${recName.replace(/\//g, "-")}`;
        const recContext = await browse.browser.newContext({
          recordVideo: { dir: videoDir },
        });
        const recPage = await recContext.newPage();
        const recEntry = {
          context: recContext,
          pages: [recPage],
          activeTab: 0,
          consoleErrors: [],
          networkErrors: [],
        };
        browse.contexts.set(recCtxName, recEntry);
        attachListeners(recCtxName, recPage);
        browse.active = recCtxName;
        browse.recording = { contextName: recCtxName, recordingPage: recPage };
        return buildResponse(
          { recording: recName, context: recCtxName },
          recEntry,
        );
      }

      case "record:stop": {
        if (!browse.recording) {
          return {
            ok: false,
            error: "No active recording. Run record:start first.",
          };
        }
        const { contextName, recordingPage } = browse.recording;
        const recEntry = browse.contexts.get(contextName);
        if (!recEntry) {
          browse.recording = null;
          return { ok: false, error: "Recording context not found." };
        }
        // Save video path reference before closing
        const videoRef = recordingPage.video();
        // Close all pages to flush video, then close context
        for (const p of recEntry.pages) {
          await p.close().catch(() => {});
        }
        await recEntry.context.close().catch(() => {});
        const videoPath = await videoRef?.path().catch(() => null);
        browse.contexts.delete(contextName);
        browse.recording = null;
        // Switch back to default
        browse.active = "default";
        return {
          ok: true,
          video: videoPath ?? null,
          hint: videoPath
            ? "Use Read tool with this path to attach video to task log"
            : "Video path unavailable — context may not have recorded any frames",
        };
      }

      // ── Meta ──────────────────────────────────────────────────────────────
      case "status":
        return {
          ok: true,
          contexts: [...browse.contexts.keys()],
          active: browse.active,
          url: page.url(),
          title: await page.title(),
          tab: ctx.activeTab,
          tabs: ctx.pages.length,
          recording: browse.recording ? browse.recording.contextName : null,
        };

      case "eval": {
        // eval <js expression> — evaluate JS in page context, returns result as JSON
        const js = args.join(" ");
        if (!js) return { ok: false, error: "eval requires a JS expression" };
        const result = await page.evaluate((code) => {
          try {
            // eslint-disable-next-line no-new-func
            return { value: Function(`"use strict"; return (${code})`)() };
          } catch (e) {
            return { error: String(e) };
          }
        }, js);
        return buildResponse({ result }, ctx);
      }

      // ── Content extraction ────────────────────────────────────────────────
      case "fetch": {
        // fetch <url> — load URL in ephemeral isolated context, return clean text
        // Does NOT affect the active browse session or any existing context.
        const fetchUrl = args[0];
        if (!fetchUrl) return { ok: false, error: "fetch requires a URL" };
        const target = fetchUrl.startsWith("http")
          ? fetchUrl
          : `https://${fetchUrl}`;
        const fetchCtx = await browse.browser.newContext();
        const fetchPage = await fetchCtx.newPage();
        try {
          const resp = await fetchPage
            .goto(target, { waitUntil: "networkidle", timeout: 20000 })
            .catch(() => null);
          if (!resp) return { ok: false, error: `Failed to load ${target}` };

          const extracted = await fetchPage.evaluate(() => {
            const noise = [
              "script",
              "style",
              "nav",
              "header",
              "footer",
              "aside",
              "[role=navigation]",
              "[role=banner]",
              "[role=contentinfo]",
            ];
            noise.forEach((sel) =>
              document.querySelectorAll(sel).forEach((el) => el.remove()),
            );
            const main = (document.querySelector(
              "article, main, [role=main], .content, #content, .post-content, .article-body",
            ) ?? document.body) as HTMLElement;
            return {
              title: document.title,
              text: main.innerText.replace(/\n{3,}/g, "\n\n").trim(),
            };
          });

          return {
            ok: true,
            url: fetchPage.url(),
            title: extracted.title,
            text: extracted.text,
          };
        } finally {
          await fetchPage.close().catch(() => {});
          await fetchCtx.close().catch(() => {});
        }
      }

      default:
        return {
          ok: false,
          error: `Unknown command: '${cmd}'. Run 'status' for current state. Available: go, reload, back, forward, click, fill, select, hover, key, scroll, screenshot, screenshot:full, text, html, fetch, console-errors, network-errors, exists, visible, value, attr, count, viewport, new-tab, switch-tab, close-tab, tabs, ctx:create, ctx:list, ctx:switch, ctx:destroy, record:start, record:stop, status, eval`,
        };
    }
  } catch (e) {
    return { ok: false, error: translateError(e as Error) };
  }
}

export async function executeBatch(
  commands: string[],
): Promise<Record<string, unknown>> {
  const results: Record<string, unknown>[] = [];

  for (const cmd of commands) {
    const result = await executeCommand(cmd);
    results.push({ command: cmd, ...result });
    if (!(result as any).ok) break; // stop batch on first error
  }

  return {
    ok: results.every((r) => (r as any).ok),
    results,
    total: commands.length,
    executed: results.length,
  };
}
