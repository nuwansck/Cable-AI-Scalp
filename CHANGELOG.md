# Changelog

## Cable AI Scalp v1.7 — 2026-05-15 — Sync with Cable Scalp v2.18

### Fix 1 — oanda_trader.py debug logs added
get_recent_closed_trades now logs total returned count, lastTransactionID,
and a warning when trades are returned but none match the CLOSED filter.
Matches Cable Scalp v2.18.

---

## Cable AI Scalp v1.6 — 2026-05-15 — Remove news block count, fix double flag
