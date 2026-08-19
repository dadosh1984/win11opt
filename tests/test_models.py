"""Tests: domain models."""
from win11opt.core.models import Action, ActionKind, Risk


def test_action_describe():
    a = Action(kind=ActionKind.REG_SET, target=r"HKCU:\X", name="Foo", value=1)
    assert "reg_set" in a.describe()
    assert "HKCU:\\X" in a.describe()
    assert "Foo" in a.describe()


def test_rule_categories():
    from win11opt.rules import get_rules

    cats = {r.category for r in get_rules().values()}
    assert "visual" in cats
    assert "services" in cats
    assert "telemetry" in cats
    assert "power" in cats
    assert "registry" in cats


def test_presets_reference_real_rules():
    from win11opt.rules import get_rules
    from win11opt.rules.builtin import PRESETS

    rules = get_rules()
    for p in PRESETS:
        for rid in p.rule_ids:
            assert rid in rules, f"preset {p.name} references unknown rule {rid}"


def test_risk_levels_present():
    from win11opt.rules import get_rules

    seen = {r.risk for r in get_rules().values()}
    assert Risk.LOW in seen
    assert Risk.MEDIUM in seen
