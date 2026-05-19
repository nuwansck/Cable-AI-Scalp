# Changelog

## Cable AI Scalp v1.8 — 2026-05-19 — Remove ORB max age hard block

### Change — ORB hard block removed (bot.py)

The ORB max age signal blocker (added in v1.5) has been removed.

Reason: the scoring system already penalises stale ORBs correctly:
- 0–60min: +2 points (fresh break)
- 60–120min: +1 point (aging)
- 120min+: +0 points (stale, no contribution)

When a signal scores 4/6 with a 365-minute ORB, the score is built entirely
on EMA cross (+3) and CPR bias (+1) — the ORB contributed zero points.
The hard block was double-penalising stale ORBs that were already excluded
from scoring, and blocking valid signals based on independent factors.

Evidence: May 19 — three BUY 4/6 signals at 14:05, 14:08, 14:32 SGT blocked
with H1 BULLISH aligned. These were likely valid entries that would have hit TP.

The orb_max_age_minutes setting remains in settings.json for reference but
is no longer used as a hard blocker. ORB scoring decay is unchanged.

---

## Cable AI Scalp v1.7 — 2026-05-15 — Add oanda_trader debug logs
