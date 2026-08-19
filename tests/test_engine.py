"""Tests: apply engine + rollback (round-trip)."""
import pytest

from win11opt.core import engine
from win11opt.rules.builtin import (
    disable_animations,
    disable_diagtrack,
    telemetry_advertising_id,
)


def test_apply_dry_run_does_not_touch_state(fake_ps):
    rule = telemetry_advertising_id()
    engine.apply(rule.actions, dry_run=True)
    # Состояние пустое — мы ничего не записали
    assert fake_ps["registry"] == {}


def test_apply_writes_value(fake_ps):
    rule = telemetry_advertising_id()
    engine.apply(rule.actions, dry_run=False)
    key = ("HKCU", r"software\microsoft\windows\currentversion\advertisinginfo", "Enabled")
    assert key in fake_ps["registry"]
    assert fake_ps["registry"][key]["value"] == "0"


def test_apply_then_rollback_restores_original(fake_ps):
    """Если значение уже было — после rollback должно вернуться к нему."""
    pre_key = ("HKCU", r"software\microsoft\windows\currentversion\advertisinginfo", "Enabled")
    fake_ps["registry"][pre_key] = {"value": "1", "type": "DWord"}

    rule = telemetry_advertising_id()
    applied = engine.apply(rule.actions, dry_run=False)
    # Сначала стало 0
    assert fake_ps["registry"][pre_key]["value"] == "0"

    # Rollback через Snapshot
    from win11opt.core.models import Snapshot
    snap = Snapshot(
        id="test", created_at="now",
        rules_applied=[rule.id], actions_undone=applied,
    )
    engine.rollback(snap)
    # Снова 1 (исходное)
    assert fake_ps["registry"][pre_key]["value"] == "1"


def test_rollback_deletes_added_value(fake_ps):
    """Если значения не было и мы его создали — rollback должен удалить."""
    pre_key = ("HKCU", r"software\microsoft\windows\currentversion\advertisinginfo", "Enabled")
    assert pre_key not in fake_ps["registry"]

    rule = telemetry_advertising_id()
    applied = engine.apply(rule.actions, dry_run=False)
    assert pre_key in fake_ps["registry"]

    from win11opt.core.models import Snapshot
    snap = Snapshot(id="t", created_at="n", rules_applied=[rule.id], actions_undone=applied)
    engine.rollback(snap)
    assert pre_key not in fake_ps["registry"]


def test_apply_service_disable(fake_ps):
    rule = disable_diagtrack()
    engine.apply(rule.actions, dry_run=False)
    assert fake_ps["services"]["DiagTrack"] == "Disabled"


def test_apply_creates_restore_point(fake_ps):
    rule = disable_animations()
    applied = engine.apply(rule.actions, dry_run=False)
    from win11opt.core.snapshot import make_snapshot
    snap = make_snapshot([rule.id], applied)
    assert snap.restore_point_id is not None
    assert snap.restore_point_id >= 1


def test_apply_without_admin_raises(monkeypatch):
    """Без прав админа apply должен поднять AdminRequiredError."""
    from win11opt.core import engine
    from win11opt.core.engine import AdminRequiredError
    from win11opt.core.models import Action, ActionKind
    monkeypatch.setattr(engine, "_is_admin", lambda: False)
    actions = [Action(kind=ActionKind.REG_SET, target=r"HKCU:\X", name="Y", value=1)]
    with pytest.raises(AdminRequiredError):
        engine.apply(actions, dry_run=False)


def test_apply_dry_run_skips_admin_check(monkeypatch):
    """dry-run не требует админа (не выполняет PowerShell)."""
    from win11opt.core import engine
    from win11opt.core.models import Action, ActionKind
    monkeypatch.setattr(engine, "_is_admin", lambda: False)
    actions = [Action(kind=ActionKind.REG_SET, target=r"HKCU:\X", name="Y", value=1)]
    # Не должно бросить исключение
    engine.apply(actions, dry_run=True)


def test_rollback_without_admin_raises(monkeypatch):
    """Без прав админа rollback тоже требует админа."""
    from win11opt.core import engine
    from win11opt.core.engine import AdminRequiredError
    from win11opt.core.models import Action, ActionKind, Snapshot
    monkeypatch.setattr(engine, "_is_admin", lambda: False)
    snap = Snapshot(
        id="20260101-000000", created_at="2026-01-01T00:00:00",
        rules_applied=[], actions_undone=[
            Action(kind=ActionKind.REG_SET, target=r"HKCU:\X", name="Y",
                   undo_target=r"HKCU:\X", undo_value=0),
        ],
    )
    with pytest.raises(AdminRequiredError):
        engine.rollback(snap, dry_run=False)
