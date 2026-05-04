# Changelog

## Cable AI Scalp v1.2 — 2026-05-04 — Schedule refinement, weekly CSV export, import fix

### Bug fix — `_clean_session` not imported in `bot.py`

Every trade cycle crashed with `NameError: name '_clean_session' is not defined`
the moment Tokyo session opened on Monday (08:02 SGT). The helper existed in
`telegram_templates.py` but was never added to the `from telegram_templates import (...)`
block in `bot.py`. Sunday masked the bug because the Sunday guard exits before
the affected line is reached.

**Fix:** `_clean_session` added to the import block in `bot.py` (line 56),
alongside the existing `msg_ai_guard_result`.

### Report schedule changes

| Report | Before | After |
|---|---|---|
| Daily summary | 04:00 SGT | **07:50 SGT** |
| Weekly report | 08:15 SGT | **08:00 SGT** |
| Weekly trade export | 08:20 SGT | **08:05 SGT** |
| Monthly report | 08:00 SGT | **08:10 SGT** |

Daily report moved to 07:50 SGT — after US Continuation closes at 04:00,
capturing the full overnight session before the dead zone begins.

### Weekly export changed from JSON → CSV

`send_weekly_export` now sends `cable_ai_scalp_trades_to_YYYY-MM-DD.csv`
instead of the raw `trade_history.json`. CSV columns are identical to the
monthly export: `date_sgt`, `time_sgt`, `session`, `direction`, `score`,
`result`, `pl_usd`, `balance`, `h1_trend`, `h1_aligned`, `ema_pts`, `orb_pts`,
`cpr_pts`, `duration_min`, `spread_pips`, `units`, `position_usd`.

Both weekly and monthly exports now open directly in Excel with consistent
column layout. The JSON file is no longer sent via Telegram.

### Dead code removed

`msg_session_cap()` in `telegram_templates.py` was never imported or called
anywhere in the codebase. Removed.

### Stale references cleaned up

All timing references in `reporting.py`, `scheduler.py`, `README.md`,
`CONFLUENCE_READY.md`, and `SETTINGS.md` updated to reflect the new schedule.
`_V16_START` / `v16` / `v2.3` labels in `reporting.py` updated to version-neutral
names (`_DEPLOY_START`, `cable_ai_scalp_trades_to_`).

### Files changed

`bot.py`, `reporting.py`, `scheduler.py`, `telegram_templates.py`,
`settings.json`, `version.py`, `config_loader.py`, `README.md`, `SETTINGS.md`,
`CONFLUENCE_READY.md`, `CHANGELOG.md`

---

## Cable AI Scalp v1.1

- Rebranded separate bot from Cable AI Scalp v1.1 to Cable AI Scalp v1.1.
- Added optional OpenAI AI News Guard adapted from Rogue-H1 v2.7.
- AI guard checks GBP/USD news risk only after a valid technical setup.
- Calendar hard-lock remains priority and cannot be overridden by AI.
- Added Telegram AI caution/block messages.
- Added settings and Railway env support for AI guard.
- Added `openai` package dependency.

