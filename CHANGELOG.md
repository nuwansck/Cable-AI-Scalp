# Changelog

## Cable AI Scalp v1.6 — 2026-05-15

### Change 1 — Removed "Blocked: X news" from daily report (telegram_templates.py)
The news filter cycle count was noisy and not meaningful. Removed entirely.
The news filter still works — you still get the real-time "News Block" Telegram
alert when a window opens. The daily count added no value.

### Change 2 — Fixed double flag in session breakdown (reporting.py)
The session breakdown was showing "🇬🇧 🇬🇧 London" because the session_order
labels in reporting.py contained emoji AND telegram_templates._session_icon()
was adding another. Fixed by removing emoji from the labels in reporting.py —
_session_icon() now provides the single correct flag.

### Change 3 — Added last_news_block upsert_state (bot.py)
News block state is now persisted to DB on every cycle — both when blocked
(blocked=True) and when passing (blocked=False with any active penalty).
This was already in Cable Scalp v2.17 but missing from AI Scalp.

---

## Cable AI Scalp v1.5 — 2026-05-13 — ORB max age cap, CPR width filter, loss cooldown
