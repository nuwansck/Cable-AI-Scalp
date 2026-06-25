from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('DATA_DIR', '/data')).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS_PATH = BASE_DIR / 'settings.json'           # canonical defaults
EXAMPLE_SETTINGS_PATH = BASE_DIR / 'settings.json.example'   # fallback if above missing
SETTINGS_FILE = DATA_DIR / 'settings.json'                   # live copy on the volume
SECRETS_JSON_PATH = BASE_DIR / 'secrets.json'

# run-once guard — ensure_persistent_settings only syncs once per process.
_settings_synced: bool = False


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as exc:
        logger.warning('Failed to read %s: %s', path, exc)
    return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def _load_defaults() -> dict:
    """The bundled settings.json is the ONE place default values live.

    Falls back to settings.json.example only if the primary bundle is missing
    (e.g. excluded from deploy). Returns {} if neither is readable.
    """
    defaults = _read_json(DEFAULT_SETTINGS_PATH, {})
    if isinstance(defaults, dict) and defaults:
        return defaults
    if EXAMPLE_SETTINGS_PATH.exists():
        logger.warning(
            'settings.json not found at %s — falling back to settings.json.example.',
            DEFAULT_SETTINGS_PATH,
        )
        fallback = _read_json(EXAMPLE_SETTINGS_PATH, {})
        if isinstance(fallback, dict):
            return fallback
    return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """Return base overlaid with override. Nested dicts merge one level deep so
    partial sub-blocks (e.g. spread_limits, pair_sl_tp, score_weights) still pick
    up any missing sub-keys from defaults. Lists and scalars: override wins.
    """
    out = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            merged = dict(out[key])
            merged.update(val)
            out[key] = merged
        else:
            out[key] = val
    return out


def ensure_persistent_settings() -> Path:
    """Sync the bundled settings.json onto the Railway volume on startup.

    The volume stores trade STATE, not configuration — config always comes from
    the deployed bundle. Runs once per process.
    """
    global _settings_synced
    if _settings_synced:
        return SETTINGS_FILE

    defaults = _load_defaults()
    if not defaults:
        logger.warning(
            'Bundled settings.json not found or empty at %s — '
            'volume settings left unchanged.',
            DEFAULT_SETTINGS_PATH,
        )
        _settings_synced = True
        return SETTINGS_FILE

    old_name = 'none'
    if SETTINGS_FILE.exists():
        old = _read_json(SETTINGS_FILE, {})
        if isinstance(old, dict):
            old_name = old.get('bot_name', 'unknown')

    _write_json(SETTINGS_FILE, defaults)
    _settings_synced = True

    new_name = defaults.get('bot_name', 'unknown')
    if old_name != new_name:
        logger.info('Settings synced on startup: %s → %s', old_name, new_name)
    else:
        logger.info('Settings synced on startup: %s (refreshed from bundle)', new_name)
    return SETTINGS_FILE


# ── load_settings cache ──────────────────────────────────────────────────────
# Invalidated when the volume file mtime changes, so manual edits to the volume
# settings.json take effect on the next cycle.
_settings_cache: dict = {}
_settings_mtime: float = 0.0


def load_settings() -> dict:
    """Return the effective settings: volume file overlaid on bundled defaults.

    Defaults live in exactly one file (the bundled settings.json), so there is
    no second copy of any value to drift out of sync.
    """
    global _settings_cache, _settings_mtime
    ensure_persistent_settings()

    try:
        mtime = SETTINGS_FILE.stat().st_mtime
    except OSError:
        mtime = 0.0

    if _settings_cache and mtime == _settings_mtime:
        return _settings_cache

    volume = _read_json(SETTINGS_FILE, {})
    if not isinstance(volume, dict):
        volume = {}
    original_keys = set(volume.keys())

    settings = _deep_merge(_load_defaults(), volume)

    # Optional Railway env override (highest priority).
    env_ai_enabled = os.environ.get('AI_NEWS_GUARD_ENABLED')
    if env_ai_enabled is not None:
        settings['ai_news_guard_enabled'] = (
            env_ai_enabled.strip().lower() in {'1', 'true', 'yes', 'on'}
        )

    # Persist backfilled keys so the volume file stays self-describing.
    if set(settings.keys()) != original_keys:
        _write_json(SETTINGS_FILE, settings)

    _settings_cache = settings
    _settings_mtime = mtime
    return settings


def save_settings(settings: dict) -> None:
    _write_json(SETTINGS_FILE, settings)
    logger.info('Saved settings -> %s', SETTINGS_FILE)


def load_secrets() -> dict:
    """Load secrets with environment variables taking priority over secrets.json."""
    file_secrets: dict = {}
    if SECRETS_JSON_PATH.exists():
        loaded = _read_json(SECRETS_JSON_PATH, {})
        if isinstance(loaded, dict):
            file_secrets = loaded

    return {
        'OANDA_API_KEY':    os.environ.get('OANDA_API_KEY')    or file_secrets.get('OANDA_API_KEY',    ''),
        'OANDA_ACCOUNT_ID': os.environ.get('OANDA_ACCOUNT_ID') or file_secrets.get('OANDA_ACCOUNT_ID', ''),
        'TELEGRAM_TOKEN':   os.environ.get('TELEGRAM_TOKEN')   or file_secrets.get('TELEGRAM_TOKEN',   ''),
        'TELEGRAM_CHAT_ID': os.environ.get('TELEGRAM_CHAT_ID') or file_secrets.get('TELEGRAM_CHAT_ID', ''),
        'DATA_DIR':         str(DATA_DIR),
    }


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}
