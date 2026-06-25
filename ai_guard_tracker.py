"""ai_guard_tracker.py — AI News Guard decision history and virtual outcome tracking.

This module is observability only. It does not create signals, change scores,
change order size, or place/close real trades.

It records every AI News Guard decision and, for AI-blocked setups, tracks a
virtual TP/SL outcome so reports can estimate whether AI avoided a loser or
blocked a winner.
"""
from __future__ import annotations

import csv
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytz

from config_loader import DATA_DIR

log = logging.getLogger(__name__)
SGT = pytz.timezone("Asia/Singapore")

AI_GUARD_HISTORY_FILE = Path(DATA_DIR) / "ai_guard_history.json"
AI_GUARD_CSV_FILE = Path(DATA_DIR) / "ai_guard_history.csv"

_FIELDNAMES = [
    "decision_id", "checked_at_sgt", "instrument", "session", "macro_session",
    "direction", "score", "risk_level", "action", "reason", "model",
    "trade_allowed", "trade_id", "actual_status", "actual_pnl_usd", "actual_closed_at_sgt",
    "entry", "sl_price", "tp_price", "sl_pips", "tp_pips",
    "estimated_risk_usd", "estimated_reward_usd",
    "virtual_tracking", "virtual_status", "virtual_result", "virtual_pnl_usd",
    "virtual_closed_at_sgt", "virtual_expiry_sgt", "virtual_close_reason",
]


def _now_sgt_str() -> str:
    return datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")


def _parse_sgt(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return SGT.localize(datetime.strptime(str(value)[:19], fmt))
        except Exception:
            pass
    return None


def _load() -> list[dict[str, Any]]:
    try:
        if not AI_GUARD_HISTORY_FILE.exists():
            return []
        data = json.loads(AI_GUARD_HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as exc:
        log.warning("ai_guard_tracker: could not read history: %s", exc)
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    AI_GUARD_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = AI_GUARD_HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(AI_GUARD_HISTORY_FILE)
    _write_csv(rows)


def _write_csv(rows: list[dict[str, Any]]) -> None:
    try:
        AI_GUARD_CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
        with AI_GUARD_CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in _FIELDNAMES})
    except Exception as exc:
        log.warning("ai_guard_tracker: could not write CSV: %s", exc)


def record_ai_decision(*, settings: dict[str, Any], payload: dict[str, Any], ai_result: dict[str, Any],
                       entry: float, sl_price: float, tp_price: float,
                       estimated_risk_usd: float, estimated_reward_usd: float,
                       sl_pips: int | float, tp_pips: int | float) -> str | None:
    """Append one AI decision and return decision_id.

    For BLOCK decisions, virtual tracking is enabled by default so the bot can
    later classify whether virtual TP or virtual SL would have hit first.
    """
    if not bool(settings.get("ai_tracking_enabled", True)):
        return None

    now_sgt = str(payload.get("time_sgt") or _now_sgt_str())
    action = str(ai_result.get("action", "ALLOW")).upper()
    risk_level = str(ai_result.get("risk_level", "LOW")).upper()
    expiry_hours = float(settings.get("ai_tracking_virtual_expiry_hours", settings.get("max_trade_duration_hours", 4)) or 4)
    start_dt = _parse_sgt(now_sgt) or datetime.now(SGT)
    expiry_sgt = (start_dt + timedelta(hours=expiry_hours)).strftime("%Y-%m-%d %H:%M:%S")
    virtual_tracking = bool(settings.get("ai_tracking_track_blocked_setups", True)) and action == "BLOCK"

    row = {
        "decision_id": uuid.uuid4().hex[:12],
        "checked_at_sgt": now_sgt,
        "instrument": payload.get("instrument", "GBP_USD"),
        "session": payload.get("session", ""),
        "macro_session": payload.get("macro_session", ""),
        "direction": str(payload.get("direction", "")).upper(),
        "score": payload.get("technical_score"),
        "risk_level": risk_level,
        "action": action,
        "reason": str(ai_result.get("reason", ""))[:240],
        "model": ai_result.get("model") or settings.get("ai_news_guard_model", "gpt-4o-mini"),
        "trade_allowed": action != "BLOCK",
        "trade_id": None,
        "actual_status": "PENDING" if action != "BLOCK" else "NOT_PLACED",
        "actual_pnl_usd": None,
        "actual_closed_at_sgt": None,
        "entry": round(float(entry), 6),
        "sl_price": round(float(sl_price), 6),
        "tp_price": round(float(tp_price), 6),
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "estimated_risk_usd": round(float(estimated_risk_usd or 0), 2),
        "estimated_reward_usd": round(float(estimated_reward_usd or 0), 2),
        "virtual_tracking": virtual_tracking,
        "virtual_status": "OPEN" if virtual_tracking else "N/A",
        "virtual_result": None,
        "virtual_pnl_usd": None,
        "virtual_closed_at_sgt": None,
        "virtual_expiry_sgt": expiry_sgt if virtual_tracking else None,
        "virtual_close_reason": None,
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row["decision_id"]


def link_trade(decision_id: str | None, trade_id: str | None) -> None:
    if not decision_id or not trade_id:
        return
    rows = _load()
    changed = False
    for row in rows:
        if row.get("decision_id") == decision_id:
            row["trade_id"] = str(trade_id)
            row["actual_status"] = "OPEN"
            changed = True
            break
    if changed:
        _save(rows)


def mark_trade_failed(decision_id: str | None, reason: str = "ORDER_FAILED") -> None:
    if not decision_id:
        return
    rows = _load()
    changed = False
    for row in rows:
        if row.get("decision_id") == decision_id:
            row["actual_status"] = "FAILED"
            row["actual_closed_at_sgt"] = _now_sgt_str()
            row["virtual_close_reason"] = reason
            changed = True
            break
    if changed:
        _save(rows)


def backfill_actual_trade_result(trade_id: str | None, pnl_usd: float | int | None, closed_at_sgt: str | None = None) -> None:
    if not trade_id or not isinstance(pnl_usd, (int, float)):
        return
    rows = _load()
    changed = False
    for row in rows:
        if str(row.get("trade_id") or "") == str(trade_id):
            row["actual_status"] = "WIN" if pnl_usd > 0 else ("LOSS" if pnl_usd < 0 else "BE")
            row["actual_pnl_usd"] = round(float(pnl_usd), 2)
            row["actual_closed_at_sgt"] = closed_at_sgt or _now_sgt_str()
            changed = True
    if changed:
        _save(rows)


def update_blocked_virtual_outcomes(trader: Any, instrument: str, now_sgt: datetime | None = None) -> dict[str, int]:
    """Update virtual outcome for AI-blocked setups for one instrument.

    Uses current bid/ask snapshot. This is a best-effort counterfactual only;
    it does not guarantee tick-perfect TP/SL sequencing if both levels were
    touched between cycles.
    """
    now_sgt = now_sgt or datetime.now(SGT)
    rows = _load()
    open_rows = [r for r in rows if r.get("instrument") == instrument and r.get("virtual_status") == "OPEN"]
    if not open_rows:
        return {"updated": 0, "expired": 0, "open": 0}

    try:
        mid, bid, ask = trader.get_price(instrument)
    except Exception as exc:
        log.warning("ai_guard_tracker: get_price failed for virtual tracking: %s", exc)
        return {"updated": 0, "expired": 0, "open": len(open_rows)}
    if bid is None or ask is None:
        return {"updated": 0, "expired": 0, "open": len(open_rows)}

    updated = expired = 0
    for row in rows:
        if row.get("instrument") != instrument or row.get("virtual_status") != "OPEN":
            continue
        direction = str(row.get("direction", "")).upper()
        sl = float(row.get("sl_price") or 0)
        tp = float(row.get("tp_price") or 0)
        hit = None
        if direction == "BUY":
            if bid <= sl:
                hit = "LOSS"
            elif bid >= tp:
                hit = "WIN"
        elif direction == "SELL":
            if ask >= sl:
                hit = "LOSS"
            elif ask <= tp:
                hit = "WIN"

        if hit:
            row["virtual_status"] = "CLOSED"
            row["virtual_result"] = hit
            row["virtual_closed_at_sgt"] = now_sgt.strftime("%Y-%m-%d %H:%M:%S")
            row["virtual_close_reason"] = "TP_HIT" if hit == "WIN" else "SL_HIT"
            row["virtual_pnl_usd"] = round(
                float(row.get("estimated_reward_usd") or 0) if hit == "WIN"
                else -float(row.get("estimated_risk_usd") or 0), 2
            )
            updated += 1
            continue

        expiry = _parse_sgt(row.get("virtual_expiry_sgt"))
        if expiry and now_sgt >= expiry:
            row["virtual_status"] = "EXPIRED"
            row["virtual_result"] = "EXPIRED"
            row["virtual_closed_at_sgt"] = now_sgt.strftime("%Y-%m-%d %H:%M:%S")
            row["virtual_close_reason"] = "EXPIRY"
            row["virtual_pnl_usd"] = 0.0
            expired += 1

    if updated or expired:
        _save(rows)
    remaining_open = sum(1 for r in rows if r.get("instrument") == instrument and r.get("virtual_status") == "OPEN")
    return {"updated": updated, "expired": expired, "open": remaining_open}


def summarize_ai_tracking(start_sgt: datetime | None = None, end_sgt: datetime | None = None) -> dict[str, Any]:
    rows = _load()
    filtered = []
    for row in rows:
        dt = _parse_sgt(row.get("checked_at_sgt"))
        if start_sgt and (not dt or dt < start_sgt):
            continue
        if end_sgt and (not dt or dt >= end_sgt):
            continue
        filtered.append(row)

    allowed = [r for r in filtered if r.get("action") == "ALLOW"]
    caution = [r for r in filtered if r.get("action") == "CAUTION"]
    blocked = [r for r in filtered if r.get("action") == "BLOCK"]
    blocked_winners = [r for r in blocked if r.get("virtual_result") == "WIN"]
    blocked_losers = [r for r in blocked if r.get("virtual_result") == "LOSS"]
    blocked_expired = [r for r in blocked if r.get("virtual_result") == "EXPIRED"]
    blocked_open = [r for r in blocked if r.get("virtual_status") == "OPEN"]

    def _sum_actual(group: list[dict[str, Any]]) -> float:
        return round(sum(float(r.get("actual_pnl_usd") or 0) for r in group), 2)

    virtual_pnl = round(sum(float(r.get("virtual_pnl_usd") or 0) for r in blocked if r.get("virtual_pnl_usd") is not None), 2)
    # Positive means AI helped by avoiding negative virtual P&L. Negative means AI likely blocked winners.
    estimated_ai_impact = round(-virtual_pnl, 2)

    return {
        "total_decisions": len(filtered),
        "allowed": len(allowed),
        "cautioned": len(caution),
        "blocked": len(blocked),
        "allowed_closed": sum(1 for r in allowed if r.get("actual_status") in ("WIN", "LOSS", "BE")),
        "caution_closed": sum(1 for r in caution if r.get("actual_status") in ("WIN", "LOSS", "BE")),
        "allowed_pnl_usd": _sum_actual(allowed),
        "caution_pnl_usd": _sum_actual(caution),
        "blocked_winners": len(blocked_winners),
        "blocked_losers": len(blocked_losers),
        "blocked_expired": len(blocked_expired),
        "blocked_open": len(blocked_open),
        "blocked_virtual_pnl_usd": virtual_pnl,
        "estimated_ai_impact_usd": estimated_ai_impact,
        "csv_path": str(AI_GUARD_CSV_FILE),
        "json_path": str(AI_GUARD_HISTORY_FILE),
    }


def get_ai_guard_csv_path() -> Path:
    return AI_GUARD_CSV_FILE
