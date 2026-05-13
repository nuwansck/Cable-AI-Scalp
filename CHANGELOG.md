# Changelog

## Cable AI Scalp v1.4 — 2026-05-13 — Narrower dead zone + Tokyo fresh-cross threshold

### Change 1 — Dead zone narrowed to 04:00–05:59 SGT (was 04:00–07:59)

The 06:00–07:59 window is Asian pre-Tokyo overlap, not a dead market. Liquidity is
present and directional moves happen. The genuine dead period is 04:00–05:59 (thin
post-US, pre-Asia). From 06:00 onwards the bot now scans and can enter trades.

Evidence: May 11 2026 — four 4/6 BUY fresh-cross signals fired at 06:20, 06:23,
06:41, 06:44 SGT while GBP/USD was trending strongly upward. All were blocked by
the dead zone. These would almost certainly have been TP hits.

Setting changed: `dead_zone_end_hour: 7 → 5`

### Change 2 — Tokyo fresh-cross signals allowed at score ≥4 (trend setups still ≥5)

Tokyo threshold ≥5 was filtering out most Tokyo setups. A fresh EMA cross in Tokyo
(EMA Fresh Cross Up/Down) at 4/6 already has ORB break + CPR alignment baked in —
it's a high-conviction entry. The ≥5 requirement was leaving 3-point fresh-cross
signals on the table unnecessarily.

Trend-following setups (EMA Trend Up/Down) in Tokyo remain at ≥5. The fresh-cross
specific override only applies in the Tokyo session.

H1 STRICT mode still applies to all entries — counter-trend setups blocked regardless.

New setting: `tokyo_fresh_cross_min_score: 4`
New logic: in `_signal_phase`, if session=Tokyo and setup contains "Fresh Cross"
           and session threshold > 4, effective threshold is overridden to 4.

### Files changed
- `bot.py` — threshold override logic in `_signal_phase`
- `config_loader.py` — `tokyo_fresh_cross_min_score` default added
- `settings.json` / `settings.json.example` — `dead_zone_end_hour: 5`,
  `tokyo_fresh_cross_min_score: 4`, `bot_name: Cable AI Scalp v1.4`
- `version.py` — 1.4.0

---

## Cable AI Scalp v1.3 — 2026-05-06 — Remove force-close + backport all v2.15 fixes
