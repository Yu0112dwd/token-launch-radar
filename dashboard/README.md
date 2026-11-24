# Token Launch Radar — dashboard (token-radar-01, v2)

Offline, static dashboard for the make.fun bounty **token-radar-01**
("Build the best token launch radar", $1,325 prize, deadline 2026-12-14 19:00 JST).

## How to open it (no network needed)

`index.html` loads only the local `data.js` next to `dashboard/`
(`../data.js`, written by `node main.ts`), then `app.js` renders the board.
No fetch, no external scripts, fonts or images:

```
# straight from disk (script tags work from file://)
open dashboard/index.html
# or serve the built output with any local static server, then open
# out/dashboard/index.html from it.
```

## Files

- `index.html` — page shell; loads `../data.js`, then `app.js`
- `app.css` — light theme, dark header band, right-aligned numbers
- `app.js` — renders from `window.RADAR`: board, filters, detail dialog, farm plans

## What it shows

- Header: 170 pre-token protocols (40 watchlist + 130 early rows),
  total TVL **$15,251,460,097**, total implied value **$2,950,087,667**,
  29 categories. Snapshot: DefiLlama sealed snapshot, `as_of` 2026-11-14.
- Method (also in `../data/METHODOLOGY.md` §v2): model **radar-1**,
  implied = TVL × 0.25 × (1 + clamp(7d change, −60, 120)/100 × 0.5)
  × (0.6 + min(age, 1095)/1095 × 0.4). Implied values are **estimates,
  not financial advice**.
- Board: sortable table of all 170 rows (rank, protocol, TVL, 7d, age,
  implied value, token status). Top 10 ranks are highlighted.
  Click a column header to re-sort; click a row for its detail view.
- Filters: text search (name, slug, category, chain) and category select.
  The count line reads "N rows shown". "Clear filters" resets both.
  Deep links: `#category=Risk%20Curators`, `#q=veda`.
- Tabs: **Pre-token** (the ranked board) and **Live token** (24 protocols
  whose token already trades, shown with market cap, set aside from the ranking).
- Detail: click any row, or open `#/protocol/<slug>` directly, e.g.
  `#/protocol/steakhouse-financial`. Shows rank, category, chains,
  TVL + 7d change, implied value with its growth/maturity multipliers
  (the page recomputes the row and checks it against the board's number),
  and a 6-step farm plan with a cost and a time per step.

## Screenshots (`../screenshots/`)

- `1-board.png` — full board, default sort (implied value, high → low), top rows.
- `2-detail.png` — detail view of #1 Steakhouse Financial, opened via
  `#/protocol/steakhouse-financial` (implied value $543,636,080).
- `3-filtered.png` — board filtered to category **Risk Curators** (33 of 170 shown).

All three are 1440×1000 PNGs, taken with headless Chromium.
