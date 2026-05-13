# Changelog

## Cable AI Scalp v1.5 — 2026-05-13 — ORB max age cap, CPR width filter, loss cooldown

### Change 1 — ORB max age cap (bot.py, config_loader.py)

Added a signal blocker that prevents entry when the ORB is older than
`orb_max_age_minutes` (default 120 min). Previously a 4+ hour old ORB would
still score +0 but not block the trade — price has moved too far from the
original breakout level for the ORB to be meaningful.

Setting: `orb_max_age_minutes: 120`

### Change 2 — CPR width filter (bot.py, config_loader.py)

Added a filter in `_signal_phase` that skips entry when the CPR width exceeds
`cpr_max_width_pct` (default 0.30%). On high-volatility days with a very wide
CPR, the pivot levels are too spread to act as reliable support/resistance.

Setting: `cpr_max_width_pct: 0.30`

### Change 3 — Loss streak cooldown extended to 60 minutes (bot.py)

`loss_streak_cooldown_min` increased from 30 to 60 minutes. After an SL hit
the bot now waits a full hour before re-entering. Gives the market more time
to settle and reduces the chance of a second loss in the same momentum move.

Setting: `loss_streak_cooldown_min: 60`

### Unchanged from v1.4
- Dead zone 04:00–05:59 SGT
- Tokyo fresh-cross threshold ≥4
- Position sizes $90/$120
- AI guard ON

---

## Cable AI Scalp v1.4 — 2026-05-13 — Narrower dead zone + Tokyo fresh-cross threshold
