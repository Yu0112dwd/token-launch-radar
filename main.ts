// main.ts — Token Launch Radar (make.fun bounty token-radar-01)
// Node 22.18+ (type-stripping runtime; no build step, no dependencies, no network).
// Reads board.json + dossier.json in the repo root, validates them against the
// bounty deliverables, and writes a packaged copy for the offline dashboard
// plus a machine-readable summary to out/.
//
// The board itself is built from a DefiLlama snapshot by data/build_board.py
// (see data/METHODOLOGY.md). This program does NOT fetch from the network:
// it works from the snapshot-derived board.json so the entry is reproducible
// from the repo alone.
//
// Usage:  node main.ts
// Output: out/summary.json, out/board.json, dashboard/data.json (generated copy)

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(fileURLToPath(import.meta.url));
const BOARD_PATH = join(ROOT, "board.json");
const DOSSIER_PATH = join(ROOT, "dossier.json");
const OUT_DIR = join(ROOT, "out");

type FarmPlan = {
  steps: string[];
  pointsOrRewards?: string;
  risks: string[];
  estimatedCostUsd?: number;
  estimatedTimeMin?: number;
};

type BoardRow = {
  rank: number;
  slug: string;
  name: string;
  category: string;
  chains: string[];
  tvlUsd: number;
  tvlChange7d?: number | null;
  impliedValueUsd: number;
  impliedValueMethod: string;
  comparables: { name: string; slug: string; mcapUsd: number; tvlUsd: number; ratio: number }[];
  categoryMedianRatio: number;
  confidence: number;
  confidenceReason: string;
  farmPlan: FarmPlan;
  website?: string;
  twitter?: string;
  defillamaUrl: string;
  tokenStatus: string;
  source: string;
  fetchedAt: string;
};

function fail(message: string): never {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function loadJson<T>(path: string, label: string): T {
  if (!existsSync(path)) fail(`${label} not found at ${path}`);
  try {
    return JSON.parse(readFileSync(path, "utf8")) as T;
  } catch (e) {
    fail(`${label} is not valid JSON: ${String(e)}`);
  }
}

const board = loadJson<BoardRow[]>(BOARD_PATH, "board.json");
const dossier = loadJson<Record<string, unknown>>(DOSSIER_PATH, "dossier.json");

// --- Validation (mirrors the bounty requirements) ---
const errors: string[] = [];
if (!Array.isArray(board)) errors.push("board.json is not an array");
if (board.length < 100) errors.push(`board.json has ${board.length} rows, need at least 100`);
const slugs = new Set<string>();
for (const [i, row] of board.entries()) {
  const where = `row ${i} (${row?.slug ?? "?"})`;
  if (typeof row.rank !== "number" || row.rank !== i + 1) errors.push(`${where}: rank must be ${i + 1}`);
  if (!row.slug || slugs.has(row.slug)) errors.push(`${where}: missing or duplicate slug`);
  slugs.add(row.slug);
  if (!row.name || !row.category) errors.push(`${where}: missing name/category`);
  if (!(row.tvlUsd > 0)) errors.push(`${where}: tvlUsd must be > 0`);
  if (!(row.impliedValueUsd > 0)) errors.push(`${where}: impliedValueUsd must be > 0`);
  if (row.tokenStatus !== "no-token") errors.push(`${where}: tokenStatus must be "no-token"`);
  if (!row.farmPlan || row.farmPlan.steps.length < 4) errors.push(`${where}: farmPlan needs at least 4 steps`);
  if (!Array.isArray(row.comparables) || row.comparables.length < 1) errors.push(`${where}: need at least 1 comparable`);
  if (typeof row.confidence !== "number" || row.confidence < 0 || row.confidence > 1) errors.push(`${where}: confidence must be 0..1`);
}
for (let i = 1; i < board.length; i++) {
  if (board[i].impliedValueUsd > board[i - 1].impliedValueUsd) {
    errors.push(`board is not sorted by impliedValueUsd at rank ${board[i].rank}`);
    break;
  }
}
if (errors.length > 0) {
  for (const e of errors.slice(0, 20)) console.error(`- ${e}`);
  fail(`validation failed with ${errors.length} error(s)`);
}

// --- Summary ---
const totalTvl = board.reduce((s, r) => s + r.tvlUsd, 0);
const totalImplied = board.reduce((s, r) => s + r.impliedValueUsd, 0);
const categories = [...new Set(board.map((r) => r.category))].sort();
const summary = {
  bounty: "token-radar-01",
  title: "Build the best token launch radar",
  generatedAt: new Date().toISOString(),
  rows: board.length,
  totalTvlUsd: Math.round(totalTvl),
  totalImpliedValueUsd: Math.round(totalImplied),
  medianImpliedValueUsd: Math.round(board[Math.floor(board.length / 2)].impliedValueUsd),
  categories,
  top10: board.slice(0, 10).map((r) => ({ rank: r.rank, slug: r.slug, name: r.name, tvlUsd: r.tvlUsd, impliedValueUsd: r.impliedValueUsd })),
  dossier: {
    fetchedAt: dossier["fetchedAt"] ?? null,
    totalProtocolsTracked: dossier["totalProtocolsTracked"] ?? null,
    watchlistCount: dossier["watchlistCount"] ?? null,
  },
  checks: {
    rowsAtLeast100: board.length >= 100,
    sortedByImpliedValue: true,
    allNoToken: board.every((r) => r.tokenStatus === "no-token"),
    allHaveFarmPlan: board.every((r) => r.farmPlan.steps.length >= 4),
    uniqueSlugs: slugs.size === board.length,
  },
};

// --- Outputs ---
mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(join(ROOT, "dashboard"), { recursive: true });
writeFileSync(join(OUT_DIR, "summary.json"), JSON.stringify(summary, null, 2) + "\n");
writeFileSync(join(OUT_DIR, "board.json"), JSON.stringify(board, null, 2) + "\n");
// Packaged copy for the offline dashboard (same data, no network needed at view time).
writeFileSync(join(ROOT, "dashboard", "data.json"), JSON.stringify({ generatedAt: summary.generatedAt, rows: board, summary }, null, 2) + "\n");

console.log(`OK: ${board.length} rows, ${categories.length} categories`);
console.log(`Total TVL: $${Math.round(totalTvl).toLocaleString()}  Total implied value: $${Math.round(totalImplied).toLocaleString()}`);
console.log(`Top 1: ${board[0].name} — TVL $${Math.round(board[0].tvlUsd).toLocaleString()}, implied $${Math.round(board[0].impliedValueUsd).toLocaleString()}`);
console.log(`Wrote out/summary.json, out/board.json, dashboard/data.json`);
