# Cable AI Scalp v1.2

Automated GBP/USD M5 scalping bot with EMA + ORB + CPR signal engine, H1 STRICT trend filter, AI News Guard, and market regime filters (EMA separation + H4 ADX).

## Strategy

- **Pair:** GBP/USD (Cable)
- **Timeframe:** M5 (5-minute candles)
- **Cycle:** Every 3 minutes
- **Signal engine:** EMA crossover + ORB break + CPR bias (scored 0–6/6)
- **H1 filter:** STRICT — BUY needs H1 BULLISH, SELL needs H1 BEARISH
- **SL:** 18 pips | **TP:** 25 pips | **RR:** 1.39
- **Risk sizing:** $90 (score 4) / $120 (score 5–6)

## Sessions (SGT = UTC+8)

| Session | Hours | Min score |
|---|---|---|
| Dead zone | 04:00–05:59 | — |
| Tokyo | 08:00–15:59 | ≥5 (fresh cross ≥4) |
| London | 16:00–20:59 | ≥4 |
| US session | 21:00–23:59 | Disabled |
| US Cont. | 00:00–03:59 | ≥4 |

## Market Regime Filters (v1.2)

### Stage 1 — EMA Separation Filter
Fresh cross signals require EMA9 and EMA21 to be at least 1.5 pips apart. Closer crosses are noise, not momentum.

### Stage 2 — H4 ADX Filter
ADX (Average Directional Index) measured on H4 candles. ADX < 20 = ranging market, all entries blocked. ADX ≥ 20 = trending, entries allowed. Fail-open if fetch fails.

## AI News Guard
After a valid technical setup, GPT-4o-mini reviews GBP/USD news risk and returns ALLOW / CAUTION / BLOCK. Does not change SL, TP, or risk sizing. All decisions tracked with virtual outcome logging.

Required Railway variable:
```
OPENAI_API_KEY=your_openai_api_key
```

## Deployment
Railway service. All config in `settings.json`. Data persisted in `/data` volume.
