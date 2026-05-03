# Cable AI Scalp v1.1 Settings

Main settings live in `settings.json`.

## Identity

```json
"bot_name": "Cable AI Scalp v1.1"
```

## Risk

```json
"position_partial_usd": 60,
"position_full_usd": 75
```

This means score 4 risks $60 and score 5–6 risks $75.

## News filter

```json
"news_filter_enabled": true,
"news_relevant_currencies": ["GBP", "USD"]
```

## AI News Guard

```json
"ai_news_guard_enabled": true,
"ai_news_guard_model": "gpt-4o-mini",
"ai_news_guard_apply_to_scores": [4, 5, 6],
"ai_news_guard_block_action": true,
"ai_news_guard_fail_closed": false,
"ai_news_guard_timeout_sec": 12
```

The AI guard only reviews news risk after the existing rule-based setup is valid. It can block/caution/allow, but it does not generate trades or change SL/TP/risk.

## Railway variables

```text
OPENAI_API_KEY=your_openai_api_key
AI_NEWS_GUARD_ENABLED=true
```

`AI_NEWS_GUARD_ENABLED` is optional and overrides the JSON setting.

## AI Guard Tracking

```json
"ai_tracking_enabled": true,
"ai_tracking_track_blocked_setups": true,
"ai_tracking_virtual_expiry_hours": 4,
"ai_tracking_export_csv": true
```

These settings enable AI decision history and blocked-trade virtual TP/SL outcome tracking. The tracking layer is reporting-only and does not affect trading decisions.
