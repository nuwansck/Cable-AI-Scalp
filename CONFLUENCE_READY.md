# Cable AI Scalp v1.2 — Technical Specification & Operations Wiki

**Bot name:** Cable AI Scalp v1.2
**Instrument:** GBP/USD (Cable) only
**Exchange:** OANDA (demo & live)
**Deployment:** Railway (PaaS)
**Signal timeframe:** M5 (5-minute candles)
**Cycle interval:** Every 3 minutes
**Current mode:** DEMO

---

## 1. Purpose & Scope

Cable AI Scalp v1.2 is a fully automated M5 scalping bot for GBP/USD. It uses a three-component signal engine (EMA crossover + ORB + CPR bias) scored 0–6/6, with session-based thresholds and multiple quality filters. The AI News Guard adds an optional macro risk layer using GPT-4o-mini. Market regime filters (EMA separation + H4 ADX) in the baseline prevent entries in ranging/choppy conditions.

---

## 2. Architecture Overview

```
scheduler.py  (APScheduler — every 3 min)
      |
      ├── run_bot_cycle()
      |       |
      |       ├── _guard_phase()     Market closed / dead zone / caps / news
      |       ├── _signal_phase()    SignalEngine.analyze() → score + direction
      |       |       ├── EMA separation filter (Stage 1)
      |       |       ├── H4 ADX filter (Stage 2)
      |       |       ├── CPR width filter
      |       |       ├── H1 STRICT filter
      |       |       └── AI News Guard
      |       └── _execution_phase() Margin check → spread check → place_order()
      |
      ├── send_daily_report()   07:50 SGT Mon–Fri
      ├── send_weekly_report()  Monday 08:00 SGT
      └── send_monthly_report() First Monday 08:10 SGT
```

---

## 3. Signal Engine

**File:** `signals.py` → `SignalEngine.analyze()`

### 3a. EMA Crossover (M5)
| Setup | Points | Direction |
|---|---|---|
| EMA9 fresh cross above EMA21 | +3 | BUY |
| EMA9 fresh cross below EMA21 | +3 | SELL |
| EMA9 aligned above EMA21 (trend) | +1 | BUY |
| EMA9 aligned below EMA21 (trend) | +1 | SELL |

### 3b. ORB Break (Tokyo session)
| Age | Points |
|---|---|
| 0–60 min (fresh) | +2 |
| 60–120 min (aging) | +1 |
| 120+ min (stale) | +0 |

### 3c. CPR Bias
| Condition | Points |
|---|---|
| Price above CPR pivot (BUY) | +1 |
| Price below CPR pivot (SELL) | +1 |

**Maximum score:** 6/6

---

## 4. Session Schedule (SGT = UTC+8)

| Session | Hours | Min score | Notes |
|---|---|---|---|
| Dead zone | 04:00–05:59 | — | No entries |
| Tokyo | 08:00–15:59 | ≥5 | Fresh cross ≥4 |
| London | 16:00–20:59 | ≥4 | Primary session |
| US session | 21:00–23:59 | Disabled | |
| US Cont. | 00:00–03:59 | ≥4 | |
| Friday cutoff | 23:00 SGT | — | No new entries |

---

## 5. Filters & Guards

### H1 STRICT Filter
BUY requires H1 EMA BULLISH. SELL requires H1 EMA BEARISH. Counter-trend signals blocked regardless of score.

### Stage 1 — EMA Separation Filter (v1.2)
Fresh cross signals require minimum 1.5 pip separation between EMA9 and EMA21. Tight crosses are market noise. Evidence: all 9 consecutive losses in May 19–30 had EMA separation < 1 pip.

### Stage 2 — H4 ADX Filter (v1.2)
H4 ADX (14-period) calculated each cycle. ADX < 20 = ranging market, all entries blocked. ADX ≥ 20 = trending, entries allowed. Fail-open — if H4 fetch fails, trading continues.

### CPR Width Filter
CPR width > 0.30% skips cycle — pivot levels too spread to be reliable.

### News Filter
Hard lock around high-impact GBP/USD events (±30 min window). Medium-impact events apply −1 score penalty. Fail-closed: if calendar unavailable, blocks all entries.

### AI News Guard
GPT-4o-mini reviews GBP/USD macro risk after technical setup passes all other filters. Returns ALLOW / CAUTION / BLOCK. All decisions logged with virtual outcome tracking. Fail-open — API timeout never blocks a trade.

---

## 6. Risk Management

| Parameter | Value |
|---|---|
| SL | 18 pips (fixed) |
| TP | 25 pips (fixed) |
| RR | 1.39 |
| Score 4 risk | $90 |
| Score 5–6 risk | $120 |
| Margin safety | 70% of account |
| Max concurrent trades | 1 |
| Daily loss cap | 4 trades |
| Loss cooldown | 60 min after SL hit |
| Breakeven | Disabled |

---

## 7. Deployment

**Railway service** with persistent `/data` volume.

Required environment variables:
```
OANDA_API_KEY=your_oanda_key
OANDA_ACCOUNT_ID=your_account_id
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
OPENAI_API_KEY=your_openai_key
```

Optional:
```
OANDA_DEMO=true
AI_NEWS_GUARD_ENABLED=true
```

---

## 8. Version History

| Version | Date | Key changes |
|---|---|---|
| **v1.2** | 2026-06-25 | Settings centralization: score_weights + tp_min_pct moved to settings.json, max score derived, single-source defaults; no logic change |
| v1.1 | 2026-06-25 | Consistency cleanup: removed latent Tokyo=5 fallbacks; no logic change |
| v1.0 (baseline) | 2026-06-25 | Baseline reset; Tokyo threshold 5→4 (single threshold 4 all sessions); block reasons logged to stdout |
| v1.9 | 2026-05-30 | EMA separation filter + H4 ADX regime filter |
| v1.8 | 2026-05-19 | Remove ORB hard block |
| v1.7 | 2026-05-15 | oanda_trader debug logs |
| v1.6 | 2026-05-15 | Fix double session flag, remove noise news count |
| v1.5 | 2026-05-13 | ORB max age cap, CPR width filter, loss cooldown 60min |
| v1.4 | 2026-05-13 | Narrow dead zone 04:00–05:59, Tokyo fresh cross ≥4 |
| v1.3 | 2026-05-06 | Remove force-close, SL/TP on OANDA handles exits |
