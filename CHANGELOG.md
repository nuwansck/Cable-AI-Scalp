# Changelog

## Cable AI Scalp v1.5 — 2026-07-06

### Add: H1 over-extension band filter
- **New filter measuring how far the entry sits beyond the H1 EMA, in the
  trade's own direction** (`BUY: (price - h1_ema) / pip`, `SELL: (h1_ema -
  price) / pip`). Motivation: on the Jun–Jul 2026 GBP/USD demo run the net
  −$370 was almost entirely concentrated in two entry types the existing
  binary H1-strict filter is blind to — over-extended chases (>= 20p past the
  H1 EMA) and just-flipped whipsaws (<= 5p, price sitting on the EMA). Of the
  10 trades with known H1 state, every entry outside the 5–20p band lost; the
  band itself held the only net-positive trades.
- **`signals.py` measures only.** Computes `levels["h1_ext_pips"]` and
  `levels["h1_ext_in_band"]`, and shadow-logs an `H1 ext | ...` line every
  cycle (grep `H1 ext`). No trading behaviour lives in signals.py.
- **`bot.py` enforces**, in the filter stack *after* the news re-derivation of
  `position_usd` and *before* units are sized (so a soft haircut is not
  clobbered and lands in the actual order size). Modes:
  - `off` — shadow only; logs the would-block, changes nothing.
  - `soft` — trade still fires at `position_usd * h1_ext_soft_haircut`
    (default 0.5). Reduces the bleed but still participates in out-of-band
    trades at reduced size.
  - `strict` — hard block with its own `SKIPPED_H1_EXT_BLOCK` status and a
    `BLOCKED_H1_EXT` signal-log label.
- **Ships on `off` deliberately.** The 5/20p edges are fitted on a single
  month (band contains 6 in-band trades), so the +$98 in-sample strict result
  is persuasive, not proof. Run in shadow, confirm the band separates winners
  out-of-sample in the logs, then promote to soft/strict. This changes no
  trade until the mode is flipped.
- **New settings keys:** `h1_ext_filter_enabled` (true), `h1_ext_mode`
  ("off"), `h1_ext_min_pips` (5.0), `h1_ext_max_pips` (20.0),
  `h1_ext_soft_haircut` (0.5). The pre-existing binary `h1_filter_mode`
  ("strict") is unchanged and independent of this band.

### Fix: version label
- **`bot_name`: "Cable AI Scalp v1.4" -> "Cable AI Scalp v1.5".** Keeps the
  Telegram banner / scheduler / config-sync logs in step with `version.py`
  (they read the displayed version from `settings.json["bot_name"]`).


## Cable AI Scalp v1.4 — 2026-06-26

### Fix: the separation filter was blocking the entire strategy
- **`ema_min_separation_pips`: 1.5 -> 0 (filter disabled).** The Stage-1 EMA
  separation filter required EMA9/EMA21 to be >= 1.5 pips apart, but it only
  applied to `"Fresh Cross"` setups and measured separation *at the cross bar* —
  where, by definition, the two EMAs have just crossed and sit ~0 pips apart. The
  result: every fresh cross was blocked (log evidence: 8/8 blocks at 0.0–0.6p,
  including a 6/6 BUY at 0.1p). Because the +3 fresh-cross score is the strategy's
  primary setup and the only path to 6/6, the strategy's core entry had, in effect,
  never traded. The only fills that got through were `EMA Trend Up` aligned
  continuations (+1, no "Fresh Cross" in the setup string, so the filter skipped
  them). Setting the threshold to 0 disables the gate (`if _ema_sep_min > 0`) and
  lets the **original strategy run as designed** — fresh cross on the cross bar,
  gated by score / H1-strict / H4-ADX / ORB / CPR / News Guard, all unchanged.
  The filter code is left in place (inert at 0) so it can be re-enabled in one
  line if a *correctly-timed* noise filter is built later from real trade data.
- No change to entry timing, scoring, or any other gate. Counter-trend fresh
  crosses remain blocked by H1-strict (correct behaviour, not the bug).

### Fix: version label
- **`bot_name`: "Cable AI Scalp v1.3" -> "Cable AI Scalp v1.4".** The Telegram
  startup banner, scheduler log, and config-sync log all read the displayed version
  from `settings.json["bot_name"]`, not from `version.py`. The initial v1.4 build
  bumped `version.py` only, so it would have booted still showing "v1.3". Now the
  label matches; on next deploy the sync log will read `v1.3 → Cable AI Scalp v1.4`,
  which is your confirmation the new bundle took.

### Fix: closed the one uncovered duplicate-fire path
- **Added `entry_reentry_gap_min` (default 10).** Existing guards already covered
  most duplicate risk: `max_concurrent_trades=1` (no second fire while a position
  is live), `sl_reentry_gap_min=10` (re-entry blocked after an SL), and the 60-min
  loss-streak cooldown. The gap: `sl_reentry_gap_min` arms only on **SL** closes,
  so after a fast **TP** within the acting candle the same still-fresh cross could
  re-fire. The new gap mirrors the SL-gap idiom but arms on **every** fill
  (`last_entry_at_sgt` recorded at fill time), blocking a second entry within
  10 min regardless of how the first closed. Set to 0 to disable. This became
  relevant only because v1.4 unblocks fresh crosses; while the separation filter
  was on, none of these paths could fire even once.



### Settings hygiene (no behavioural change to trade gating)
- **Removed dead `rr_ratio: 1.67` key.** `derive_rr_ratio()` reads the computed
  value from `levels` (25/18 = 1.39) first; the settings fallback was only reachable
  when SL/TP distances are missing, which never happens because `pair_sl_tp` always
  supplies 18/25. The key was inert and misleadingly implied a 1.67 target.
- **`tp_min_pct`: 0.35 -> 0.15.** The 25-pip TP is ~0.19% of price at current Cable
  (~1.32), so the old 0.35% threshold made the "TP >= 0.35%" row in the Telegram signal
  checklist render as a permanent FAIL on otherwise-valid setups. This row is display-only
  (`tp_ok` is hardwired True in signals.py and the real RR gate is `min_rr_ratio: 1.3`),
  so no trade was ever blocked — but the message was misleading. 0.15 reflects reality
  across the recent price range.

# Changelog

## Cable AI Scalp v1.2 — 2026-06-25 — Settings centralization

Configuration refactor. No change to live trading behaviour: every effective
value is identical to v1.1 as deployed (verified by parity check). The work
closes the gaps where tunable parameters were still hardcoded or where defaults
were defined in more than one place.

### Changes
- **Scoring weights centralized.** The EMA / ORB / CPR / exhaustion point values
  (+3 / +2 / +1 / -1) are now `settings.json["score_weights"]` instead of literals
  in `signals.py`. The strategy can be re-weighted without code changes.
- **`tp_min_pct` centralized.** The TP-quality display threshold (was a hardcoded
  `0.35` in `bot.py`) is now a setting.
- **Max score derived, not hardcoded.** Every `/6` denominator in logs and Telegram
  is now computed from the weights via `signals.compute_max_score()`. Change a weight
  and the displayed ceiling tracks it automatically.
- **Single source of defaults.** The bundled `settings.json` is now the only place a
  default value lives. The duplicate `setdefault` ladders in `config_loader.py` and
  `bot.py` (`validate_settings`) — which held values that disagreed with each other
  and with `settings.json`, e.g. `margin_safety_factor` 0.6 vs 0.7, `h1_filter_mode`
  soft vs strict — have been removed. Missing keys backfill from the bundle via a
  one-level deep merge; `validate_settings()` now only validates.
- **Guardrail added.** Startup now raises if `signal_threshold` exceeds the maximum
  achievable score (which would make every trade impossible).
- **Dead code removed.** Unused `SCALP_SL_PCT` / `SCALP_TP_PCT` constants in `signals.py`.

## Cable AI Scalp v1.1 — 2026-06-25 — Consistency cleanup

Patch release on top of the v1.0 baseline. No trading-logic or strategy
changes; behaviour is identical to v1.0 as deployed. This removes latent
version-fallback inconsistencies so the single-threshold-4 baseline is
internally consistent everywhere, not just via `settings.json`.

### Changes
- Removed three latent `Tokyo=5` fallbacks that were dormant only because
  `settings.json` set Tokyo=4 explicitly: the second `setdefault('Tokyo', 5)`
  in `config_loader.py`, the session-table fallback in `bot.py` (`_build_sessions`),
  and the `bot.py` header docstring. All now read 4. Prevents a silent revert
  to the old Tokyo gate if the Tokyo key were ever absent from settings.
- Corrected the stale Tokyo fresh-cross override comment that still claimed
  "trend setups need ≥5." The override block is inert at baseline (fires only
  when a session threshold exceeds 4) and is retained for future use.

## Cable AI Scalp v1.0 — 2026-06-25 — Baseline reset

Rebaselined the bot to **v1.0** as the clean reference point. No strategy
logic was rewritten; this consolidates the existing engine (EMA crossover +
ORB + CPR bias, scored 0–6) and the v1.9 regime filters into a single
documented baseline. Version history prior to this entry is retained below
for provenance.

### Changes
- **Single session threshold = 4 across all sessions.** Tokyo threshold
  lowered 5→4 (`settings.json` + `bot.py` default). Rationale: an aligned-trend
  setup scores at most 4/6 (EMA aligned +1, fresh ORB +2, CPR +1), so a Tokyo
  gate of 5 was mathematically unreachable for non-cross setups and produced
  perpetual "Score 4/6 Watching" with zero trades. Threshold 4 aligns the gate
  with the achievable score ceiling. Scores 5–6 remain reachable only on a
  fresh EMA cross and continue to map to the full position tier.
- **Block reasons now logged to stdout.** Previously the EMA-separation, H4
  ADX, H1-strict, and generic signal-validation blocks only surfaced via
  Telegram/DB, leaving Railway stdout silent on *why* a tradeable signal did
  not fire. Each block now emits a `log.info` line (`FILTER …` / `BLOCKED …`
  with reason, score, direction, setup) so a dead week is diagnosable from the
  log alone instead of a 25k-line dig.

### Unchanged (carried into baseline)
- Scoring engine, ORB time-decay, CPR width filter, AI News Guard,
  position-sizing tiers ($90 partial / $120 full), all session/news/spread
  limits, and the v1.9 EMA-separation + H4-ADX regime filters.

---

## Cable AI Scalp v1.9 — 2026-05-30 — Market regime filters

### Background
May 19–30 produced 9 consecutive losses (0W/9L). Analysis showed GBP/USD
entered a ranging/choppy market where EMA crossovers were false signals.
The strategy is trend-following by nature and requires a trending market.
Two filters added to detect and skip ranging conditions.

### Stage 1 — EMA Separation Filter (signals.py, bot.py)

A fresh EMA cross where EMA9 and EMA21 are nearly identical (< 1.5 pips apart)
is noise, not momentum. All 9 recent losses had EMA separation under 1 pip at
entry. Minimum separation of 1.5 pips required for fresh cross signals to fire.

Setting: `ema_min_separation_pips: 1.5`
Applies to: EMA Fresh Cross Up / Fresh Cross Down setups only
Trend setups (EMA Trend Up/Down) not affected

### Stage 2 — H4 ADX Trend Strength Filter (signals.py, bot.py)

ADX (Average Directional Index) measures trend strength independent of direction.
ADX < 20 = ranging/weak market → all entries blocked
ADX >= 20 = trending market → entries allowed

- Calculated on H4 candles (14-period)
- One extra OANDA API call per cycle (H4 candles)
- Fail-open: if fetch fails, trending=True so trades are not blocked

Settings: `h4_adx_filter_enabled: true`, `h4_adx_period: 14`, `h4_adx_threshold: 20.0`

### Also updated
- `telegram_templates.py` — H4 ADX shown on all signal cards (WATCHING/BLOCKED/READY)
- `config_loader.py` — new setting defaults registered
- `settings.json` — new settings added
- `SETTINGS.md` — ADX and EMA separation documented

### From v1.8
- ORB hard block remains removed (scoring handles stale ORB via 0-point decay)

---

## Cable AI Scalp v1.8 — 2026-05-19 — Remove ORB max age hard block
