import { chromium } from "playwright";
import { randomUUID } from "crypto";
import { writeFileSync } from "fs";
import {
  browse,
  createContext,
  ensureScreenshotsDir,
  ensureVideosDir,
  STATE_FILE,
} from "./state";
import { executeCommand, executeBatch } from "./commands";

const IDLE_TIMEOUT = parseInt(process.env.BROWSE_IDLE_TIMEOUT ?? "1800000"); // 30min default

let idleTimer: ReturnType<typeof setTimeout>;

function resetIdle() {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(shutdown, IDLE_TIMEOUT);
}

async function shutdown() {
  for (const entry of browse.contexts.values()) {
    await entry.context.close().catch(() => {});
  }
  await browse.browser.close().catch(() => {});
  try {
    Bun.unlinkSync(STATE_FILE);
  } catch {}
  process.exit(0);
}

async function main() {
  ensureScreenshotsDir();
  ensureVideosDir();

  browse.browser = await chromium.launch({ headless: true });
  await createContext("default");

  const token = randomUUID();

  const server = Bun.serve({
    port: parseInt(process.env.BROWSE_PORT ?? "0"),
    async fetch(req) {
      const url = new URL(req.url);

      if (url.pathname === "/health") {
        return Response.json({
          ok: true,
          contexts: [...browse.contexts.keys()],
          active: browse.active,
          pid: process.pid,
        });
      }

      const auth = req.headers.get("authorization");
      if (auth !== `Bearer ${token}`) {
        return Response.json(
          { ok: false, error: "Unauthorized" },
          { status: 401 },
        );
      }

      resetIdle();

      if (url.pathname === "/stop" && req.method === "POST") {
        setTimeout(shutdown, 100);
        return Response.json({ ok: true, message: "Shutting down" });
      }

      if (url.pathname === "/command" && req.method === "POST") {
        try {
          const body = (await req.json()) as {
            command?: string;
            commands?: string[];
            context?: string;
          };

          if (body.context && browse.contexts.has(body.context)) {
            browse.active = body.context;
          }

          if (body.commands) {
            return Response.json(await executeBatch(body.commands));
          }

          if (body.command) {
            return Response.json(await executeCommand(body.command));
          }

          return Response.json(
            {
              ok: false,
              error: "Provide 'command' (string) or 'commands' (array)",
            },
            { status: 400 },
          );
        } catch (e: any) {
          return Response.json(
            { ok: false, error: e.message },
            { status: 500 },
          );
        }
      }

      return Response.json({ ok: false, error: "Not found" }, { status: 404 });
    },
  });

  writeFileSync(
    STATE_FILE,
    JSON.stringify({ port: server.port, token, pid: process.pid }),
    {
      mode: 0o600,
    },
  );

  console.log(
    `Browse daemon started — port ${server.port} | pid ${process.pid}`,
  );
  console.log(`State: ${STATE_FILE}`);

  resetIdle();
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);
}

main().catch((e) => {
  console.error("Browse daemon failed to start:", e);
  process.exit(1);
});
