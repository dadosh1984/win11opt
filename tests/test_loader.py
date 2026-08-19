"""Tests: YAML rule loader."""
from pathlib import Path

import pytest

from win11opt.rules.loader import (
    DEFAULT_RULES_DIR, RuleLoadError, load_all, load_preset,
    validate_dir, validate_file,
)
from win11opt.core.models import ActionKind, Risk


def _write_yaml(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_load_preset_minimal(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
description: test
rules:
  - id: x.one
    name: One
    actions:
      - kind: reg_set
        target: 'HKCU:\\X'
        name: Foo
        value: '0'
""")
    preset, rules = load_preset(p)
    assert preset == "x"
    assert len(rules) == 1
    assert rules[0].id == "x.one"
    assert rules[0].risk == Risk.LOW  # default
    assert rules[0].actions[0].kind == ActionKind.REG_SET
    assert rules[0].actions[0].value_type is None  # default


def test_load_preset_explicit_risk(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.risky
    risk: medium
    actions:
      - kind: service_disable
        target: Foo
""")
    _, rules = load_preset(p)
    assert rules[0].risk == Risk.MEDIUM


def test_unknown_action_kind_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.bad
    actions:
      - kind: nuke_system
        target: '*'
""")
    with pytest.raises(RuleLoadError, match="unknown action kind"):
        load_preset(p)


def test_unknown_risk_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.r
    risk: apocalyptic
    actions:
      - kind: reg_set
        target: 'HKCU:\\X'
""")
    with pytest.raises(RuleLoadError, match="unknown risk"):
        load_preset(p)


def test_missing_actions_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.empty
""")
    with pytest.raises(RuleLoadError, match="non-empty"):
        load_preset(p)


def test_duplicate_ids_in_preset_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.dup
    actions: [{kind: reg_set, target: HKCU:\\A, name: a, value: '1'}]
  - id: x.dup
    actions: [{kind: reg_set, target: HKCU:\\B, name: b, value: '2'}]
""")
    with pytest.raises(RuleLoadError, match="duplicate rule id"):
        load_preset(p)


def test_id_without_category_prefix_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: noprefix
    actions: [{kind: reg_set, target: HKCU:\\A, name: a, value: '1'}]
""")
    with pytest.raises(RuleLoadError, match="category prefix"):
        load_preset(p)


def test_malformed_yaml_rejected(tmp_path):
    p = _write_yaml(tmp_path, "x.yaml", "name: x\nrules:\n  - :\n   bad: [yaml")
    with pytest.raises(RuleLoadError, match="YAML syntax"):
        load_preset(p)


def test_load_all_merged_unique():
    """Все встроенные YAML-пресеты должны грузиться без дублей."""
    rules = load_all(DEFAULT_RULES_DIR)
    ids = list(rules.keys())
    assert len(ids) == len(set(ids)), "duplicate ids across files"
    # Sanity: должны быть все наши категории
    cats = {r.category for r in rules.values()}
    assert {"visual", "services", "telemetry", "power", "registry"} <= cats


def test_validate_dir_passes_for_builtin():
    errs = validate_dir(DEFAULT_RULES_DIR)
    assert errs == {}, f"builtin YAML has errors: {errs}"


def test_validate_file_returns_list(tmp_path):
    p = _write_yaml(tmp_path, "bad.yaml", """
name: bad
rules:
  - id: bad.x
    actions: []
""")
    errs = validate_file(p)
    assert errs and "non-empty" in errs[0]


def test_yaml_round_trip_with_engine(fake_ps, tmp_path):
    """Загруженное из YAML правило должно работать через engine."""
    p = _write_yaml(tmp_path, "x.yaml", """
name: x
rules:
  - id: x.test
    actions:
      - kind: reg_set
        target: 'HKCU:\\X'
        name: Foo
        value: '42'
""")
    _, rules = load_preset(p)
    rule = rules[0]
    from win11opt.core import engine
    engine.apply(rule.actions, dry_run=False)
    key = ("HKCU", "x", "Foo")
    assert fake_ps["registry"][key]["value"] == "42"


def test_all_new_categories_loaded():
    """ui/gaming/onedrive должны появиться после v0.4."""
    rules = load_all(DEFAULT_RULES_DIR)
    cats = {r.category for r in rules.values()}
    assert "ui" in cats
    assert "gaming" in cats
    assert "onedrive" in cats


def test_ui_instant_menu_low_risk():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["ui.instant_menu"]
    assert r.risk.value == "low"
    assert r.requires_reboot is False
    assert r.actions[0].target.endswith("Control Panel\\Desktop")
    assert r.actions[0].name == "MenuShowDelay"
    assert r.actions[0].value == "0"


def test_gaming_disable_gamebar_requires_reboot():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["gaming.disable_gamebar"]
    assert r.requires_reboot is True
    assert len(r.actions) == 3  # AppCapture + GameDVR_Enabled + AllowGameDVR


def test_debloat_appx_remove_actions():
    """Правила debloat должны содержать appx_remove действия."""
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["debloat.remove_xbox_apps"]
    assert all(a.kind == ActionKind.APPX_REMOVE for a in r.actions)
    assert any("XboxGameOverlay" in a.target for a in r.actions)


def test_debloat_apply_runs_appx_remove(fake_ps):
    """apply appx_remove должен вызвать ps.appx_remove."""
    from win11opt.core import engine
    from win11opt.core.models import Action
    actions = [Action(kind=ActionKind.APPX_REMOVE, target="*BingWeather*")]
    engine.apply(actions, dry_run=False)
    assert "*BingWeather*" in fake_ps["appx_removed"]


def test_debloat_dry_run_does_not_remove(fake_ps):
    """В dry-run appx_remove НЕ должен вызываться."""
    from win11opt.core import engine
    from win11opt.core.models import Action
    actions = [Action(kind=ActionKind.APPX_REMOVE, target="*BingWeather*")]
    engine.apply(actions, dry_run=True)
    assert fake_ps["appx_removed"] == []


def test_explorer_show_extensions_target():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["explorer.show_extensions"]
    assert r.actions[0].target.endswith("Explorer\\Advanced")
    assert r.actions[0].name == "HideFileExt"
    assert r.actions[0].value == "0"


def test_all_new_categories_loaded_v05():
    """explorer/debloat должны появиться после v0.5."""
    rules = load_all(DEFAULT_RULES_DIR)
    cats = {r.category for r in rules.values()}
    assert "explorer" in cats
    assert "debloat" in cats


def test_defender_rules_loaded():
    """defender/update появились в v0.6."""
    rules = load_all(DEFAULT_RULES_DIR)
    cats = {r.category for r in rules.values()}
    assert "defender" in cats
    assert "update" in cats
    # SpyNetReporting — ключевой твик
    assert "defender.disable_cloud_protection" in rules
    assert rules["defender.disable_cloud_protection"].risk.value == "medium"


def test_update_defer_feature_present():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["update.defer_feature_updates"]
    assert r.risk.value == "low"
    assert any("DeferFeatureUpdates" in a.name for a in r.actions)


def test_defender_does_not_break_real_time_protection():
    """Твики defender НЕ должны отключать реалтайм-защиту (это невозможно сделать без BSOD)."""
    rules = load_all(DEFAULT_RULES_DIR)
    # Проверяем что мы НЕ пишем в DisableAntiSpyware / DisableRealtimeMonitoring
    for rid in ("defender.disable_cloud_protection", "defender.disable_mp_telemetry", "defender.disable_smart_screen"):
        for action in rules[rid].actions:
            assert action.name not in ("DisableAntiSpyware", "DisableRealtimeMonitoring"), \
                f"{rid} would disable real-time protection!"


def test_power_hibernation_rule():
    """power.disable_hibernation должен использовать hibernate_off."""
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["power.disable_hibernation"]
    assert r.actions[0].kind == ActionKind.POWER_HIBERNATE_DISABLE


def test_power_plan_uses_guid_target():
    """power.ultimate_performance: target должен быть GUID (не 'ultimate')."""
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["power.ultimate_performance"]
    assert r.actions[0].kind == ActionKind.POWER_PLAN
    assert "-" in r.actions[0].target  # GUID содержит дефисы
    assert r.actions[0].target != "ultimate"


def test_hibernation_apply_calls_ps(fake_ps):
    """apply hibernate_off должен вызвать ps.power_hibernate_set(False)."""
    from win11opt.core import engine
    from win11opt.core.models import Action
    actions = [Action(kind=ActionKind.POWER_HIBERNATE_DISABLE, target="hiberfil.sys")]
    engine.apply(actions, dry_run=False)
    assert fake_ps["hibernate"] is False


def test_power_plan_apply_calls_ps(fake_ps):
    """apply power_plan должен вызвать ps.power_plan_activate(GUID)."""
    from win11opt.core import engine
    from win11opt.core.models import Action
    guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    actions = [Action(kind=ActionKind.POWER_PLAN, target=guid)]
    engine.apply(actions, dry_run=False)
    assert guid in fake_ps["power_plans"]


def test_telemetry_ceip_rule():
    """telemetry.disable_ceip должен писать AllowTelemetry=0."""
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["telemetry.disable_ceip"]
    assert any(a.name == "AllowTelemetry" and a.value == "0" for a in r.actions)
    assert any(a.name == "CEIPEnable" for a in r.actions)


def test_network_rules_loaded():
    """network/ntfs появились в v0.8."""
    rules = load_all(DEFAULT_RULES_DIR)
    cats = {r.category for r in rules.values()}
    assert "network" in cats
    assert "ntfs" in cats
    assert rules["network.disable_nagle"].risk.value == "low"
    assert rules["ntfs.disable_last_access_time"].risk.value == "low"


def test_network_nagle_target():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["network.disable_nagle"]
    assert any(a.name == "TcpAckFrequency" and a.value == "1" for a in r.actions)
    assert any(a.name == "TCPNoDelay" for a in r.actions)


def test_ntfs_last_access_target():
    rules = load_all(DEFAULT_RULES_DIR)
    r = rules["ntfs.disable_last_access_time"]
    assert r.actions[0].name == "NtfsDisableLastAccessUpdate"
    assert r.actions[0].value == "1"
    assert "FileSystem" in r.actions[0].target
