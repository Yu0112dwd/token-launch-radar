# Token Launch Radar — Methodology (token-radar-01)

Bounty: **"Build the best token launch radar"**, slug `token-radar-01`.
This document describes exactly how `board.json` and `dossier.json` were built
from DefiLlama data. Nothing in this build was submitted, registered, or paid
for; no private key, seed phrase, password, or API key was used.

> **Not financial advice.** Implied values below are estimates from a simple
> comparables proxy, not predictions that a token will launch or reach any
> valuation. Do your own research before using any protocol.

## v2 (kit rebuild) — 2026-11-24 — supersedes v1

Sections 1–8 below describe the **superseded v1 build** (fresh DefiLlama pull,
150 rows, comparables ranking). This section describes the v2 rebuild from the
official make.fun kit's sealed snapshot. Nothing in v2 was submitted,
registered, or paid for; no private key, seed phrase, password, or API key was
used. The kit CLI was not run.

### v2.1 Sealed snapshot

- **Kit:** `~/workspace/makefun/kit/token-radar-01-kit/token-radar-01-kit/`
  (`kit.json` bundle sha256 `ea1c9dccab78e6846655e81b921a79465c7267677ea2e0908624ddbc8a012d43`).
- **Snapshot:** `input/snapshot.json`, sha256
  `42a71213519479f3a180cc5010cbbf6bd18a2447fa0ad29e4c5122b6c9184393`
  (matches `kit.json`).
- **Contents:** `as_of` 2026-11-14; `source` DefiLlama
  `https://api.llama.fi/protocols`, fetched 2026-11-14T01:18:33.201Z;
  `floor_usd` $50,000,000; **758 protocols** (≥ $5M TVL, exactly 10 fields
  each); **watchlist 40 slugs**. 342 of the 758 protocols record no token
  (`mcap_usd`, `gecko_id` and `symbol` all null).
- **Program:** `main.ts` (starter, with a one-line log fix: the dashboard
  file count in its final message), `lib/model.ts` (starter + v2 additions,
  §v2.2–v2.3), `vendor/makefun-board.ts` copied byte-for-byte from the kit,
  sha256 `9ca51b6e5cd84fe46cb0efa61e2ea99365a1fb0e21f2b75e6007f977f0dc326e`.
  `main.ts` reads the snapshot by default from `/input/snapshot.json` and
  takes `--input <snapshot.json|directory>`; local run:
  `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts --input <kit input dir>`.
  It writes `out/board.json`, `out/data.js`, copies `dashboard/` and
  `screenshots/` to `out/`, and writes `out/dossier.json` **last** via
  `buildDossier(out, {text_max_bytes: 65536, screenshots: {max: 4, max_bytes: 524288}, dashboard: {max_files: 400, max_bytes: 4194304}})`.
  No `Date.now` / `new Date` in outputs; the only date arithmetic is
  `age_days = as_of − listed_at` from snapshot dates.

### v2.2 Ranking change — why, and what replaced v1's driver

- **v1 driver (dropped as the ranking driver):** implied = TVL ×
  category-median mcap/TVL of tokenized comparables in the same category
  (global median 0.255 fallback if < 3 comparables), ratio capped at
  p75 × 1.5, $5bn cap, 0.85 haircut if 7d change < −20% (or unaudited).
- **v2 driver (kit starter house model, `impliedValue` in `lib/model.ts`):**
  `implied = max(1, round(TVL × 0.25 × (1 + clamp(change_7d, −60, 120)/100 × 0.5) × (0.6 + min(age_days, 1095)/1095 × 0.4)))`,
  `age_days = as_of − listed_at` (unknown → 365). No ratio cap, no $5bn cap,
  no haircut.
- **Why:** the judge criteria in the kit's `RULES.txt` state implied value
  follows TVL, 7-day growth and age with no token — not a hardcoded list of
  names and not a comparables ratio. The house model is the kit-required
  driver; using v1's comparables as the driver would fail that criterion.
- **Comparables retained as supporting evidence only (extra keys, allowed by
  the gate):** per row `categoryMedianRatio`, `categoryMedianRatioSource`
  (`category` | `global-fallback`), `categoryComparablesCount`,
  `comparables` (up to 5 tokenized protocols from the **sealed snapshot
  only**, same category, `mcap_usd > 0`, `tvl_usd ≥ $1m`, closest by TVL on
  a log scale), `confidence` + `confidenceReason`, and
  `impliedValueMethod` naming both the house formula and the comparables
  cross-check (`TVL × category median ratio`). They never change a rank.
  Sealed-snapshot figures: tokenized pool n = 128, global median ratio
  **0.213803** (v1's fresh-pull global median was 0.255, n = 202 — different
  data, not an error). Category median used when a category has ≥ 3
  comparables (86 rows); otherwise the global median (84 rows).
  Confidence is v1's score minus its haircut penalty: base 0.50, +0.20 for
  ≥ 10 comparables (+0.10 for 5–9), +0.10 for TVL ≥ $100m (+0.05 for
  ≥ $10m), +0.10 for a 7d change between −10% and +10%, clamped to
  [0.30, 0.95]; observed range 0.50–0.90.

### v2.3 Board selection and early-row exclusions

- **Board: 170 rows = all 40 watchlist slugs + 130 early rows**
  (≥ 100 required; 130 rows outside the watchlist, ≥ 60 required).
  Watchlist TVL $51,272,081–$2,753,981,495. 29 categories on the board;
  median implied value $3,704,159.
- **Watchlist coverage is complete, including the four slugs v1 excluded:**
  `usdd` (rank 4), `bittensor-dtao` (rank 8), `lightning-network` (rank 16),
  `saturn` (rank 21). The gate requires every watchlist slug, so v1's
  exclusions of them were wrong for this entry and are not applied to
  watchlist rows. `saturn` is category Stablecoin Wrapper;
  `bittensor-dtao` / `lightning-network` match v1's wrapped-BTC product
  words — all three would be excluded by §v2.3's early filter, which is why
  the filter must never touch watchlist rows.
- **Early rows:** pre-token protocols below the $50M floor by TVL, cap 160
  (`EARLY_ROWS`, non-binding here). Of 186 rankable pre-token protocols
  below the floor, **56 were excluded** by v1's wrapped/staked/bridge
  exclusions (applied to early rows only) and **130 kept**:
  category Bridge 13, Canonical Bridge 7, Liquid Staking 20, Liquid
  Restaking 3, Dual-Token Stablecoin 2; name/slug word `staking` 6;
  product markers `chain fusion` 1, `ftusd` 1, `stablecoin` 1, `ybtc` 1,
  `yusd` 1. The full early filter (`isExcludedEarly` in `lib/model.ts`):
  category in {Bridge, Canonical Bridge, Liquid Staking, Liquid Restaking,
  Restaked BTC, CEX, Stablecoin Wrapper, Dual-Token Stablecoin}; name/slug
  containing `wrapped` / `staked` / `staking` / `wst` / `steth` / `lst`
  (substring, as in v1); stablecoin products (`stablecoin`, `thUSD`,
  `YUSD`, `avUSD`, `USDCx`, `USDdw`, `ftUSD`, `USDh`, `USDM`); wrapped-BTC
  products (`btc staking`, `lightning network`, `chain fusion`, `gtbtc`,
  `ybtc`, `dtao`, `bittensor`, `wrapped btc`, `wbtc`).
- **Why the filter matters even though the floor already excludes the big
  ones:** the kit's `isRankable` alone (pre-token, not CEX, not versioned)
  would rank wrapped/staked/bridge products at the top if the floor were
  ever lifted — WBTC ($7,908,800,359 TVL, Bridge), Binance staked ETH
  ($7,448,338,841, Liquid Staking) and Coinbase Bridge (Bridge) are all
  pre-token in the snapshot's record. In v2 they are absent twice over:
  above the $50M floor (so not early rows) and excluded by this filter
  anyway. No early row on the board has an excluded category.
- **Row schema (kit `lib/model.ts`, exact):** `rank`, `slug`, `name`,
  `category`, `chains`, `tvl_usd`, `change_7d`, `mcap_usd`, `listed_at`,
  `gecko_id`, `symbol`, `token_status: 'pre-token'`, `age_days`,
  `implied_value_usd`, `model{base_multiple, growth_pct,
  growth_multiplier, maturity_multiplier, age_days}`, `farm_steps`:
  6 strings each (kit `farmSteps`/`stepText`), 20–600 chars, each naming
  cost and time. `board.json` is `{"rows": [...]}`, sorted by
  `implied_value_usd` desc, ranks 1..170. All 170 implied values are
  distinct.

### v2.4 What was dropped from v1 (and why)

- **Audit haircut — dropped, impossible here:** the sealed snapshot has no
  audit fields (`audits`, `audit_links` do not exist among its 10 fields),
  so v1's 0.85 haircut for unaudited protocols cannot be computed. The
  7d-change part of v1's haircut is also dropped: the house model already
  prices 7d change through its growth multiplier. Documented, not silently
  omitted.
- **`farmPlan` object — dropped:** replaced by the kit's `farm_steps:
  string[]` (6 steps per row). The cost/time content survives inside each
  step string (`Cost: … Time: …`); `pointsOrRewards` / `risks` /
  `estimatedCostUsd` / `estimatedTimeMin` as separate fields are gone.
  Farm steps still never assert a points programme or airdrop exists.
- **`website` / `twitter` / `defillamaUrl` / `fetchedAt` / `source` row
  fields — dropped:** the sealed snapshot carries none of them (10 fields
  only, no website or Twitter handle); nothing was invented to fill them.
- **v1 `board.json` / `dossier.json` at the repo root — removed** (preserved
  in `~/workspace/makefun/token-radar-01-v1-backup/`). The board is now
  generated by `node main.ts` into `out/board.json`; `out/` is git-ignored.
  `data/build_board.py` and `data/raw_*.json` remain in the repo as v1
  artefacts and are **not** used by v2.

### v2.5 Results (verified 2026-11-24, two runs)

- **Board:** 170 rows. **Total TVL $15,251,460,097. Total implied value
  $2,950,087,667.** Watchlist coverage 40/40, 130 rows outside the
  watchlist. Ranks 1..170, sorted by implied value desc.
- **Top 10 by implied value:** 1 Steakhouse Financial $543,636,080 ·
  2 Gauntlet $323,776,463 · 3 Veda $311,287,338 · 4 USDD $214,232,685 ·
  5 Upshift $111,679,277 · 6 Nonce Capital $75,323,884 · 7 OnRe
  $60,130,582 · 8 Bittensor dTAO $56,414,103 · 9 Symbiotic $55,106,874 ·
  10 OpenTrade $51,414,515.
- **Verification:** `node main.ts` exits 0; `boardIssue()` is null
  (checked in-program, exit 1 otherwise). Independent re-check:
  house-formula mismatches 0/170, comparables mismatches 0/170,
  farm-step lengths all 20–600 chars, all slugs in the snapshot, all rows
  pre-token per the snapshot. `out/board.json` 393,173 bytes (< 8 MiB).
- **Determinism (three runs, 2026-11-24):** `out/board.json` sha256
  `15aafabaff6ad6d3bc773673dd25e5c2d67a8e0e566b09fd4c2a1d44bd8caf03`
  and `out/data.js` sha256
  `1e20fdd231da370c5cffd4a560ff665e8be84218423d66cc8bf80e34126324f4`
  byte-identical across all runs; `out/dossier.json` also identical
  across all three runs (sha256
  `477731ac39008de87b5129b8ef4a58ee286df42bbda255ac3467fc535aaba1e2`)
  with the final dashboard and screenshots in place.

### v2.6 Dashboard rebuild and screenshots (2026-11-24)

- **Dashboard rebuilt from the kit starter** (`starter/dashboard/`):
  `dashboard/index.html`, `app.css`, `app.js` plus a short `README.md` —
  4 files, 33,992 bytes total. The stale v1 `dashboard/data.json`
  (516 KB) and `dashboard/styles.css` are deleted; the page loads
  `../data.js` (`window.RADAR`) and makes no fetch and no network request
  (no `fetch`, no URL in any attribute, style, or script import).
  It renders a sortable/filterable board of all 170 rows, search +
  category filter, a Pre-token / Live token tab (24 live rows with market
  caps), a per-protocol detail dialog deep-linkable as
  `#/protocol/<slug>`, and a 6-step farm plan with cost + time per step.
  It states model radar-1 (TVL × 0.25 × growth × maturity) and that
  implied values are estimates, not financial advice.
- **Dossier text is no longer cut:** 34,331 of the 65,536-byte cap, all
  four dashboard files included whole, no cut marker.
- **Screenshots re-taken** (headless Chromium 157 via CDP, `file://`
  URLs — plain `--screenshot` produced no output in this build, and an
  `http://127.0.0.1` serve was refused by the browser's local-network
  access checks, so the page was opened from disk): `screenshots/`
  now holds `1-board.png` (150,519 B), `2-detail.png` (217,644 B,
  Steakhouse Financial detail, dialog open), `3-filtered.png`
  (154,364 B, Risk Curators, 33 of 170 shown), all 1440×1000, each
  ≤ 512 KiB. The old v1 `board.png` / `detail.png` / `filtered.png`
  are deleted from `screenshots/` and from `out/screenshots/`
  (main.ts copies but never cleans `out/`, so stale files there had to
  be removed by hand). All three were visually checked: the board shows
  the v2 top row (Steakhouse Financial, $543.6M implied), not the v1 board.
- **Dossier regenerated** from the final dashboard + screenshots:
  `out/dossier.json` 732,196 bytes (≤ 1.5 MiB), schema
  `makefun/dossier/v1`, cover 0, 3 images.

## 1. Data source

- **Source:** DefiLlama public API, `https://api.llama.fi/protocols` (no key).
- **Fetched:** 2026-11-24T12:30:40Z (UTC). `fetchedAt` is recorded in every
  board row, in `dossier.json`, and in `data/raw_protocols.json`.
- **Total protocols counted:** 9,100.
- **Files:** `data/build_board.py` (the reproducible builder — re-running it
  on the saved pull reproduces `board.json` / `dossier.json` exactly),
  `data/raw_protocols.json` (trimmed copy of the pull, 3.9 MB; logo and
  description fields dropped), `data/raw_full.json` (the untrimmed pull,
  kept for audit).
- **Important limitation — no sealed kit snapshot:** the bounty kit's sealed
  snapshot was not available for this build (and was not downloaded), so the
  watchlist is a **fresh DefiLlama pull from 2026-11-24, not the kit's sealed
  snapshot**. Results will differ from any entry built on the sealed snapshot.
  Likewise `vendor/makefun-board.ts` from the kit is **missing** — it was not
  downloaded and not invented. This document covers the data layer
  (`board.json`, `dossier.json`, `data/`); the dashboard is in `dashboard/`
  and the program that packages the entry is `main.ts`.

## 2. What counts as "already has a token" (token evidence)

A protocol is treated as **already tokenized** — and excluded — if **any** of
these strong signals is present in the DefiLlama record:

| Signal | Rule |
|---|---|
| `symbol` | present and not `"-"` and not null |
| `mcap` | not null and > 0 |
| `address` | token contract address, not null |

**`gecko_id` / `cmcId` alone do NOT count.** That is a deliberate choice:
a CoinGecko / CoinMarketCap listing page can exist without a live, trading
token, and these are weak signals on their own. They count only in
combination with a symbol or mcap — which is already covered by the strong
checks above, so in practice they never change the outcome. In this pull,
12 protocols have *only* a `gecko_id`/`cmcId` and no strong signal; they were
**not** excluded for that reason (recorded in `dossier.json` as
`gecko_cmc_id_only_not_excluded: 12`). If the judge's sealed snapshot treats
`gecko_id`/`cmcId` alone as token evidence, a few rows could differ.

**Consequence / limitation:** token status reflects **DefiLlama fields only**.
A protocol can have a token elsewhere that DefiLlama does not record (for
example an entry whose description mentions a token, or a token launched
after the pull). No independent token search was done, and no token launch,
airdrop date, or points programme was invented for any row.

## 3. Eligibility pipeline (sequential, first match wins)

Each protocol is tested in this order and counted once, under the first rule
it fails. Counts are in `dossier.json` → `excludedCounts`.

| # | Rule | Excluded in this pull |
|---|---|---|
| 1 | `already_tokenized` — strong token evidence (§2) | 4,705 |
| 2 | `no_usable_tvl` — `tvl` null, zero, or not a number | 1,768 |
| 3 | `tvl_lt_1m` — TVL < $1,000,000 | 2,077 |
| 4 | `excluded_category` — category in {CEX, Bridge, Canonical Bridge, Cross Chain Bridge, Liquid Staking, Liquid Restaking, Reserve Currency, Stablecoin Wrapper, Dual-Token Stablecoin, Restaked BTC, Decentralized BTC, Anchor BTC} | 185 |
| 5 | `wrapped_or_staked_name` — name or slug contains `wrapped`, `wst`, `steth`, `staked`, `lst`, or `liquid staking` (case-insensitive) | 0 |
| 5a | `stablecoin_product` — name/slug matches `stablecoin`, `thUSD`, `YUSD`, `avUSD`, `USDCx`, `USDdw`, `ftUSD`, `USDh`, or `USDM` | 8 |
| 5b | `wrapped_btc_product` — name/slug matches `btc staking`, `lightning network`, `chain fusion`, `gtbtc`, `ybtc`, `dtao`, or `bittensor` | 3 |
| 5c | `manual_review_exclusion` — slug `usdd` (USDD is itself a stablecoin token that trades, but DefiLlama records no symbol/mcap/address for the protocol row) | 1 |
| 6 | `parent_has_token` — `parentProtocolSlug` (or the slug after `#` in `parentProtocol`) belongs to a tokenized protocol | 0 |
| 7 | `description_wrapped_or_staked` — description matches `wrapped` / `staked version` / `liquid staking token` | 0 |

- **Eligible after all filters: 353.** The board keeps the **top 150 by TVL**
  (minimum TVL on the board: $8,548,148).
- **Cleanup pass (2026-11-24, after the first build):** the first board
  still contained stablecoins (USDD, thUSD/YUSD/avUSD products), wrapped-BTC
  products (Bittensor dTAO, GTBTC, Lightning Network, Chain Fusion) and a
  cross-chain bridge (Circle Gateway) that the original exact-category list
  had missed. Rules 4, 5a, 5b and 5c above were added for exactly those
  cases and the builder was re-run on the same saved pull
  (`data/raw_full.json`, fetched 2026-11-24T12:30:40Z), so the board is still
  reproducible from the same snapshot. The re-run removed 28 rows and
  backfilled the board with the next eligible protocols by TVL; the new
  top 10 is in §7.
- **CEXs and bridges excluded even when no-token — judgement call:** they are
  not launchable DeFi protocols in the usual sense (a centralised exchange or
  a bridge rarely launches a governance token in the way a DeFi protocol
  does), so they are out regardless of token status. This is a judgement
  call, documented here rather than hidden in the code.
- The wrapped/staked name check is a substring match, so it can in principle
  catch innocent names; in this pull it caught 0 protocols after the
  earlier filters (the one it caught in the first build was re-caught by
  the wider category list in the re-run).

## 4. Ranking — comparables method

For each category, the **comparables** are tokenized protocols in that same
category with a symbol **and** `mcap > 0` and TVL ≥ $1m. For those, compute
`ratio = mcap / TVL`, then the **median, p25 and p75** of the ratio
(percentiles by linear interpolation).

- **Category median ratio** is the FDV/TVL proxy. It is stated clearly here
  and in every row's `impliedValueMethod`: **this is a market-cap/TVL proxy,
  not true FDV/TVL**, because DefiLlama reports market cap, not fully
  diluted valuation, and mcap can be stale or missing for some comparables.
- **Fallback:** if a category has **fewer than 3 comparables**, the **global**
  median ratio is used instead (global: n=202, median 0.255, p25 0.048,
  p75 1.511). This avoids absurd medians from n=1 categories (e.g. Risk
  Curators has a single comparable with ratio 3.212; Farm's single comparable
  has ratio 12.823). Fallback categories are flagged with
  `"source": "global-fallback"` in `dossier.json` → `categoryComparables`
  (which also records the true category n as `categoryNComparables`).
- **Formula** (per row, also spelled out in `impliedValueMethod`):

```
effectiveRatio = min(categoryMedianRatio, categoryP75 × 1.5)
impliedValueUsd = TVL × effectiveRatio
if change_7d < -20% OR (audits == "0" AND no audit_links):
    impliedValueUsd ×= 0.85        # haircut; reason named in the method string
impliedValueUsd = min(impliedValueUsd, $5,000,000,000)
```

- The ratio cap (p75 × 1.5) and the $5bn cap stop a single rich category or a
  giant TVL from producing a fantasy valuation. The 0.85 haircut applies to
  90 of the 150 rows (mostly unaudited protocols: `audits == "0"` with no
  `audit_links`).
- **Sort:** final board is sorted by `impliedValueUsd` descending, rank 1..150.
  TVL-descending order is *not* required and is *not* the ranking.

### Category median ratios used (board categories)

| Category | n comparables | Median | p25 | p75 | Source |
|---|---|---|---|---|---|
| Basis Trading | 7 | 0.585 | 0.257 | 1.082 | category |
| CDP | 9 | 0.167 | 0.034 | 0.299 | category |
| Derivatives | 8 | 1.396 | 0.356 | 2.276 | category |
| Dexs | 25 | 0.380 | 0.068 | 1.528 | category |
| Indexes | 3 | 0.155 | 0.103 | 1.018 | category |
| Lending | 21 | 0.135 | 0.023 | 0.430 | category |
| Liquidity Manager | 3 | 0.017 | 0.015 | 11.329 | category |
| Onchain Capital Allocator | 4 | 0.075 | 0.019 | 0.599 | category |
| Prediction Market | 3 | 2.072 | 1.631 | 3.301 | category |
| RWA | 10 | 0.334 | 0.093 | 0.876 | category |
| Yield | 18 | 0.152 | 0.034 | 0.538 | category |
| Yield Aggregator | 6 | 0.065 | 0.031 | 0.212 | category |
| All other board categories | — | 0.255 | 0.048 | 1.511 | global fallback (category n < 3) |

Global comparables overall: n=202, median 0.255, p25 0.048, p75 1.511.

## 5. Confidence (0–1)

Deterministic score, clamped to [0.30, 0.95], starting at 0.50:

- +0.20 if ≥ 10 comparables, +0.10 if 5–9, +0 if fewer;
- +0.10 if TVL ≥ $100m, +0.05 if TVL ≥ $10m;
- +0.10 if 7d TVL change is between −10% and +10% (stable);
- −0.05 if the 0.85 haircut was applied.

`confidenceReason` on each row names the components. Confidence is about
*how much evidence supports the estimate*, not a probability that a token
launches.

## 6. Row contents

Each row of `board.json` has: `rank`, `slug`, `name`, `category`,
`chains` (top 5), `tvlUsd` (rounded), `tvlChange7d` (if present),
`impliedValueUsd` (rounded), `impliedValueMethod`, `comparables` (3–5
tokenized protocols in the same category, chosen by closest TVL on a log
scale, with their mcap, TVL and ratio; filled from the global pool only if
fewer than 3 same-category comparables exist), `categoryMedianRatio`,
`confidence`, `confidenceReason`, `farmPlan`, `website`, `twitter`
(if present), `defillamaUrl` (`https://defillama.com/protocol/<slug>`),
`tokenStatus: "no-token"`, `source`, `fetchedAt`. No row carries a token
symbol.

### Farm plans

`farmPlan` = `{steps (5–6 concrete steps, tailored to the category/product),
pointsOrRewards, risks (3–4 items), estimatedCostUsd, estimatedTimeMin}`.
Steps are **generic, category-tailored usage steps** (e.g. for Lending:
supply collateral, optionally borrow at a safe health factor, monitor it;
for Dexs: test swap, then LP). Where a step is generic (e.g. "use the app
weekly"), it says so in the step text.

`pointsOrRewards` **never** asserts a programme exists. Every row states:
*"No confirmed airdrop or points programme in the DefiLlama data for this
protocol"* followed by what to watch for if one is announced. No airdrop
dates, point programmes, or valuations beyond the comparables formula were
invented.

`estimatedCostUsd` / `estimatedTimeMin` are rough active-time and gas/fee
estimates per category ($20–$60 / 45–90 min), not quotes.

## 7. Verification (2026-11-24)

- `python3 -m json.tool board.json` and `dossier.json`: valid JSON.
- Board rows: **150** (≥ 120 required). No duplicate slugs. Ranks 1..150,
  sorted by `impliedValueUsd` descending.
- Every row: `impliedValueUsd > 0`, `farmPlan.steps ≥ 4` (min 5), all
  required fields present, `tokenStatus == "no-token"`, no `symbol` field,
  TVL ≥ $1m (min $8,548,148), 3–5 comparables per row.
- Top 10 by implied value (after the §3 cleanup re-run): Polymarket
  International ($651m), Sentora Curator ($574m), Gauntlet ($342m),
  RocketSwap Anubis V2 ($128m), Extended Perps ($108m), Veda ($106m),
  BitFi Basis ($106m), Nonce Capital ($100m), OnRe ($97m),
  Arcus Perps ($68m). Total board TVL $14.87bn, total implied value $3.86bn.

## 8. Limitations (also in `dossier.json`)

1. Fresh pull, not the kit's sealed snapshot; `vendor/makefun-board.ts` missing.
2. mcap/TVL is a proxy for FDV/TVL (DefiLlama reports mcap, not FDV).
3. Token status is DefiLlama fields only; tokens recorded elsewhere are missed.
4. `gecko_id`/`cmcId` alone not treated as token evidence (12 protocols).
5. Categories with < 3 comparables use the blunt global median (0.255).
6. Farm plans are generic usage steps; no airdrop or points programme is confirmed.
7. TVL, mcap and 7d change are a single snapshot (2026-11-24T12:30:40Z) and move daily.
8. Some top rows are institutional-only products (e.g. risk curators / vault
   allocators, 25 + 19 rows) whose "launch value" is inherently speculative
   — they are kept because the stated rules keep them, and the reader
   should weigh that. Stablecoins, wrapped-BTC products and cross-chain
   bridges were removed in the §3 cleanup pass, so no stablecoin or
   wrapped-BTC row remains on the board.
