# Cable AI Scalp v1.0

Separate AI-enabled GBP/USD scalping bot based on Cable AI Scalp v1.0, with the Rogue-H1 v2.7 AI News Guard pattern adapted for Cable.

## Purpose

Run this as a separate Railway service to compare normal Cable AI Scalp behavior against an AI-assisted news-risk guard.

## Strategy

- Pair: GBP/USD
- Timeframe: M5
- Core strategy: EMA + ORB + CPR
- H1 filter: strict by default
- SL/TP: configured in `pair_sl_tp`
- Risk sizing: fixed USD risk by score
- AI layer: optional OpenAI News Guard, used only after a valid technical setup exists

## AI News Guard

The AI guard does **not** create signals and does **not** change entry, SL, TP, or risk.

Flow:

1. Technical strategy finds a valid setup.
2. Calendar news hard lock/penalty runs first.
3. Spread/margin guards run.
4. AI News Guard reviews GBP/USD news risk.
5. AI can return `ALLOW`, `CAUTION`, or `BLOCK`.

Required Railway variable when enabled:

```text
OPENAI_API_KEY=your_openai_api_key
```

Optional override:

```text
AI_NEWS_GUARD_ENABLED=true
```

## Current baseline settings

- Bot name: Cable AI Scalp v1.0
- Risk: $60 score 4 / $75 score 5–6
- Relevant news currencies: GBP + USD
- AI model: gpt-4o-mini
- AI scores checked: 4, 5, 6
- AI fail mode: fail-open by default
- Max open trades: 1
- Session max trades: 4

## Safety design

Calendar hard-lock remains priority. AI cannot override a fixed high-impact news block. If OpenAI API fails and fail-closed is false, the bot allows normal rule-based operation.
