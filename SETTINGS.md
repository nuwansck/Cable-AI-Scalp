# Cable AI Scalp v1.2 — Settings Reference

All settings live in `settings.json`. Overrides via Railway environment variables where noted.

---

## Identity
| Setting | Value |
|---|---|
| `bot_name` | `Cable AI Scalp v1.2` |

---

## Position Sizing
| Setting | Value | Description |
|---|---|---|
| `position_partial_usd` | `90` | USD risk for score 4 entries |
| `position_full_usd` | `120` | USD risk for score 5–6 entries |
| `margin_safety_factor` | `0.7` | Max % of account used as margin (70%) |
| `margin_retry_safety_factor` | `0.3` | Retry margin safety on rejection |
| `auto_scale_on_margin_reject` | `true` | Auto-scale units if OANDA rejects |

---

## Trade Parameters
| Setting | Value | Description |
|---|---|---|
| `pair_sl_tp.GBP_USD.sl_pips` | `18` | Stop loss in pips |
| `pair_sl_tp.GBP_USD.tp_pips` | `25` | Take profit in pips |
| `min_rr_ratio` | `1.3` | Minimum RR ratio required |
| `tp_min_pct` | `0.35` | Min TP distance (% of price) shown in the signal quality check |
| `max_concurrent_trades` | `1` | Max 1 open trade at a time |
| `max_trades_day` | `12` | Max trades per day |
| `max_losing_trades_day` | `4` | Daily loss cap |
| `loss_streak_cooldown_min` | `60` | Cooldown after SL hit (minutes) |
| `sl_reentry_gap_min` | `10` | Min gap before re-entry after SL |
| `breakeven_enabled` | `false` | Breakeven stop (currently off) |

---

## Score Weights
Point values that build the signal score. Max achievable score = `ema_fresh_cross + orb_fresh + cpr_bias` (default 6); the `signal_threshold` gate and every `/N` denominator are derived from these, so tuning a weight automatically updates them. The exhaustion penalty is negative and never adds to the ceiling.

| Setting | Value | Description |
|---|---|---|
| `score_weights.ema_fresh_cross` | `3` | Fresh EMA9/EMA21 cross in trade direction |
| `score_weights.ema_aligned` | `1` | EMAs aligned, no fresh cross |
| `score_weights.orb_fresh` | `2` | ORB break, fresh (< `orb_fresh_minutes`) |
| `score_weights.orb_aging` | `1` | ORB break, aging |
| `score_weights.orb_stale` | `0` | ORB break, stale (> `orb_aging_minutes`) |
| `score_weights.cpr_bias` | `1` | Price on correct side of CPR pivot |
| `score_weights.exhaustion_penalty` | `-1` | Over-stretched vs ATR (non-ORB entries) |

---

## Sessions
| Setting | Value | Description |
|---|---|---|
| `dead_zone_start_hour` | `4` | Dead zone start (SGT) |
| `dead_zone_end_hour` | `5` | Dead zone end (SGT) — 04:00–05:59 |
| `friday_cutoff_hour_sgt` | `23` | No new entries after 23:00 SGT Friday |
| `session_thresholds.Tokyo` | `5` | Min score for Tokyo trend setups |
| `session_thresholds.London` | `4` | Min score for London |
| `session_thresholds.US_Cont` | `4` | Min score for US Cont. |
| `tokyo_fresh_cross_min_score` | `4` | Tokyo fresh cross override threshold |

---

## Signal Filters
| Setting | Value | Description |
|---|---|---|
| `h1_filter_enabled` | `true` | H1 trend alignment filter |
| `h1_filter_mode` | `strict` | BUY needs H1 BULLISH, SELL needs H1 BEARISH |
| `cpr_max_width_pct` | `0.30` | Skip if CPR width > 0.30% |
| `orb_max_age_minutes` | `120` | Reference only — no hard block (scoring handles decay) |

---

## Market Regime Filters (v1.2)

### Stage 1 — EMA Separation Filter
| Setting | Default | Description |
|---|---|---|
| `ema_min_separation_pips` | `1.5` | Min pips between EMA9 and EMA21 on fresh cross. Set 0 to disable. |

### Stage 2 — H4 ADX Trend Strength Filter
| Setting | Default | Description |
|---|---|---|
| `h4_adx_filter_enabled` | `true` | Enable/disable H4 ADX filter |
| `h4_adx_period` | `14` | ADX calculation period (H4 candles) |
| `h4_adx_threshold` | `20.0` | ADX < 20 = ranging (block). ADX ≥ 20 = trending (allow). |

**ADX guidance:**
- ADX < 20 → Ranging market, entries blocked
- ADX 20–25 → Weak trend, entries allowed
- ADX 25–40 → Strong trend, ideal conditions
- ADX > 40 → Very strong trend

---

## News Filter
| Setting | Value | Description |
|---|---|---|
| `news_filter_enabled` | `true` | Hard lock + penalty around high-impact events |
| `news_fail_closed` | `true` | If calendar unavailable, block all entries |
| `calendar_cache_max_age_hours` | `24` | Max cache age before treat as missing |

---

## AI News Guard
| Setting | Value | Description |
|---|---|---|
| `ai_news_guard_enabled` | `true` | Enable AI guard |
| `ai_news_guard_model` | `gpt-4o-mini` | OpenAI model |
| `ai_news_guard_apply_to_scores` | `[4,5,6]` | Scores that get AI review |
| `ai_news_guard_fail_closed` | `false` | Fail-open if OpenAI unreachable |

Railway variable: `OPENAI_API_KEY=your_key`
Optional override: `AI_NEWS_GUARD_ENABLED=true`

---

## Reporting
| Setting | Value |
|---|---|
| `daily_report_hour_sgt` | `7` |
| `daily_report_minute_sgt` | `50` |
| `telegram_min_score_alert` | `4` |
