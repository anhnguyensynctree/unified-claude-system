import type { ContextEntry } from "./state";

export function flushErrors<T>(buffer: T[]): T[] {
  const copy = [...buffer];
  buffer.length = 0;
  return copy;
}

export async function buildResponse(
  data: Record<string, unknown>,
  ctx?: ContextEntry,
): Promise<Record<string, unknown>> {
  const base: Record<string, unknown> = { ok: true, ...data };

  if (!ctx) return base;

  const page = ctx.pages[ctx.activeTab];
  base.page = { url: page.url(), title: await page.title() };

  const consoleErrors = flushErrors(ctx.consoleErrors);
  const networkErrors = flushErrors(ctx.networkErrors);
  if (consoleErrors.length > 0) base.new_console_errors = consoleErrors;
  if (networkErrors.length > 0) base.new_network_errors = networkErrors;

  try {
    base.interactive = await page.evaluate(() => ({
      inputs: document.querySelectorAll("input, textarea, select").length,
      buttons: document.querySelectorAll("button, [role=button], [type=submit]")
        .length,
      links: document.querySelectorAll("a[href]").length,
      forms: document.querySelectorAll("form").length,
    }));
  } catch {
    // Non-HTML page — skip interactive summary
  }

  return base;
}

export function translateError(e: Error): string {
  const msg = e.message;
  if (msg.includes("Timeout"))
    return "Timeout — element not found or navigation stalled. Check selector or page load state.";
  if (msg.includes("strict mode"))
    return "Multiple elements match selector. Use a more specific selector or nth-child.";
  if (msg.includes("not visible"))
    return "Element exists but is not visible. It may be hidden or off-screen.";
  if (msg.includes("net::ERR"))
    return `Network error: ${msg.split("net::ERR")[1]?.split("\n")[0] ?? msg}`;
  return msg;
}
