#!/usr/bin/env node
// Bump the plugin version and sync it across every manifest location, so
// marketplace consumers get auto-updates instead of a stale cached copy.
//
// The version lives in three places that must always agree:
//   .claude-plugin/plugin.json      -> version
//   .claude-plugin/marketplace.json -> metadata.version
//   .claude-plugin/marketplace.json -> plugins[].version
//
// Usage:
//   node scripts/bump-version.mjs           # patch bump (default): 2.0.0 -> 2.0.1
//   node scripts/bump-version.mjs minor     # 2.0.1 -> 2.1.0
//   node scripts/bump-version.mjs major     # 2.1.0 -> 3.0.0
//   node scripts/bump-version.mjs 3.4.2     # set an explicit version
//   node scripts/bump-version.mjs patch --commit   # also git-commit + tag v<version>

import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PLUGIN = path.join(ROOT, ".claude-plugin", "plugin.json");
const MARKETPLACE = path.join(ROOT, ".claude-plugin", "marketplace.json");

function parseVersion(v) {
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(String(v ?? "").trim());
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

function nextVersion(current, arg) {
  if (parseVersion(arg)) return arg.trim();
  const [maj, min, pat] = parseVersion(current) ?? [0, 0, 0];
  if (arg === "major") return `${maj + 1}.0.0`;
  if (arg === "minor") return `${maj}.${min + 1}.0`;
  if (arg === "patch") return `${maj}.${min}.${pat + 1}`;
  throw new Error(`Unknown bump argument: "${arg}". Use major | minor | patch | x.y.z`);
}

async function readJson(file) {
  return JSON.parse(await readFile(file, "utf8"));
}

async function writeJson(file, obj) {
  await writeFile(file, JSON.stringify(obj, null, 2) + "\n");
}

const args = process.argv.slice(2);
const commit = args.includes("--commit");
const bumpArg = args.find((a) => a !== "--commit") ?? "patch";

const plugin = await readJson(PLUGIN);
const marketplace = await readJson(MARKETPLACE);

const current =
  marketplace.metadata?.version ?? plugin.version ?? "0.0.0";
const version = nextVersion(current, bumpArg);

plugin.version = version;
marketplace.metadata = { ...marketplace.metadata, version };
marketplace.plugins = (marketplace.plugins ?? []).map((p) => ({
  ...p,
  version,
}));

await writeJson(PLUGIN, plugin);
await writeJson(MARKETPLACE, marketplace);

console.log(`✓ version ${current} -> ${version} (plugin.json + marketplace.json)`);

if (commit) {
  const rel = [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"];
  execFileSync("git", ["add", ...rel], { cwd: ROOT, stdio: "inherit" });
  execFileSync("git", ["commit", "-m", `Release v${version}`], { cwd: ROOT, stdio: "inherit" });
  execFileSync("git", ["tag", `v${version}`], { cwd: ROOT, stdio: "inherit" });
  console.log(`✓ committed and tagged v${version} (run: git push --follow-tags)`);
}
