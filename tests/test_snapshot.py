"""Tests: snapshot persistence."""
from __future__ import annotations

from win11opt.core import snapshot as snap_mod
from win11opt.core.models import Action, ActionKind


def _mk_action(kind=ActionKind.REG_SET, target="HKLM\\Software\\X", name="Foo", value=1):
    return Action(kind=kind, target=target, name=name, value=value,
                  undo_target=target, undo_value=value)


def test_create_snapshot_id_is_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(snap_mod, "_snapshots_dir", lambda: tmp_path)
    sid = snap_mod.create_snapshot_id()
    assert len(sid) == 15  # YYYYMMDD-HHMMSS


def test_make_snapshot_includes_restore_point_id(tmp_path, monkeypatch, fake_ps):
    monkeypatch.setattr(snap_mod, "_snapshots_dir", lambda: tmp_path)
    snap = snap_mod.make_snapshot(["x.y"], [_mk_action()])
    assert snap.restore_point_id == 1
    assert "x.y" in snap.rules_applied


def test_save_and_load_round_trip(tmp_path, monkeypatch, fake_ps):
    monkeypatch.setattr(snap_mod, "_snapshots_dir", lambda: tmp_path)
    snap = snap_mod.make_snapshot(["x.y"], [_mk_action(value=42)])
    snap_mod.save(snap)
    loaded = snap_mod.load(snap.id)
    assert loaded.id == snap.id
    assert loaded.rules_applied == ["x.y"]
    assert len(loaded.actions_undone) == 1
    assert loaded.actions_undone[0].value == 42


def test_load_round_trip_all_action_kinds(tmp_path, monkeypatch, fake_ps):
    """Regression: snapshot.load() использовал ActionKind без импорта (NameError)."""
    monkeypatch.setattr(snap_mod, "_snapshots_dir", lambda: tmp_path)
    actions = [
        _mk_action(kind=ActionKind.REG_SET, value=1),
        _mk_action(kind=ActionKind.REG_DELETE),
        _mk_action(kind=ActionKind.SERVICE_DISABLE, target="Spooler"),
        _mk_action(kind=ActionKind.SCHED_TASK_DISABLE, target="\\X\\Y"),
    ]
    snap = snap_mod.make_snapshot([], actions)
    snap_mod.save(snap)
    loaded = snap_mod.load(snap.id)
    kinds = [a.kind for a in loaded.actions_undone]
    assert kinds == [ActionKind.REG_SET, ActionKind.REG_DELETE,
                     ActionKind.SERVICE_DISABLE, ActionKind.SCHED_TASK_DISABLE]


def test_undo_value_round_trips_independently_of_value(tmp_path, monkeypatch, fake_ps):
    """Regression: undo_value (исходное) не должен подменяться value (новым).

    До фикса to_dict() не сериализовал undo_value, а load() подставлял
    undo_value = value — rollback после перезапуска возвращал реестр в
    НОВОЕ значение вместо исходного.
    """
    monkeypatch.setattr(snap_mod, "_snapshots_dir", lambda: tmp_path)
    action = Action(
        kind=ActionKind.REG_SET, target="HKCU:\\Software\\X", name="Foo",
        value=0, value_type="DWord",
        undo_target="HKCU:\\Software\\X", undo_value=1,
    )
    snap = snap_mod.make_snapshot(["x.y"], [action])
    snap_mod.save(snap)
    loaded = snap_mod.load(snap.id)
    a = loaded.actions_undone[0]
    assert a.value == 0          # новое значение
    assert a.undo_value == 1     # исходное значение — не подменено
    assert a.undo_target == "HKCU:\\Software\\X"
