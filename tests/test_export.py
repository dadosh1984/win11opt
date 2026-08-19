"""Tests for rules/export.py — export+import custom preset."""
from __future__ import annotations

from pathlib import Path

import yaml

from win11opt.rules import export as export_mod
from win11opt.rules import get_rules
from win11opt.rules.loader import RuleLoadError


def test_export_profile_writes_yaml(tmp_path: Path):
    rules = get_rules()
    out = tmp_path / "my-set.yaml"
    saved = export_mod.export_profile(
        name="MySet",
        description="Custom config",
        rule_ids=["visual.disable_animations", "telemetry.advertising_id"],
        rules_lookup=rules,
        out_path=out,
    )
    assert saved == out
    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["name"] == "MySet"
    assert data["description"] == "Custom config"
    assert len(data["rules"]) == 2
    assert data["rules"][0]["id"] == "visual.disable_animations"


def test_export_profile_rejects_unknown_ids(tmp_path: Path):
    rules = get_rules()
    out = tmp_path / "bad.yaml"
    try:
        export_mod.export_profile(
            name="Bad",
            description="",
            rule_ids=["visual.disable_animations", "FAKE.id"],
            rules_lookup=rules,
            out_path=out,
        )
    except RuleLoadError as e:
        assert "FAKE.id" in str(e)
        assert not out.exists(), "файл не должен быть создан при ошибке"
    else:
        raise AssertionError("expected RuleLoadError")


def test_export_profile_creates_parent_dirs(tmp_path: Path):
    rules = get_rules()
    out = tmp_path / "subdir" / "nested" / "preset.yaml"
    export_mod.export_profile(
        name="X",
        description="",
        rule_ids=["visual.disable_animations"],
        rules_lookup=rules,
        out_path=out,
    )
    assert out.exists()


def test_export_then_import_round_trip(tmp_path: Path):
    """Export → import должны давать идентичные rule_ids."""
    rules = get_rules()
    src_ids = ["visual.disable_animations", "telemetry.advertising_id", "power.ultimate_performance"]
    out = tmp_path / "rt.yaml"
    export_mod.export_profile(
        name="RT",
        description="round-trip",
        rule_ids=src_ids,
        rules_lookup=rules,
        out_path=out,
    )
    name, got_ids = export_mod.import_profile(out)
    assert name == "RT"
    assert got_ids == src_ids


def test_export_preserves_action_fields(tmp_path: Path):
    """PowerPlan (kind + target + name) должно пережить export→import."""
    rules = get_rules()
    out = tmp_path / "p.yaml"
    export_mod.export_profile(
        name="P",
        description="",
        rule_ids=["power.ultimate_performance"],
        rules_lookup=rules,
        out_path=out,
    )
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    a = data["rules"][0]["actions"][0]
    # Проверяем что важные поля есть
    assert "kind" in a
    assert "target" in a
    assert a["target"] == rules["power.ultimate_performance"].actions[0].target


def test_export_preserves_ms_doc_url(tmp_path: Path):
    rules = get_rules()
    out = tmp_path / "doc.yaml"
    export_mod.export_profile(
        name="D",
        description="",
        rule_ids=["visual.disable_animations"],
        rules_lookup=rules,
        out_path=out,
    )
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["rules"][0]["ms_doc_url"] == rules["visual.disable_animations"].ms_doc_url


def test_export_preserves_unicode_name(tmp_path: Path):
    rules = get_rules()
    out = tmp_path / "u.yaml"
    export_mod.export_profile(
        name="Кастом",
        description="описание",
        rule_ids=["visual.disable_animations"],
        rules_lookup=rules,
        out_path=out,
    )
    content = out.read_text(encoding="utf-8")
    assert "Кастом" in content
    assert "описание" in content


def test_import_rejects_malformed_yaml(tmp_path: Path):
    p = tmp_path / "bad.yaml"
    p.write_text("not yaml: this is broken: [", encoding="utf-8")
    try:
        export_mod.import_profile(p)
    except RuleLoadError:
        pass
    else:
        raise AssertionError("expected RuleLoadError")


def test_import_rejects_rule_without_id(tmp_path: Path):
    p = tmp_path / "no-id.yaml"
    p.write_text("""
name: bad
rules:
  - name: missing id
    actions:
      - kind: reg_set
        target: HKLM:\\\\Foo
        name: X
        value: '1'
""", encoding="utf-8")
    try:
        export_mod.import_profile(p)
    except RuleLoadError as e:
        assert "id" in str(e).lower() or "missing" in str(e).lower()
    else:
        raise AssertionError("expected RuleLoadError")


def test_install_profile_copies_to_dir(tmp_path: Path):
    """install_profile копирует файл в dest_dir."""
    from win11opt.rules import export as export_mod
    src = tmp_path / "src.yaml"
    src.write_text("name: x\nrules: []\n", encoding="utf-8")
    dest_dir = tmp_path / "rules"
    result = export_mod.install_profile(src, dest_dir=dest_dir)
    assert result == dest_dir / "src.yaml"
    assert result.exists()
    assert result.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_install_profile_default_dir(tmp_path, monkeypatch):
    """install_profile без dest_dir копирует в DEFAULT_RULES_DIR."""
    from win11opt.rules import export as export_mod
    from win11opt.rules import loader as loader_mod
    src = tmp_path / "p.yaml"
    src.write_text("name: p\nrules: []\n", encoding="utf-8")
    fake_dir = tmp_path / "fake_rules"
    monkeypatch.setattr(loader_mod, "DEFAULT_RULES_DIR", fake_dir)
    result = export_mod.install_profile(src)
    assert result == fake_dir / "p.yaml"
    assert result.exists()


def test_cmd_import_validates_only_does_not_copy(tmp_path, monkeypatch, capsys):
    """CLI import --validate-only не копирует файл."""
    from win11opt.rules import get_rules
    from win11opt.rules import loader as loader_mod
    export_mod = __import__("win11opt.rules.export", fromlist=["export_profile"])
    src = tmp_path / "p.yaml"
    export_mod.export_profile(
        name="P", description="", rule_ids=["visual.disable_animations"],
        rules_lookup=get_rules(), out_path=src,
    )
    fake_dir = tmp_path / "rules"
    monkeypatch.setattr(loader_mod, "DEFAULT_RULES_DIR", fake_dir)
    from win11opt.cli.main import build_parser
    parser = build_parser()
    args = parser.parse_args(["import", str(src), "--validate-only"])
    rc = args.func(args)
    assert rc == 0
    assert not fake_dir.exists(), "validate-only must not create rules dir"
    out = capsys.readouterr().out
    assert "validate-only" in out


def test_cmd_import_copies_and_prints_install_path(tmp_path, monkeypatch, capsys):
    """CLI import без --validate-only копирует и печатает путь."""
    from win11opt.rules import get_rules
    from win11opt.rules import loader as loader_mod
    export_mod = __import__("win11opt.rules.export", fromlist=["export_profile"])
    src = tmp_path / "p.yaml"
    export_mod.export_profile(
        name="MyProfile", description="", rule_ids=["visual.disable_animations"],
        rules_lookup=get_rules(), out_path=src,
    )
    fake_dir = tmp_path / "rules"
    monkeypatch.setattr(loader_mod, "DEFAULT_RULES_DIR", fake_dir)
    from win11opt.cli.main import build_parser
    parser = build_parser()
    args = parser.parse_args(["import", str(src)])
    rc = args.func(args)
    assert rc == 0
    assert (fake_dir / "p.yaml").exists()
    out = capsys.readouterr().out
    assert "installed:" in out
    assert "MyProfile" in out
