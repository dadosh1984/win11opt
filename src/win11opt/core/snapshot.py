"""Snapshot persistence — JSON в %LOCALAPPDATA%\\win11opt\\snapshots."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from . import ps
from .models import Action, ActionKind, Snapshot


def _snapshots_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p = Path(base) / "win11opt" / "snapshots"
    p.mkdir(parents=True, exist_ok=True)
    return p


def create_snapshot_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def make_snapshot(rule_ids: list[str], actions: list[Action], description: str = "win11opt apply") -> Snapshot:
    snap = Snapshot(
        id=create_snapshot_id(),
        created_at=dt.datetime.now().isoformat(timespec="seconds"),
        rules_applied=rule_ids,
        actions_undone=actions,
    )
    # Restore point — best-effort
    rp_id = ps.create_restore_point(description)
    object.__setattr__(snap, "restore_point_id", rp_id)
    return snap


def save(snap: Snapshot) -> Path:
    path = _snapshots_dir() / f"{snap.id}.json"
    path.write_text(json.dumps(snap.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load(snap_id: str) -> Snapshot:
    path = _snapshots_dir() / f"{snap_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    actions = [
        Action(
            kind=ActionKind(a["kind"]), target=a["target"],
            name=a.get("name"), value=a.get("value"),
            value_type=a.get("value_type"),
            undo_target=a.get("undo_target", a["target"]),
            undo_value=a.get("undo_value", a.get("value")),
        )
        for a in data.get("actions_undone", [])
    ]
    return Snapshot(
        id=data["id"], created_at=data["created_at"],
        rules_applied=data.get("rules_applied", []),
        actions_undone=actions,
        restore_point_id=data.get("restore_point_id"),
    )


def list_snapshots() -> list[str]:
    d = _snapshots_dir()
    return sorted(p.stem for p in d.glob("*.json"))
