import asyncio
import json
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import open_webui.config as config_module
from open_webui.config import ENABLE_PERSISTENT_CONFIG, REDIS_KEY_PREFIX


DB_RESTORE_CONFIRMATION = "RESTORE DATABASE"
DB_RESTORE_TOKEN_TTL_SECONDS = 15 * 60


def deep_merge_dict(current: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current)

    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge_dict(merged[key], value)
        else:
            merged[key] = value

    return merged


def get_database_restore_support(engine_name: str, worker_count: int) -> dict[str, Any]:
    backend = "sqlite" if engine_name == "sqlite" else engine_name
    supported = backend == "sqlite" and worker_count == 1

    if backend != "sqlite":
        reason = "backend_not_sqlite"
    elif worker_count != 1:
        reason = "multiple_workers_not_supported"
    else:
        reason = None

    return {
        "backend": backend,
        "worker_count": worker_count,
        "supported": supported,
        "reason": reason,
    }


def ensure_db_restore_state(app):
    if not hasattr(app.state, "DB_RESTORE_LOCK"):
        app.state.DB_RESTORE_LOCK = asyncio.Lock()
    if not hasattr(app.state, "DB_RESTORE_TOKENS"):
        app.state.DB_RESTORE_TOKENS = {}

    return app.state.DB_RESTORE_LOCK, app.state.DB_RESTORE_TOKENS


def prune_db_restore_tokens(app, now: float | None = None) -> None:
    _, tokens = ensure_db_restore_state(app)
    current_time = now or time.time()

    expired_tokens = [
        token
        for token, payload in tokens.items()
        if payload.get("expires_at", 0) <= current_time
    ]

    for token in expired_tokens:
        payload = tokens.pop(token, None)
        if payload:
            cleanup_path(payload.get("path"))


def create_restore_token(app, *, path: str, filename: str, user_id: str) -> dict[str, Any]:
    _, tokens = ensure_db_restore_state(app)
    prune_db_restore_tokens(app)

    token = uuid.uuid4().hex
    payload = {
        "path": path,
        "filename": filename,
        "user_id": user_id,
        "expires_at": time.time() + DB_RESTORE_TOKEN_TTL_SECONDS,
    }
    tokens[token] = payload
    return {"token": token, **payload}


def pop_restore_token(app, token: str) -> dict[str, Any] | None:
    _, tokens = ensure_db_restore_state(app)
    prune_db_restore_tokens(app)
    return tokens.pop(token, None)


def cleanup_path(path: str | Path | None) -> None:
    if not path:
        return

    candidate = Path(path)
    try:
        if candidate.is_dir():
            for child in candidate.iterdir():
                if child.is_file():
                    child.unlink(missing_ok=True)
            candidate.rmdir()
        else:
            candidate.unlink(missing_ok=True)
            parent = candidate.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
    except Exception:
        return


def write_upload_to_temp(upload_file, prefix: str) -> Path:
    suffix = Path(upload_file.filename or "database-backup.db").suffix or ".db"
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    temp_path = temp_dir / f"{uuid.uuid4().hex}{suffix}"

    upload_file.file.seek(0)
    with temp_path.open("wb") as file_obj:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            file_obj.write(chunk)

    return temp_path


def create_sqlite_snapshot(engine, filename: str = "webui.db") -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="open-webui-db-export-"))
    snapshot_path = temp_dir / filename

    raw_connection = engine.raw_connection()
    source_connection = (
        getattr(raw_connection, "driver_connection", None)
        or getattr(raw_connection, "connection", raw_connection)
    )
    target_connection = sqlite3.connect(snapshot_path)

    try:
        source_connection.backup(target_connection)
        target_connection.commit()
    finally:
        target_connection.close()
        raw_connection.close()

    return snapshot_path


def inspect_sqlite_backup(file_path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()
        integrity_value = integrity_result[0] if integrity_result else "unknown"

        if integrity_value != "ok":
            raise ValueError(f"SQLite integrity check failed: {integrity_value}")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()

    if "config" not in tables or "chat" not in tables:
        raise ValueError("The uploaded file is not a compatible Halo WebUI SQLite backup.")

    warnings: list[str] = []
    if "user" not in tables:
        warnings.append("The backup is missing the user table; please verify the source file.")

    return {
        "summary": {
            "table_count": len(tables),
            "tables_preview": tables[:8],
            "has_config_table": "config" in tables,
            "has_chat_table": "chat" in tables,
            "has_user_table": "user" in tables,
        },
        "warnings": warnings,
    }


def restore_sqlite_backup(source_path: Path, target_path: Path) -> None:
    source_connection = sqlite3.connect(source_path)
    target_connection = sqlite3.connect(target_path)

    try:
        source_connection.backup(target_connection)
        target_connection.commit()
    finally:
        target_connection.close()
        source_connection.close()

    Path(f"{target_path}-wal").unlink(missing_ok=True)
    Path(f"{target_path}-shm").unlink(missing_ok=True)


def reload_persistent_config_state(app_config) -> None:
    config_module.CONFIG_DATA = config_module.get_config()
    config_module.CONFIG_DATA = config_module._repair_web_search_numeric_config(
        config_module.CONFIG_DATA
    )

    for config_item in config_module.PERSISTENT_CONFIG_REGISTRY:
        new_value = config_module.get_config_value(config_item.config_path)
        if new_value is not None and ENABLE_PERSISTENT_CONFIG:
            config_item.value = new_value
            config_item.config_value = new_value
        else:
            config_item.value = config_item.env_value
            config_item.config_value = None

    redis_client = getattr(app_config, "_redis", None)
    state = getattr(app_config, "_state", {})
    if redis_client:
        for key, config_item in state.items():
            redis_client.set(
                f"{REDIS_KEY_PREFIX}config:{key}", json.dumps(config_item.value)
            )


def refresh_runtime_after_restore(app) -> None:
    from open_webui.retrieval.runtime import (
        reset_embedding_runtime,
        reset_reranking_runtime,
    )
    from open_webui.utils.models import invalidate_base_model_cache

    reload_persistent_config_state(app.state.config)

    app.state.USER_COUNT = None
    app.state.TOOLS = {}
    app.state.FUNCTIONS = {}
    app.state.MODELS = {}
    app.state.BASE_MODELS = None
    app.state.OLLAMA_MODELS = {}
    app.state.OPENAI_MODELS = {}
    app.state.GEMINI_MODELS = {}
    app.state.ANTHROPIC_MODELS = {}

    reset_embedding_runtime(app)
    reset_reranking_runtime(app)
    invalidate_base_model_cache()
