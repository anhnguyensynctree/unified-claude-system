#!/usr/bin/env node
/**
 * Stitch skill — AI UI generation with iterative update support.
 *
 * Usage:
 *   node stitch.mjs generate "a login page with email and password"
 *   node stitch.mjs update login "change button to blue"
 *   node stitch.mjs breakdown "full app: login, dashboard, settings"
 *   node stitch.mjs list
 *   node stitch.mjs status
 */

import path from "path";
import fs from "fs";
import { detectDevice } from "./lib/detect-device.mjs";
import { readManifest, writeManifest, findScreen, upsertScreen, buildScreenEntry } from "./lib/manifest.mjs";
import { breakdownPrompt } from "./lib/breakdown.mjs";
import { classifyChange, describeChange } from "./lib/diff.mjs";
import { generate, edit, generateVariants, downloadFile } from "./lib/backends/stitch.mjs";
import { buildGeneratePrompt, buildUpdatePrompt, getStyleConfig, detectProfile } from "./lib/prompt-builder.mjs";
import { readProjectContext, extractSignals } from "./lib/context-reader.mjs";
import { proposeStyleConfig } from "./lib/style-proposer.mjs";

const [,, command, ...args] = process.argv;

/**
 * Auto mode — Claude calls this when no explicit command is needed.
 * Detects: update (screen exists) | breakdown (multi-screen) | generate (default)
 * Usage: stitch auto "your intent" [screen-name-hint]
 */
async function cmdAuto(rawPrompt, screenHint) {
  if (!rawPrompt) fatal("Usage: stitch auto <prompt> [screen-name]");

  const manifest = readManifest(projectRoot);

  // 1. Explicit screen hint + exists in manifest → update
  if (screenHint) {
    const existing = findScreen(manifest, screenHint);
    if (existing) {
      console.log(`[auto] Found existing screen "${screenHint}" → update mode`);
      return cmdUpdate(screenHint, rawPrompt);
    }
  }

  // 2. Prompt references a known screen by name → update
  if (manifest.screens.length > 0) {
    const match = manifest.screens.find((s) =>
      new RegExp(`\\b${s.name}\\b`, "i").test(rawPrompt)
    );
    if (match) {
      console.log(`[auto] Detected existing screen "${match.name}" in prompt → update mode`);
      return cmdUpdate(match.name, rawPrompt);
    }
  }

  // 3. Multi-screen prompt → breakdown
  const screens = breakdownPrompt(rawPrompt);
  if (screens.length > 1) {
    console.log(`[auto] Multi-screen prompt detected (${screens.length} screens) → breakdown mode`);
    return cmdBreakdown(rawPrompt);
  }

  // 4. Default → generate
  console.log("[auto] New screen → generate mode");
  return cmdGenerate(rawPrompt);
}
const projectRoot = process.cwd();
const designDir = path.join(projectRoot, "design/stitch");

async function cmdGenerate(promptArg) {
  if (!promptArg) fatal("Usage: stitch generate <prompt>");

  const screens = breakdownPrompt(promptArg);
  const deviceType = detectDevice(projectRoot);
  const manifest = readManifest(projectRoot);
  const profile = detectProfile(projectRoot);
  const styleConfig = getStyleConfig(manifest);

  if (!manifest.defaultDevice) manifest.defaultDevice = deviceType;

  console.log(`Device: ${deviceType}  Profile: ${profile}`);
  console.log(`Screens to generate: ${screens.map((s) => s.name).join(", ")}`);

  for (const { name, prompt: rawScreenPrompt } of screens) {
    // Reuse existing screen via edit (cheaper) rather than full regenerate
    const existing = findScreen(manifest, name);
    if (existing) {
      console.log(`\n[generate] Screen "${name}" already exists (v${existing.version}) — routing to update to save cost`);
      await cmdUpdate(name, rawScreenPrompt);
      continue;
    }

    const enrichedPrompt = buildGeneratePrompt(rawScreenPrompt, styleConfig, profile);
    console.log(`\nGenerating "${name}"...`);
    if (process.env.STITCH_DEBUG) console.log(`[prompt] ${enrichedPrompt}`);
    const result = await generate({ prompt: enrichedPrompt, deviceType, projectId: manifest.projectId });

    if (!manifest.projectId) manifest.projectId = result.projectId;

    const htmlPath = `design/stitch/${name}.html`;
    const imagePath = `design/stitch/${name}.png`;

    await downloadFile(result.htmlUrl, path.join(projectRoot, htmlPath));
    await downloadFile(result.imageUrl, path.join(projectRoot, imagePath));

    upsertScreen(manifest, buildScreenEntry({
      id: result.id,
      name,
      prompt: rawScreenPrompt,
      deviceType,
      htmlPath,
      imagePath,
    }));

    writeManifest(projectRoot, manifest);
    console.log(`✓ ${name} → ${htmlPath}`);
  }
}

async function cmdUpdate(screenName, newPrompt) {
  if (!screenName || !newPrompt) fatal("Usage: stitch update <screen-name> <prompt>");

  const manifest = readManifest(projectRoot);
  const existing = findScreen(manifest, screenName);
  if (!existing) fatal(`Screen "${screenName}" not found in manifest. Run 'stitch list' to see available screens.`);

  const changeType = classifyChange(existing.prompt, newPrompt);
  console.log(describeChange(changeType));

  if (changeType === "none") {
    console.log("Nothing to do.");
    return;
  }

  if (changeType === "structural") {
    const confirmed = await confirm("Structural change detected — this will regenerate the layout. Continue? (y/N) ");
    if (!confirmed) { console.log("Aborted."); return; }
  }

  console.log(`\nUpdating "${screenName}"...`);

  // Archive previous version
  const prevHtml = path.join(projectRoot, existing.htmlPath);
  if (fs.existsSync(prevHtml)) {
    fs.copyFileSync(prevHtml, prevHtml.replace(".html", `.v${existing.version}.html`));
  }

  const styleConfig = getStyleConfig(manifest);
  const enrichedPrompt = buildUpdatePrompt(newPrompt, styleConfig);
  if (process.env.STITCH_DEBUG) console.log(`[prompt] ${enrichedPrompt}`);

  const result = await edit({
    screenId: existing.id,
    projectId: manifest.projectId,
    prompt: enrichedPrompt,
    deviceType: existing.deviceType,
  });

  await downloadFile(result.htmlUrl, path.join(projectRoot, existing.htmlPath));
  await downloadFile(result.imageUrl, path.join(projectRoot, existing.imagePath));

  upsertScreen(manifest, buildScreenEntry({
    ...existing,
    id: result.id,
    prompt: newPrompt,
    version: existing.version + 1,
  }));

  writeManifest(projectRoot, manifest);
  console.log(`✓ ${screenName} updated → v${existing.version + 1}`);
}

async function cmdBreakdown(promptArg) {
  if (!promptArg) fatal("Usage: stitch breakdown <compound-prompt>");
  const screens = breakdownPrompt(promptArg);
  console.log(`Breaking down into ${screens.length} screen(s):\n`);
  screens.forEach(({ name, prompt }) => console.log(`  • ${name}: ${prompt}`));
  console.log("\nProceed with generation? (y/N) ");
  const confirmed = await confirm("");
  if (confirmed) await cmdGenerate(promptArg);
}

function cmdList() {
  const manifest = readManifest(projectRoot);
  if (!manifest.screens.length) { console.log("No screens generated yet."); return; }
  console.log(`Project: ${manifest.projectId ?? "not initialized"}`);
  console.log(`Default device: ${manifest.defaultDevice}\n`);
  manifest.screens.forEach(({ name, deviceType, version, updatedAt, htmlPath }) => {
    console.log(`  ${name.padEnd(20)} v${version}  ${deviceType.padEnd(8)}  ${updatedAt?.slice(0, 10)}  ${htmlPath}`);
  });
}

function cmdStatus() {
  const manifest = readManifest(projectRoot);
  if (!manifest.screens.length) { console.log("No screens generated yet."); return; }
  console.log(`${manifest.screens.length} screen(s) tracked:\n`);
  manifest.screens.forEach(({ name, version, updatedAt }) => {
    const htmlFile = path.join(projectRoot, `design/stitch/${name}.html`);
    const exists = fs.existsSync(htmlFile);
    const state = exists ? "✓" : "✗ missing";
    console.log(`  ${state}  ${name}  (v${version}, updated ${updatedAt?.slice(0, 10)})`);
  });
}

/**
 * stitch variants — generate design explorations from an existing screen.
 *
 * Workflow (from official stitch-skills repo):
 *   REIMAGINE → early ideation, dramatic exploration
 *   EXPLORE   → moderate variation, finding direction (default)
 *   REFINE    → polishing a near-final layout
 *
 * Usage:
 *   stitch variants login --range REIMAGINE --count 3
 *   stitch variants dashboard --range REFINE --aspects COLOR_SCHEME,LAYOUT
 */
async function cmdVariants(screenName, rawArgs) {
  if (!screenName) fatal("Usage: stitch variants <screen-name> [--range REIMAGINE|EXPLORE|REFINE] [--count N] [--aspects LAYOUT,COLOR_SCHEME]");

  const manifest = readManifest(projectRoot);
  const existing = findScreen(manifest, screenName);
  if (!existing) fatal(`Screen "${screenName}" not found. Run 'stitch list'.`);

  // Parse flags
  let range = "EXPLORE";
  let count = 3;
  let aspects;
  for (let i = 0; i < rawArgs.length; i++) {
    if (rawArgs[i] === "--range" && rawArgs[i + 1]) { range = rawArgs[i + 1].toUpperCase(); i++; }
    if (rawArgs[i] === "--count" && rawArgs[i + 1]) { count = parseInt(rawArgs[i + 1], 10); i++; }
    if (rawArgs[i] === "--aspects" && rawArgs[i + 1]) { aspects = rawArgs[i + 1].split(","); i++; }
  }

  const rangeEmoji = { REIMAGINE: "dramatic exploration", EXPLORE: "moderate variation", REFINE: "conservative polish" };
  console.log(`\nGenerating ${count} variants of "${screenName}" (${range} — ${rangeEmoji[range] ?? range})...`);

  const variants = await generateVariants({
    screenId: existing.id,
    projectId: manifest.projectId,
    prompt: `Explore variations of this ${screenName} screen`,
    count,
    creativeRange: range,
    aspects,
  });

  fs.mkdirSync(designDir, { recursive: true });

  variants.forEach((v, i) => {
    const label = `${screenName}.variant-${range.toLowerCase()}-${i + 1}`;
    const htmlPath = `design/stitch/${label}.html`;
    const imagePath = `design/stitch/${label}.png`;
    downloadFile(v.htmlUrl, path.join(projectRoot, htmlPath));
    downloadFile(v.imageUrl, path.join(projectRoot, imagePath));
    console.log(`  v${i + 1} → ${htmlPath}`);
  });

  console.log(`\n${count} variants saved. Review and promote best with: stitch update ${screenName} "<refinement>"`);
}

/**
 * stitch init — set project-level style config stored in manifest.styleConfig.
 *
 * --auto   Read project docs (CLAUDE.md, README, PRD, docs/**) and propose a config.
 *          Outputs a proposal with reasoning for Claude to present to the user.
 *          Claude then confirms or adjusts and re-runs with explicit flags.
 *
 * Flags: --aesthetic, --brand, --palette, --typography, --profile, --theme, --platform, --notes
 */
function cmdInit(rawArgs) {
  const manifest = readManifest(projectRoot);

  // ── Auto mode: read docs and propose ──────────────────────────────────────
  if (rawArgs.includes("--auto")) {
    const { files, combined } = readProjectContext(projectRoot);

    if (files.length === 0) {
      console.log("PROPOSAL_RESULT: no_docs");
      console.log("No project documents found (CLAUDE.md, README.md, PRD.md, docs/**).");
      console.log("Ask the user directly for: aesthetic anchor, brand reference, color palette.");
      return;
    }

    const signals = extractSignals(combined);
    const { proposal, reasoning } = proposeStyleConfig(signals);

    // Output structured JSON for Claude to parse + present to user
    console.log("PROPOSAL_RESULT: ok");
    console.log("DOCS_READ: " + files.map((f) => f.path).join(", "));
    console.log("REASONING:");
    reasoning.forEach((r) => console.log("  - " + r));
    console.log("PROPOSED_CONFIG:");
    console.log(JSON.stringify(proposal, null, 2));
    console.log("\nTo confirm this config, run:");
    const flags = Object.entries(proposal)
      .filter(([k]) => k !== "notes" && k !== "platform" && k !== "theme")
      .map(([k, v]) => `--${k.replace(/([A-Z])/g, (m) => "-" + m.toLowerCase())} "${v}"`)
      .join(" \\\n  ");
    console.log(`  stitch init ${flags}`);
    console.log("\nOr adjust individual values with the flags above.");
    return;
  }

  // ── Manual mode: apply flags ───────────────────────────────────────────────
  const styleConfig = manifest.styleConfig ?? {};

  const flags = {
    "--aesthetic": "aestheticAnchor",
    "--brand": "brandReference",
    "--palette": "colorPalette",
    "--typography": "typography",
    "--profile": "profile",
    "--theme": "theme",
    "--platform": "platform",
    "--notes": "notes",
  };

  for (let i = 0; i < rawArgs.length; i++) {
    const key = flags[rawArgs[i]];
    if (key && rawArgs[i + 1] && !rawArgs[i + 1].startsWith("--")) {
      styleConfig[key] = rawArgs[i + 1];
      i++;
    }
  }

  if (Object.keys(styleConfig).length === 0) {
    console.log(`
Usage: stitch init --auto              Read project docs and propose a config
       stitch init [flags]             Set config directly

Flags:
  --aesthetic   "Japandi"                     Visual anchor
  --brand       "similar to Linear"           Design reference
  --palette     "dark neutral, teal accent"   Color palette
  --typography  "Satoshi headings, mono data" Typography
  --profile     product|marketing|dense       Quality profile
  --theme       "Light, modern minimal"       Theme description
  --platform    "Web, Desktop-first"          Platform target
  --notes       "..."                         Extra constraints

Current config:
${JSON.stringify(manifest.styleConfig ?? {}, null, 2)}
    `.trim());
    return;
  }

  manifest.styleConfig = styleConfig;
  writeManifest(projectRoot, manifest);
  console.log("Style config saved:");
  console.log(JSON.stringify(styleConfig, null, 2));
}

// ── helpers ────────────────────────────────────────────────────────────────

function fatal(msg) {
  console.error(`Error: ${msg}`);
  process.exit(1);
}

function confirm(question) {
  return new Promise((resolve) => {
    if (question) process.stdout.write(question);
    process.stdin.setEncoding("utf8");
    process.stdin.once("data", (data) => {
      resolve(data.trim().toLowerCase() === "y");
    });
  });
}

// ── dispatch ───────────────────────────────────────────────────────────────

switch (command) {
  case "auto": {
    // --screen flag for explicit screen hint; rest is the prompt
    const screenIdx = args.indexOf("--screen");
    const screenHint = screenIdx !== -1 ? args[screenIdx + 1] : undefined;
    const promptArgs = screenIdx !== -1
      ? [...args.slice(0, screenIdx), ...args.slice(screenIdx + 2)]
      : args;
    await cmdAuto(promptArgs.join(" "), screenHint);
    break;
  }
  case "init":     cmdInit(args); break;
  case "generate": await cmdGenerate(args.join(" ")); break;
  case "update":   await cmdUpdate(args[0], args.slice(1).join(" ")); break;
  case "breakdown": await cmdBreakdown(args.join(" ")); break;
  case "variants": await cmdVariants(args[0], args.slice(1)); break;
  case "list":     cmdList(); break;
  case "status":   cmdStatus(); break;
  default:
    console.log(`
Stitch — AI UI generation

Commands:
  generate  <prompt>               Generate screen(s) from a text prompt
  update    <name> <prompt>        Edit an existing screen
  breakdown <compound-prompt>      Preview screen breakdown before generating
  list                             Show all tracked screens
  status                           Check which screens exist on disk
    `.trim());
}
