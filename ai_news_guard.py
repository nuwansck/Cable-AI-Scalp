"""ai_news_guard.py — Cable AI Scalp v1.2 optional OpenAI news-risk guard.

This module is intentionally NOT a signal generator.
It only classifies market/news risk around an already-valid technical setup.

Hard calendar locks remain the first priority in bot.py. If the existing
GBP/USD calendar hard lock is active, bot.py blocks before calling this guard.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_ALLOWED_RISK = {"LOW", "MEDIUM", "HIGH"}
_ALLOWED_ACTION = {"ALLOW", "CAUTION", "BLOCK"}

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
        "action": {"type": "string", "enum": ["ALLOW", "CAUTION", "BLOCK"]},
        "reason": {"type": "string", "maxLength": 240},
    },
    "required": ["risk_level", "action", "reason"],
    "additionalProperties": False,
}


def _normalise(result: dict[str, Any] | None) -> dict[str, str]:
    result = result or {}
    risk = str(result.get("risk_level", "LOW")).upper().strip()
    action = str(result.get("action", "ALLOW")).upper().strip()
    reason = str(result.get("reason", "AI News Guard returned no reason.")).strip()

    if risk not in _ALLOWED_RISK:
        risk = "LOW"
    if action not in _ALLOWED_ACTION:
        action = "ALLOW"
    if not reason:
        reason = "No elevated news risk detected."
    return {"risk_level": risk, "action": action, "reason": reason[:240]}


def ai_news_guard(settings: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return LOW/MEDIUM/HIGH and ALLOW/CAUTION/BLOCK for a trade context.

    Fail-open by default: API errors return ALLOW unless settings explicitly set
    ai_news_guard_fail_closed=true. This prevents a transient API outage from
    stopping a rule-based demo bot unexpectedly.
    """
    if not bool(settings.get("ai_news_guard_enabled", False)):
        return {"enabled": False, "risk_level": "LOW", "action": "ALLOW", "reason": "AI News Guard disabled."}

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        if bool(settings.get("ai_news_guard_fail_closed", False)):
            return {"enabled": True, "risk_level": "HIGH", "action": "BLOCK", "reason": "OPENAI_API_KEY missing and fail-closed is enabled."}
        return {"enabled": True, "risk_level": "LOW", "action": "ALLOW", "reason": "OPENAI_API_KEY missing; AI guard skipped fail-open."}

    try:
        from openai import OpenAI  # imported lazily so the bot can run when disabled

        client = OpenAI(api_key=api_key, timeout=float(settings.get("ai_news_guard_timeout_sec", 12)))
        model = str(settings.get("ai_news_guard_model", "gpt-4o-mini"))
        prompt = {
            "role": "system",
            "content": (
                "You are a conservative news-risk filter for an automated GBP/USD M5 scalping trading bot. "
                "Do not predict direction. Do not generate signals. Do not change the technical score. "
                "Only classify event/headline risk for whether an already-valid technical trade should be allowed, cautioned, or blocked. "
                "Return BLOCK only for clearly elevated scheduled or unscheduled news/volatility risk."
            ),
        }
        user_msg = {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)}

        response = client.responses.create(
            model=model,
            input=[prompt, user_msg],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "cable_ai_scalp_news_guard",
                    "schema": _SCHEMA,
                    "strict": True,
                }
            },
        )
        raw = getattr(response, "output_text", "") or "{}"
        parsed = json.loads(raw)
        out = _normalise(parsed)
        out["enabled"] = True
        out["model"] = model
        return out
    except Exception as exc:
        log.warning("AI News Guard failed: %s", exc)
        if bool(settings.get("ai_news_guard_fail_closed", False)):
            return {"enabled": True, "risk_level": "HIGH", "action": "BLOCK", "reason": f"AI guard error; fail-closed active: {exc}"[:240]}
        return {"enabled": True, "risk_level": "LOW", "action": "ALLOW", "reason": f"AI guard error; fail-open: {exc}"[:240]}
