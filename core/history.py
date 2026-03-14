from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .schemas import DesignPackage, HistoryEntry

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = PROJECT_ROOT / ".design_history.json"


def _read_entries() -> list[HistoryEntry]:
    if not HISTORY_PATH.exists():
        return []
    try:
        raw = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    entries: list[HistoryEntry] = []
    for item in raw:
        if isinstance(item, dict):
            try:
                entries.append(HistoryEntry(**item))
            except Exception:
                continue
    return entries


def _write_entries(entries: list[HistoryEntry]) -> None:
    payload = [entry.model_dump(mode="json") for entry in entries]
    HISTORY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def create_history_entry(task: str, package: DesignPackage, tags: list[str]) -> HistoryEntry:
    now = datetime.now(timezone.utc).isoformat()
    entry = HistoryEntry(
        version_id=str(uuid4()),
        created_at=now,
        task=task.strip(),
        tags=[tag.strip() for tag in tags if tag.strip()],
        package=package,
    )
    entries = _read_entries()
    entries.insert(0, entry)
    _write_entries(entries)
    return entry


def list_history_entries() -> list[HistoryEntry]:
    return _read_entries()


def get_history_entry(version_id: str) -> HistoryEntry | None:
    for entry in _read_entries():
        if entry.version_id == version_id:
            return entry
    return None


def set_review_status(version_id: str, status: str) -> HistoryEntry | None:
    entries = _read_entries()
    for idx, entry in enumerate(entries):
        if entry.version_id != version_id:
            continue
        updated = HistoryEntry.model_validate(
            entry.model_dump(mode="python") | {"status": status}
        )
        entries[idx] = updated
        _write_entries(entries)
        return updated
    return None


def add_reviewer_comment(version_id: str, comment: str) -> HistoryEntry | None:
    clean_comment = comment.strip()
    if not clean_comment:
        return None
    entries = _read_entries()
    for idx, entry in enumerate(entries):
        if entry.version_id != version_id:
            continue
        updated_comments = [*entry.reviewer_comments, clean_comment]
        updated = entry.model_copy(update={"reviewer_comments": updated_comments})
        entries[idx] = updated
        _write_entries(entries)
        return updated
    return None
