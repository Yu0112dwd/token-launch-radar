#!/usr/bin/env python3
"""
Build the make.fun token-radar-01 board from a fresh DefiLlama pull.

Data source: https://api.llama.fi/protocols (public, no key).
Reproducible: reads data/raw_full.json if present (fetched 2026-11-24
~12:30 UTC via curl), otherwise fetches the API live with urllib and
records fetched_at. Writes:
  data/raw_protocols.json  (trimmed copy, < ~5 MB)
  board.json               (top 150 eligible protocols, ranked by implied value)
  dossier.json             (summary / counts / comparables / limitations)

Eligibility and ranking rules are documented in full in
data/METHODOLOGY.md. Summary of the pipeline (sequential, first-match):
  1. already_tokenized  -- strong token evidence (see has_token_evidence)
  2. no_usable_tvl / tvl_lt_1m
  3. excluded_category  -- CEX / Bridge / Canonical Bridge / Liquid Staking /
                          Reserve Currency
  4. wrapped_or_staked_name
  5. parent_has_token
  6. description_wrapped_or_staked
Ranking: impliedValueUsd = TVL x category median mcap/TVL (tokenized
comparables in the same category), ratio capped at p75 x 1.5, a 0.85
haircut for sharp 7d TVL falls or unaudited protocols, total capped at $5bn.
mcap/TVL is a proxy for FDV/TVL: DefiLlama reports mcap, not FDV.
"""
import json
import math
import os
import re
import statistics
import urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RAW_FULL = os.path.join(DATA, "raw_full.json")
RAW_TRIMMED = os.path.join(DATA, "raw_protocols.json")
BOARD = os.path.join(BASE, "board.json")
DOSSIER = os.path.join(BASE, "dossier.json")
API_URL = "https://api.llama.fi/protocols"

TVL_MIN = 1_000_000
BOARD_N = 150
IMPLIED_CAP = 5_000_000_000
HAIRCUT = 0.85

EXCLUDED_CATEGORIES = {
    "Liquid Staking", "Canonical Bridge", "Bridge", "CEX", "Reserve Currency",
    "Cross Chain Bridge", "Liquid Restaking", "Stablecoin Wrapper",
    "Dual-Token Stablecoin", "Restaked BTC", "Decentralized BTC", "Anchor BTC",
}
WRAPPED_RE = re.compile(r"wrapped|wst|steth|staked|lst|liquid staking", re.I)
# Stablecoin products: the token IS the stablecoin, so there is no
# separate launch to rank. Pattern covers the stablecoin-named rows
# found on manual review (thUSD, YUSD, avUSD, USDCx, USDdw, ftUSD,
# USDh, USDM, "Stablecoin" in the name). It does not match generic
# "USD" (many tokenized protocols use USD in a product name and are
# already excluded by the token-evidence check).
STABLECOIN_RE = re.compile(
    r"stablecoin|thusd|yusd|avusd|usdcx|usddw|ftusd|usdh|usdm", re.I)
# Wrapped / staked BTC and BTC-adjacent products: the underlying (BTC,
# TAO) already trades, so these are wrapped/staked products of one
# that trades.
WRAPPED_BTC_RE = re.compile(
    r"btc staking|lightning network|chain fusion|gtbtc|ybtc|dtao|bittensor",
    re.I)
# Manual review exclusions (slug -> reason). USDD's own token trades
# but DefiLlama records no symbol/mcap/address for the protocol row,
# so the automatic token-evidence check misses it.
MANUAL_EXCLUDE_SLUGS = {
    "usdd": "USDD is itself a stablecoin token that trades",
}
DESC_WRAPPED_RE = re.compile(
    r"wrapped|staked version|liquid staking token|staked .* token", re.I)

# ---------------------------------------------------------------- helpers
def percentile(values, q):
    s = sorted(values)
    if not s:
        return None
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def has_symbol(p):
    return bool(p.get("symbol")) and p.get("symbol") != "-"


def has_token_evidence(p):
    """Strong token evidence only.

    symbol (not '-' / null), mcap > 0, or a token contract address.
    gecko_id / cmcId ALONE do not count: they are weak signals (a
    listing page can exist without a live token, and 12 protocols in
    this pull have only a gecko_id/cmcId with no symbol, mcap or
    address). They count only in combination with a symbol or mcap,
    which is already covered by the strong checks above.
    """
    return (
        has_symbol(p)
        or (p.get("mcap") or 0) > 0
        or bool(p.get("address"))
    )


def parent_slug(p):
    s = p.get("parentProtocolSlug") or ""
    if s:
        return s
    pp = p.get("parentProtocol") or ""
    return pp.split("#")[-1] if "#" in pp else pp


def is_unaudited(p):
    audits = p.get("audits")
    return (audits in (None, "", "0")) and not p.get("audit_links")


# ------------------------------------------------------- farm-plan templates
# Steps are generic, category-tailored usage steps. Nothing here asserts
# an airdrop, points programme or token launch exists: pointsOrRewards
# says so explicitly for every row.
def _fp(steps, watch, risks, cost, minutes):
    return {
        "steps": steps,
        "pointsOrRewards": (
            "No confirmed airdrop or points programme in the DefiLlama data "
            f"for this protocol. {watch} If a programme is announced, watch "
            "the project's official site / X for its terms; do not assume one exists."
        ),
        "risks": risks,
        "estimatedCostUsd": cost,
        "estimatedTimeMin": minutes,
    }


GENERIC_RISKS = [
    "Smart-contract risk: funds deposited in the protocol's contracts could be lost to a bug or exploit.",
    "No token may ever launch, and past usage may never be rewarded.",
    "TVL and yields can fall sharply; check current terms on the project's official site before depositing.",
]

FARM_TEMPLATES = {
    "Risk Curators": lambda n, ch: _fp([
        f"Open {n} on its official site ({ch}) and read which vaults / curators it manages and on which chains.",
        "Pick one vault whose underlying strategy and assets you understand; check its current TVL, fees and any lock-up or withdrawal delay.",
        "Deposit a small test amount first, confirm the vault share / receipt token appears in your wallet, then scale up only if comfortable.",
        "Hold the vault position over several weeks (generic step: curators typically reward sustained deposits, if they reward anything at all).",
        "Re-check the vault's allocation and curator updates weekly; withdraw if the strategy changes in a way you do not understand.",
        "Keep records of deposits, withdrawals and fees for tax / accounting.",
    ], "Watch for any vault-deposit or curator points programme, if announced.",
       GENERIC_RISKS + ["Curator risk: the vault's returns depend on a third-party curator's allocation decisions."],
       60, 90),
    "Onchain Capital Allocator": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read which vaults it offers and what strategies / assets each one holds.",
        "Choose a vault matching your risk appetite; check fees, withdrawal terms and minimums before depositing.",
        "Deposit a small test amount, confirm the receipt token, then add more only if comfortable.",
        "Hold the position over several weeks (generic step: allocators typically reward sustained deposits, if they reward anything at all).",
        "Monitor vault performance and strategy changes weekly and exit if the mandate changes.",
        "Keep records of deposits, withdrawals and fees.",
    ], "Watch for any vault-deposit points programme, if announced.",
       GENERIC_RISKS + ["Strategy risk: the allocator may rotate into strategies you would not choose yourself."],
       60, 90),
    "Lending": lambda n, ch: _fp([
        f"Open {n} ({ch}), connect a wallet on a supported chain and check which assets can be supplied and borrowed, and current rates.",
        "Supply a widely used asset (e.g. a major stablecoin or ETH) as collateral; start small and confirm the deposit is reflected.",
        "Optionally borrow a small amount against the supplied collateral, keeping the health factor / loan-to-value well inside the safe range.",
        "Use the app at least weekly (generic step: repeat supply / borrow / repay activity, if the protocol ever rewards usage).",
        "Monitor your health factor after any large price move and repay or top up collateral promptly to avoid liquidation.",
        "Keep records of interest paid / earned and any liquidation thresholds.",
    ], "Watch for any supply / borrow points programme, if announced.",
       GENERIC_RISKS + ["Liquidation risk: borrowed positions can be liquidated if collateral value falls."],
       40, 75),
    "Dexs": lambda n, ch: _fp([
        f"Open {n} ({ch}) and check which pools / pairs have the deepest liquidity and lowest slippage for your trade size.",
        "Make a small test swap first and compare the received amount with the quoted amount.",
        "If providing liquidity, pick a pool you understand, check the fee tier and the impermanent-loss profile, and deposit a small amount first.",
        "Use the DEX periodically (generic step: repeat swaps / LP activity over weeks, if the protocol ever rewards usage).",
        "Track your LP position and exit if volume or fees collapse.",
        "Keep records of swaps, fees paid and LP returns.",
    ], "Watch for any trading-volume or LP points programme, if announced.",
       GENERIC_RISKS + ["Impermanent loss: LP positions can underperform simply holding the assets."],
       25, 60),
    "RWA": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read what real-world asset backs each product, who the issuer / custodian is, and whether KYC or accreditation is required.",
        "Complete any KYC / onboarding the issuer requires before depositing; check minimums and lock-ups.",
        "Buy or deposit into the product with a small test amount and confirm the on-chain receipt / token.",
        "Hold the position and monitor issuer reports and redemption terms (generic step: sustained holding is what RWA products typically track, if they track anything).",
        "Check redemption / secondary-market options before you need them, so you know how to exit.",
        "Keep records of purchases, yields and redemptions.",
    ], "Watch for any holder points programme, if announced.",
       GENERIC_RISKS + ["Issuer / custodian risk: the on-chain product depends on an off-chain issuer and its reserves."],
       50, 90),
    "Yield": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read how each yield product generates its return and what the underlying assets are.",
        "Deposit a small test amount into a product you understand; confirm the receipt token and the stated APY / fees.",
        "Hold over several weeks (generic step: sustained deposits are what yield products typically track, if they track anything).",
        "Re-check the yield source weekly; yields can be subsidised and can fall fast.",
        "Withdraw a small amount once to confirm the exit path works before committing more.",
        "Keep records of deposits, yields and fees.",
    ], "Watch for any deposit points programme, if announced.",
       GENERIC_RISKS + ["Yield-source risk: the advertised yield may come from incentives that end, or from leveraged strategies."],
       40, 75),
    "Derivatives": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read the trading rules: leverage limits, fees, funding, liquidation and any testnet / mainnet status.",
        "Start with a small test trade at low or no leverage and confirm fills, fees and funding behave as expected.",
        "Trade modest size only, with a pre-set stop / exit plan; do not increase leverage to chase losses.",
        "Use the platform periodically (generic step: repeat trading activity over weeks, if the protocol ever rewards usage).",
        "Monitor open positions daily while they are live and close them before funding costs dominate.",
        "Keep records of trades, fees and funding paid.",
    ], "Watch for any trading-volume points programme, if announced.",
       GENERIC_RISKS + ["Leverage risk: derivatives can lose more than the initial margin quickly."],
       30, 60),
    "Basis Trading": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read how its basis / delta-neutral yield is generated and what the backing assets are.",
        "Check the product's current yield, fees, redemption terms and any lock-up before depositing.",
        "Deposit a small test amount and confirm the receipt token and redemption path.",
        "Hold over several weeks (generic step: sustained deposits are what these products typically track, if they track anything).",
        "Monitor funding rates and the issuer's reserve / attestation reports weekly.",
        "Keep records of deposits, yields and redemptions.",
    ], "Watch for any deposit points programme, if announced.",
       GENERIC_RISKS + ["Basis risk: funding-rate income can turn negative and the hedge can break in volatile markets."],
       50, 75),
    "Yield Aggregator": lambda n, ch: _fp([
        f"Open {n} ({ch}) and compare the vaults / strategies it routes to, their APYs, fees and underlying protocols.",
        "Deposit a small test amount into one vault; confirm the receipt token and that the strategy matches the description.",
        "Hold over several weeks (generic step: sustained deposits are what aggregators typically track, if they track anything).",
        "Check the vault's underlying strategies weekly; an aggregator can rotate into protocols you would not choose.",
        "Test a small withdrawal to confirm the exit path works.",
        "Keep records of deposits, yields and fees.",
    ], "Watch for any deposit points programme, if announced.",
       GENERIC_RISKS + ["Stacked risk: the aggregator adds its own contracts on top of the underlying protocols' risk."],
       40, 75),
    "CDP": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read the collateral types, minimum collateral ratio, stability / borrowing fees and liquidation rules.",
        "Open a small test vault / position with a conservative collateral ratio, well above the liquidation threshold.",
        "Mint or borrow only a modest amount against the collateral; keep a buffer for price falls.",
        "Monitor the collateral ratio weekly (generic step: maintain the position over time, if the protocol ever rewards usage).",
        "Top up collateral or repay debt promptly if the ratio approaches the liquidation level.",
        "Keep records of collateral, debt and fees.",
    ], "Watch for any vault / borrowing points programme, if announced.",
       GENERIC_RISKS + ["Liquidation risk: collateral can be liquidated if its price falls below the threshold."],
       40, 75),
    "Staking Pool": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read the staking terms: reward rate, lock-up / unbonding period, validator / operator and fees.",
        "Stake a small test amount first and confirm the stake and any receipt token are reflected.",
        "Hold through at least one full reward / unbonding cycle (generic step: sustained staking is what pools typically track, if they track anything).",
        "Check validator performance and reward payouts weekly.",
        "Test unstaking a small amount to confirm the unbonding delay before committing more.",
        "Keep records of stakes, rewards and fees.",
    ], "Watch for any staking points programme, if announced.",
       GENERIC_RISKS + ["Slashing / validator risk: staked assets can be penalised for validator faults, and unbonding can take days or weeks."],
       30, 60),
    "Prediction Market": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read the market rules, fees, resolution criteria and how winnings are paid.",
        "Start with small positions in markets you understand; confirm the trade settles as quoted.",
        "Trade periodically across different markets (generic step: repeat activity over weeks, if the protocol ever rewards usage).",
        "Check open positions before each market's resolution date and close or hold deliberately.",
        "Withdraw winnings / funds promptly and confirm the withdrawal path works.",
        "Keep records of trades and outcomes.",
    ], "Watch for any trading points programme, if announced.",
       GENERIC_RISKS + ["Market risk: prediction-market positions can go to zero if the outcome resolves against you."],
       25, 60),
    "Payments": lambda n, ch: _fp([
        f"Open {n} ({ch}) and read how payments / transfers work, which assets and chains are supported, and the fees.",
        "Make a small test payment or transfer and confirm it arrives as expected.",
        "Use the product for real payments you would make anyway (generic step: repeat usage over weeks, if the protocol ever rewards usage).",
        "Check fee and limit changes before larger transfers.",
        "Keep records of payments and fees.",
    ], "Watch for any usage points programme, if announced.",
       GENERIC_RISKS,
       20, 45),
}

DEFAULT_FARM = lambda n, ch, cat: _fp([
    f"Open {n} ({ch}) and read what the protocol does, which assets it accepts, and its fees and withdrawal terms.",
    "Try the core function with a small test amount first and confirm the transaction settles as expected.",
    "Use the protocol's main feature periodically (generic step: repeat usage over weeks, if the protocol ever rewards usage).",
    "Re-check the protocol's terms and TVL weekly before adding more funds.",
    "Test a small withdrawal / exit to confirm you can get funds out.",
    "Keep records of deposits, withdrawals and fees.",
], "Watch for any usage points programme, if announced.",
   GENERIC_RISKS,
   40, 75)


def farm_plan(p):
    cat = p.get("category") or "Unknown"
    name = p.get("name") or p.get("slug")
    chains = p.get("chains") or []
    ch = ", ".join(chains[:3]) if chains else "its supported chains"
    tpl = FARM_TEMPLATES.get(cat)
    if tpl:
        return tpl(name, ch)
    return DEFAULT_FARM(name, ch, cat)


# ---------------------------------------------------------------- main
def fetch_live():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "makefun-token-radar/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return data, fetched_at


def main():
    if os.path.exists(RAW_FULL):
        with open(RAW_FULL) as f:
            protocols = json.load(f)
        mtime = os.path.getmtime(RAW_FULL)
        fetched_at = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        protocols, fetched_at = fetch_live()
        with open(RAW_FULL, "w") as f:
            json.dump(protocols, f)

    total = len(protocols)
    tokenized_slugs = {p["slug"] for p in protocols if has_token_evidence(p)}
    gecko_cmc_only = sum(
        1 for p in protocols
        if not has_token_evidence(p) and (p.get("gecko_id") or p.get("cmcId"))
    )

    # Trimmed raw copy: keep only fields the build uses / a reader needs.
    trimmed = []
    for p in protocols:
        trimmed.append({
            "id": p.get("id"), "name": p.get("name"), "slug": p.get("slug"),
            "category": p.get("category"), "chains": p.get("chains"),
            "tvl": p.get("tvl"), "change_1d": p.get("change_1d"),
            "change_7d": p.get("change_7d"), "mcap": p.get("mcap"),
            "symbol": p.get("symbol"), "gecko_id": p.get("gecko_id"),
            "cmcId": p.get("cmcId"), "address": p.get("address"),
            "url": p.get("url"), "twitter": p.get("twitter"),
            "audits": p.get("audits"),
            "audit_links": p.get("audit_links") or [],
            "parentProtocolSlug": p.get("parentProtocolSlug"),
            # description dropped: it is the bulkiest field and is not used
            # by the build (except the wrapped/staked description check,
            # which is re-derived from the full pull if needed).
        })
    with open(RAW_TRIMMED, "w") as f:
        json.dump({"fetchedAt": fetched_at, "source": API_URL,
                   "totalProtocols": total, "protocols": trimmed}, f)

    # ---- comparables: tokenized (symbol + mcap), TVL >= $1m, per category
    comp_by_cat = {}
    all_ratios = []
    for p in protocols:
        if has_symbol(p) and (p.get("mcap") or 0) > 0 and (p.get("tvl") or 0) >= TVL_MIN:
            r = p["mcap"] / p["tvl"]
            all_ratios.append(r)
            comp_by_cat.setdefault(p.get("category") or "Unknown", []).append(p)
    global_stats = {
        "n": len(all_ratios),
        "median": statistics.median(all_ratios),
        "p25": percentile(all_ratios, 0.25),
        "p75": percentile(all_ratios, 0.75),
    }
    cat_stats = {}
    for cat, ps in comp_by_cat.items():
        ratios = [p["mcap"] / p["tvl"] for p in ps]
        cat_stats[cat] = {
            "n": len(ratios),
            "median": statistics.median(ratios),
            "p25": percentile(ratios, 0.25),
            "p75": percentile(ratios, 0.75),
        }

    def stats_for(cat):
        """Category stats if n>=3, else the global stats (fallback)."""
        s = cat_stats.get(cat)
        if s and s["n"] >= 3:
            return s, "category"
        return global_stats, "global-fallback"

    # ---- sequential eligibility pipeline (first-match exclusion counts)
    excluded = {
        "already_tokenized": 0, "no_usable_tvl": 0, "tvl_lt_1m": 0,
        "excluded_category": 0, "wrapped_or_staked_name": 0,
        "stablecoin_product": 0, "wrapped_btc_product": 0,
        "manual_review_exclusion": 0,
        "parent_has_token": 0, "description_wrapped_or_staked": 0,
    }
    eligible = []
    for p in protocols:
        if has_token_evidence(p):
            excluded["already_tokenized"] += 1
            continue
        tvl = p.get("tvl")
        if tvl is None or not isinstance(tvl, (int, float)) or tvl <= 0:
            excluded["no_usable_tvl"] += 1
            continue
        if tvl < TVL_MIN:
            excluded["tvl_lt_1m"] += 1
            continue
        if (p.get("category") or "") in EXCLUDED_CATEGORIES:
            excluded["excluded_category"] += 1
            continue
        if WRAPPED_RE.search((p.get("name") or "") + " " + (p.get("slug") or "")):
            excluded["wrapped_or_staked_name"] += 1
            continue
        if STABLECOIN_RE.search((p.get("name") or "") + " " + (p.get("slug") or "")):
            excluded["stablecoin_product"] += 1
            continue
        if WRAPPED_BTC_RE.search((p.get("name") or "") + " " + (p.get("slug") or "")):
            excluded["wrapped_btc_product"] += 1
            continue
        if (p.get("slug") or "") in MANUAL_EXCLUDE_SLUGS:
            excluded["manual_review_exclusion"] += 1
            continue
        if parent_slug(p) in tokenized_slugs:
            excluded["parent_has_token"] += 1
            continue
        if DESC_WRAPPED_RE.search(p.get("description") or ""):
            excluded["description_wrapped_or_staked"] += 1
            continue
        eligible.append(p)

    eligible.sort(key=lambda p: p["tvl"], reverse=True)
    watchlist = eligible[:BOARD_N]

    # ---- ranking
    rows = []
    for p in watchlist:
        cat = p.get("category") or "Unknown"
        stats, stats_source = stats_for(cat)
        median_ratio = stats["median"]
        cap_ratio = stats["p75"] * 1.5
        eff_ratio = min(median_ratio, cap_ratio)
        ch7 = p.get("change_7d")
        unaudited = is_unaudited(p)
        haircut_applied = bool(
            (ch7 is not None and ch7 < -20) or unaudited)
        haircut_reason = None
        if ch7 is not None and ch7 < -20:
            haircut_reason = f"change_7d {ch7:.1f}% < -20%"
        if unaudited:
            haircut_reason = (haircut_reason + "; " if haircut_reason else "") + \
                "audits=0 and no audit_links"
        implied = p["tvl"] * eff_ratio
        if haircut_applied:
            implied *= HAIRCUT
        implied = min(implied, IMPLIED_CAP)

        method = (
            f"TVL x {'category' if stats_source == 'category' else 'global (category n<3 fallback)'} "
            f"median mcap/TVL {median_ratio:.3f} (n={stats['n']}, "
            f"p25={stats['p25']:.3f}, p75={stats['p75']:.3f}); ratio capped at "
            f"p75 x 1.5 = {cap_ratio:.3f} (effective ratio {eff_ratio:.3f})"
            + (f"; x 0.85 haircut ({haircut_reason})" if haircut_applied else "; no haircut")
            + "; implied value capped at $5bn. mcap/TVL is a proxy for FDV/TVL "
              "(DefiLlama reports mcap, not FDV)."
        )

        # comparables: same-category tokenized, closest TVL (log distance), up to 5
        pool = comp_by_cat.get(cat, [])
        pool_sorted = sorted(
            pool, key=lambda q: abs(math.log((q["tvl"] or 1) / (p["tvl"] or 1))))
        comps = []
        for q in pool_sorted[:5]:
            comps.append({
                "slug": q["slug"], "name": q.get("name"), "category": q.get("category"),
                "mcapUsd": round(q["mcap"]), "tvlUsd": round(q["tvl"]),
                "ratio": round(q["mcap"] / q["tvl"], 4),
            })
        if len(comps) < 3:
            # fill with the globally closest-TVL tokenized protocols
            seen = {c["slug"] for c in comps}
            global_pool = sorted(
                (q for ps in comp_by_cat.values() for q in ps),
                key=lambda q: abs(math.log((q["tvl"] or 1) / (p["tvl"] or 1))))
            for q in global_pool:
                if len(comps) >= 3 or q["slug"] in seen:
                    continue
                comps.append({
                    "slug": q["slug"], "name": q.get("name"),
                    "category": q.get("category"),
                    "mcapUsd": round(q["mcap"]), "tvlUsd": round(q["tvl"]),
                    "ratio": round(q["mcap"] / q["tvl"], 4),
                })

        # confidence: 0.30-0.95
        conf = 0.50
        reasons = []
        if stats["n"] >= 10:
            conf += 0.20; reasons.append(f"{stats['n']} comparables")
        elif stats["n"] >= 5:
            conf += 0.10; reasons.append(f"{stats['n']} comparables")
        else:
            reasons.append(f"only {stats['n']} comparables ({stats_source})")
        if p["tvl"] >= 100_000_000:
            conf += 0.10; reasons.append("TVL >= $100m")
        elif p["tvl"] >= 10_000_000:
            conf += 0.05; reasons.append("TVL >= $10m")
        if ch7 is not None and -10 <= ch7 <= 10:
            conf += 0.10; reasons.append("7d TVL change stable (-10% to +10%)")
        elif ch7 is not None:
            reasons.append(f"7d TVL change {ch7:.1f}%")
        if haircut_applied:
            conf -= 0.05; reasons.append("haircut applied (" + (haircut_reason or "") + ")")
        conf = round(max(0.30, min(0.95, conf)), 2)

        fp = farm_plan(p)
        rows.append({
            "slug": p["slug"], "name": p.get("name"),
            "category": cat,
            "chains": (p.get("chains") or [])[:5],
            "tvlUsd": round(p["tvl"]),
            "tvlChange7d": round(ch7, 2) if isinstance(ch7, (int, float)) else None,
            "impliedValueUsd": round(implied),
            "impliedValueMethod": method,
            "comparables": comps,
            "categoryMedianRatio": round(median_ratio, 4),
            "confidence": conf,
            "confidenceReason": "; ".join(reasons),
            "farmPlan": fp,
            "website": p.get("url"),
            "twitter": p.get("twitter"),
            "defillamaUrl": f"https://defillama.com/protocol/{p['slug']}",
            "tokenStatus": "no-token",
            "source": "DefiLlama api.llama.fi/protocols",
            "fetchedAt": fetched_at,
        })

    rows.sort(key=lambda r: r["impliedValueUsd"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r2 = {"rank": i}
        r2.update(r)
        rows[i - 1] = r2

    with open(BOARD, "w") as f:
        json.dump(rows, f, indent=2)

    # ---- dossier
    board_cats = {}
    for r in rows:
        board_cats.setdefault(r["category"], {"n": 0})
        board_cats[r["category"]]["n"] += 1
    cat_comps = []
    for cat in sorted(board_cats):
        stats, src = stats_for(cat)
        cat_comps.append({
            "category": cat, "nComparables": stats["n"],
            "categoryNComparables": cat_stats.get(cat, {}).get("n", 0),
            "medianRatio": round(stats["median"], 4),
            "p25": round(stats["p25"], 4), "p75": round(stats["p75"], 4),
            "source": src,
        })
    dossier = {
        "title": "Token Launch Radar — DefiLlama data layer (token-radar-01)",
        "bountySlug": "token-radar-01",
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": API_URL,
        "fetchedAt": fetched_at,
        "totalProtocolsTracked": total,
        "preTokenCandidates": len(protocols) - excluded["already_tokenized"],
        "excludedCounts": dict(excluded, gecko_cmc_id_only_not_excluded=gecko_cmc_only),
        "eligibleAfterAllFilters": len(eligible),
        "watchlistCount": len(watchlist),
        "boardRows": len(rows),
        "methodologySummary": (
            "No-token protocols (no symbol, mcap or token address in DefiLlama; "
            "gecko_id/cmcId alone do not count) with TVL >= $1m, excluding "
            "CEX/bridge (incl. Cross Chain Bridge)/liquid-staking (incl. Liquid "
            "Restaking)/reserve-currency/stablecoin-wrapper/dual-token-stablecoin/"
            "restaked-BTC categories, stablecoin products, wrapped/staked BTC "
            "products and children of tokenized parents, plus a manual exclusion "
            "of USDD. Ranked by implied value "
            "= TVL x category median mcap/TVL of tokenized comparables "
            "(global median fallback when a category has <3 comparables), ratio "
            "capped at p75 x 1.5, 0.85 haircut for 7d TVL fall < -20% or unaudited "
            "protocols, total capped at $5bn. mcap/TVL is a proxy for FDV/TVL."
        ),
        "categoryComparables": cat_comps,
        "top10": [r["slug"] for r in rows[:10]],
        "limitations": [
            "No sealed kit snapshot was available, so the watchlist is a fresh DefiLlama pull (fetched 2026-11-24), not the kit's sealed snapshot; results will differ from any entry built on the sealed snapshot.",
            "vendor/makefun-board.ts from the kit is missing (not downloaded, not invented); this build is the data layer only (board.json / dossier.json / data/).",
            "mcap/TVL is a proxy for FDV/TVL: DefiLlama reports market cap, not fully diluted valuation, and mcap can be stale or missing for some comparables.",
            "Token status reflects DefiLlama fields only (symbol, mcap, address). A protocol can have a token elsewhere that DefiLlama does not record (e.g. an entry whose description mentions a token, or a token launched after the pull); no independent token search was done.",
            "gecko_id/cmcId alone were not treated as token evidence (12 protocols in this pull have only those); if the judge's sealed snapshot treats them as token evidence, a few rows could differ.",
            "Categories with fewer than 3 tokenized comparables fall back to the global median mcap/TVL (0.255), which is a blunt proxy for those categories.",
            "Farm plans are generic, category-tailored usage steps; no airdrop, points programme or token launch is confirmed for any row.",
            "TVL, mcap and 7d change are a single snapshot in time (fetched_at); they move daily.",
        ],
        "disclaimer": (
            "Not financial advice. Implied values are estimates from a simple "
            "comparables proxy, not predictions that a token will launch or "
            "reach any valuation. Do your own research before using any protocol."
        ),
    }
    with open(DOSSIER, "w") as f:
        json.dump(dossier, f, indent=2)

    print(f"fetchedAt={fetched_at} total={total} eligible={len(eligible)} "
          f"board_rows={len(rows)}")
    print("excluded:", excluded, "gecko_cmc_only_not_excluded:", gecko_cmc_only)
    print("global stats:", {k: round(v, 4) if isinstance(v, float) else v
                            for k, v in global_stats.items()})
    for r in rows[:10]:
        print(f"#{r['rank']} {r['name']} ({r['slug']}) {r['category']} "
              f"TVL ${r['tvlUsd']:,} implied ${r['impliedValueUsd']:,}")


if __name__ == "__main__":
    main()
