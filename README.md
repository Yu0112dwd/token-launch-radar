# Token Launch Radar — make.fun bounty token-radar-01

[![make.fun](https://make.fun/badge/token-radar-01.svg)](https://make.fun/bounty/token-radar-01)
[![rank](https://make.fun/badge/token-radar-01/Yu0112dwd/token-launch-radar/rank.svg)](https://make.fun/bounty/token-radar-01)
[![reward](https://make.fun/badge/token-radar-01/Yu0112dwd/token-launch-radar/reward.svg)](https://make.fun/bounty/token-radar-01)

**Bounty:** "Build the best token launch radar" (`token-radar-01`) — $1,325 total
(1st $1,000, 2nd–5th $50 each, 6th–10th $25 each).
**Deadline:** 2026-12-14 10:00 UTC / 19:00 JST. **Started:** 2026-11-14.
**Entrant:** GitHub [Yu0112dwd](https://github.com/Yu0112dwd),
make.fun [@golden-puffin-42-1121](https://make.fun/u/golden-puffin-42-1121).

> **Status: built locally, NOT submitted.** See "Still missing for submission" below.

## v2 rebuild (2026-11-24) — kit rebuild, supersedes the v1 description below

Rebuilt from the official make.fun kit's sealed snapshot (`as_of`
2026-11-14, 758 protocols, 40-protocol watchlist; snapshot sha256
`42a71213519479f3a180cc5010cbbf6bd18a2447fa0ad29e4c5122b6c9184393`).
`main.ts` / `lib/model.ts` / `vendor/makefun-board.ts` are the kit starter
(vendor byte-for-byte, sha256
`9ca51b6e5cd84fe46cb0efa61e2ea99365a1fb0e21f2b75e6007f977f0dc326e`),
with `lib/model.ts` extended only by early-row wrapped/staked/bridge
exclusions and comparables-as-evidence fields; ranking is the kit house
model (TVL × 0.25 × growth × maturity). Full rules:
`data/METHODOLOGY.md` §v2.

- **Run:** `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts --input <kit input dir>` — exits 0, `boardIssue()` null.
- **Board:** 170 rows in `out/board.json` (all 40 watchlist slugs + 130
  early rows). Total TVL $15,251,460,097; total implied value
  $2,950,087,667. Top 10: Steakhouse Financial ($543.6m), Gauntlet
  ($323.8m), Veda ($311.3m), USDD ($214.2m), Upshift ($111.7m),
  Nonce Capital ($75.3m), OnRe ($60.1m), Bittensor dTAO ($56.4m),
  Symbiotic ($55.1m), OpenTrade ($51.4m).
- **Determinism:** three runs produce byte-identical `out/board.json`,
  `out/data.js` and `out/dossier.json` (board sha256 `15aafaba…`,
  dossier sha256 `477731ac…`; full hashes in `data/METHODOLOGY.md` §v2.5).
- **Dashboard rebuilt, screenshots re-taken, dossier regenerated
  (2026-11-24, §v2.6):** `dashboard/` is rebuilt from the kit starter
  (`index.html`, `app.css`, `app.js`, `README.md` — 4 files, 33,992 bytes;
  stale v1 `data.json` / `styles.css` deleted; loads `../data.js`, no fetch,
  no network). Dossier text is 34,331 / 65,536 bytes, all dashboard files
  whole, no cut. `screenshots/` are re-taken v2 shots (`1-board.png`,
  `2-detail.png`, `3-filtered.png`, all 1440×1000, visually checked —
  top row Steakhouse Financial, $543.6M implied). `out/dossier.json`
  regenerated from the final dashboard + screenshots (732,196 bytes,
  schema `makefun/dossier/v1`, cover 0, 3 images).
- The sections below still describe v1 unless marked otherwise.

## What it is

A radar of the pre-token DeFi protocols most worth a token launch, ranked by
implied launch value, with a usable dashboard: a sortable/filterable board,
a detail view for every protocol, and a farm plan per protocol.

- **Data:** fresh DefiLlama pull (`https://api.llama.fi/protocols`),
  fetched 2026-11-24T12:30:40Z — 9,100 protocols tracked, 353 eligible after
  filters, board = top 150 by TVL (min TVL $8.5m).
- **Ranking:** implied value = TVL × category median mcap/TVL of tokenized
  comparables in the same category (global median 0.255 fallback when a
  category has < 3 comparables), ratio capped at p75 × 1.5, 0.85 haircut for
  a 7d TVL fall worse than −20% or unaudited protocols, total capped at $5bn.
  **mcap/TVL is a proxy for FDV/TVL** — DefiLlama reports market cap, not FDV.
  Full rules: `data/METHODOLOGY.md`.
- **Top 10:** Polymarket International ($651m implied), Sentora Curator
  ($574m), Gauntlet ($342m), RocketSwap Anubis V2 ($128m), Extended Perps
  ($108m), Veda ($106m), BitFi Basis ($106m), Nonce Capital ($100m),
  OnRe ($97m), Arcus Perps ($68m). Board totals: TVL $14.87bn,
  implied value $3.86bn, median implied value $5.9m, 27 categories.
- **Not financial advice.** No airdrop or points programme is confirmed for
  any row; farm plans are generic category-tailored usage steps.

## Files

| File | What it is |
|---|---|
| `main.ts` | Node 22 program (no deps, no network). Validates `board.json` / `dossier.json` and writes `out/` + `dashboard/data.json`. Run: `node main.ts` |
| `board.json` | 150 rows, sorted by implied value desc. Each row: rank, slug, name, category, chains, TVL, 7d change, implied value + method, comparables, category median ratio, confidence + reason, farm plan, links, `tokenStatus: "no-token"` |
| `dossier.json` | Summary: source, fetchedAt, counts, exclusion counts, category comparables, top 10, limitations, disclaimer |
| `data/build_board.py` | Reproducible builder (re-run on `data/raw_full.json` reproduces board + dossier) |
| `data/METHODOLOGY.md` | Exact eligibility rules, ranking formula, confidence, verification, limitations |
| `data/raw_protocols.json` | Trimmed DefiLlama pull (3.9 MB); `data/raw_full.json` is the untrimmed pull (9.3 MB) |
| `dashboard/index.html`, `app.js`, `app.css` | Static dashboard, no network at runtime (loads local `../data.js` only; see `dashboard/README.md`) |
| `dashboard/README.md` | How to open offline (v2) |
| `screenshots/1-board.png` | Board, default sort, 170 of 170 shown (1440×1000) |
| `screenshots/2-detail.png` | Detail view, #1 Steakhouse Financial (1440×1000) |
| `screenshots/3-filtered.png` | Board filtered to Risk Curators, 33 of 170 shown (1440×1000) |
| `LICENSE` | MIT (OSI-approved, as the bounty requires) |

## How to run / verify

```sh
node main.ts            # validates board.json + dossier.json, writes out/ + dashboard/data.json
python3 -m http.server 8000   # then open http://127.0.0.1:8000/dashboard/index.html
# or: google-chrome --allow-file-access-from-files dashboard/index.html
```

Verified 2026-11-24: `node main.ts` exits 0 ("OK: 150 rows, 27 categories.
Total TVL: $14,867,618,009. Total implied value: $3,864,020,163.");
`board.json`/`dossier.json` are valid JSON; 150 rows, unique slugs, sorted by
implied value, all `tokenStatus: "no-token"`, farm plan ≥ 4 steps per row;
dashboard renders offline (CDP render checks: board 150 rows, detail #1,
filtered Lending 15 rows); all 3 screenshots visually checked and show the
intended views; no external loads in `dashboard/` (only outbound link targets
in the data).

## Still missing for submission (do NOT claim this is ready to submit)

1. **`vendor/makefun-board.ts`** from the official make.fun kit — not
   downloaded and not invented. The kit is needed for the official local
   grade, transcript bundling, and submission. Download it only from the
   official make.fun kit source.
2. **GitHub repository** — create a public repo under Yu0112dwd (created
   after the competition opened, 2026-11-14), MIT-licensed, with this
   content at its root (`main.ts` in root). Not created yet.
3. **Agent transcripts** — the sessions that built this entry, bundled with
   the kit's CLI. The build sessions for this entry need to be bundled at
   submission time; do not fabricate them.
4. **Submission itself** — at most 5 submissions a day, 10 in all; the last
   submission before the deadline is the final entry. Not submitted.
5. **Sealed snapshot difference** — this board uses a fresh DefiLlama pull
   (2026-11-24), not the kit's sealed snapshot, so the watchlist will
   differ from an entry built on the sealed snapshot. If the kit's snapshot
   is available at submission time, rebuild from it with
   `data/build_board.py` and re-run `node main.ts` + re-take screenshots.

## Known limitations

- Risk Curators (25 rows) and Onchain Capital Allocators (19 rows) dominate
  the board; their "launch value" is speculative and most use the blunt
  global median ratio (category n < 3).
- Token status is DefiLlama fields only; a token recorded elsewhere is missed.
- Categories with < 3 comparables use the global median mcap/TVL (0.255).
- TVL/mcap are a single snapshot (2026-11-24T12:30:40Z) and move daily.
- 1 row has null `tvlChange7d`; 11 rows lack a website, 4 lack a Twitter handle.
