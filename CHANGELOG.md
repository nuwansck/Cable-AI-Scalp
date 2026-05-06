# Changelog

## Cable AI Scalp v1.3 — 2026-05-06 — Remove force-close + backport all v2.15 fixes

### Summary

All force-close logic removed. Backported every bug fix from Cable Scalp v2.15.
AI News Guard and AI Guard Tracker are untouched.

### Force-close removed (bot.py, oanda_trader.py, settings)

Identical to the Cable Scalp v2.15 cleanup. Every trade has a hard SL and TP
set on OANDA at entry — OANDA closes the trade regardless of bot state.
The bot-side force-close was the source of the entire v2.5–v2.14 bug chain.

- Removed force_close_stale_trades() function from bot.py
- Removed the call site and _sess_end_h variable from the main cycle
- Removed the dead zone management fallthrough (open-trade management no longer
  needed during 04:00–07:59 SGT — OANDA SL/TP handles it)
- Dead zone / outside-session handling restored to clean single early-return
- Removed max_trade_duration_hours and force_close_at_session_end settings defaults
- Removed max_trade_duration_hours and force_close_at_session_end from settings.json
- Removed close_trade() and get_today_closed_transactions() from oanda_trader.py

### Backported fixes from Cable Scalp v2.15

get_recent_closed_trades() now queries state=ALL and filters state=CLOSED in
Python, bypassing OANDA index quirks where recently-closed trades are sometimes
absent from the state=CLOSED result set.

startup_oanda_reconcile() now uses get_recent_closed_trades() (proven endpoint)
instead of get_today_closed_transactions() (broken — OANDA returns a pagination
envelope, not transactions, and the function was always silently returning []).

### AI integration unchanged

ai_news_guard.py, ai_guard_tracker.py, and all AI-related bot.py code are
identical to v1.2. Requires OPENAI_API_KEY env var when ai_news_guard_enabled=true.

---

## Cable AI Scalp v1.2 — 2026-05-04 — Schedule refinement, weekly CSV export, import fix
