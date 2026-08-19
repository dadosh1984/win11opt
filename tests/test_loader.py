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
