"""YAML loader для пресетов правил.

Формат YAML — простой и читаемый, без лишней магии:

```yaml
name: visual
description: Визуальные оптимизации.
rules:
  - id: visual.disable_animations
    name: Отключить анимации окон
    risk: low
    actions:
      - kind: reg_set
        target: 'HKCU:\\...'
        name: Foo
        value: '0'
        value_type: DWord
```

ponytail: rung 4 — YAML loader нужен сейчас, чтобы правила мог
расширять сообщество без перекомпиляции EXE (если будем читать из
рядом с EXE; пока идём из репо).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml

from ..core.models import Action, ActionKind, Risk, Rule


def _resolve_default_rules_dir() -> Path:
    """Корень с YAML-пресетами.

    Приоритет:
    1. Env WIN11OPT_RULES_DIR (override для пользовательских пресетов)
    2. Рядом с EXE: <exe-dir>/rules — для portable-режима
    3. PyInstaller `_MEIPASS/rules` — внутри упакованного EXE
    4. <src>/../rules — dev-режим (родитель src/)
    """
    env = os.environ.get("WIN11OPT_RULES_DIR")
    if env:
        return Path(env)

    # PyInstaller: данные распакованы в _MEIPASS
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand = Path(meipass) / "rules"
        if cand.exists():
            return cand

    # Рядом с exe-файлом (portable)
    exe = getattr(sys, "executable", None)
    if exe:
        cand = Path(exe).resolve().parent / "rules"
        if cand.exists():
            return cand

    # Dev-режим: src/win11opt/rules/loader.py → src/ → корень
    return Path(__file__).resolve().parents[3] / "rules"


DEFAULT_RULES_DIR = _resolve_default_rules_dir()


class RuleLoadError(ValueError):
    """Невалидный YAML или правило."""


# Mapping YAML-friendly action kind names → ActionKind enum.
# YAML использует читабельные имена вида service_disable; enum хранит
# короткий машинный код.
_KIND_ALIASES = {
    "reg_set": ActionKind.REG_SET,
    "reg_delete": ActionKind.REG_DELETE,
    "service_disable": ActionKind.SERVICE_DISABLE,
    "service_manual": ActionKind.SERVICE_MANUAL,
    "service_delete": ActionKind.SERVICE_DELETE,
    "sched_task_disable": ActionKind.SCHED_TASK_DISABLE,
    "appx_remove": ActionKind.APPX_REMOVE,
    "power_plan": ActionKind.POWER_PLAN,
    "shell_ext": ActionKind.SHELL_EXT,
}


def _parse_action(raw: dict[str, Any]) -> Action:
    if not isinstance(raw, dict):
        raise RuleLoadError(f"action must be a mapping, got {type(raw).__name__}")
    raw_kind = raw.get("kind")
    if raw_kind is None:
        raise RuleLoadError(f"action missing 'kind': {raw}")
    kind = _KIND_ALIASES.get(raw_kind)
    if kind is None:
        raise RuleLoadError(
            f"unknown action kind: {raw_kind!r}; "
            f"expected one of {sorted(_KIND_ALIASES)}"
        )
    try:
        target = raw["target"]
    except KeyError:
        raise RuleLoadError(f"action missing 'target': {raw}")
    return Action(
        kind=kind,
        target=target,
        name=raw.get("name"),
        value=raw.get("value"),
        value_type=raw.get("value_type"),
    )


def _parse_risk(raw: Any) -> Risk:
    if raw is None:
        return Risk.LOW
    try:
        return Risk(raw)
    except ValueError:
        raise RuleLoadError(f"unknown risk: {raw!r}; expected one of {[r.value for r in Risk]}")


def _parse_rule(raw: dict[str, Any], category: str) -> Rule:
    if not isinstance(raw, dict):
        raise RuleLoadError(f"rule must be a mapping, got {type(raw).__name__}")
    if "id" not in raw:
        raise RuleLoadError(f"rule missing 'id': {raw}")
    rid = raw["id"]
    if "." not in rid:
        raise RuleLoadError(f"rule id must contain category prefix (e.g. 'visual.x'): {rid!r}")
    actions_raw = raw.get("actions", [])
    if not isinstance(actions_raw, list) or not actions_raw:
        raise RuleLoadError(f"rule {rid}: 'actions' must be non-empty list")
    return Rule(
        id=rid,
        name=raw.get("name", rid),
        description=raw.get("description", ""),
        category=category,
        risk=_parse_risk(raw.get("risk")),
        actions=tuple(_parse_action(a) for a in actions_raw),
        requires_reboot=bool(raw.get("requires_reboot", False)),
        ms_doc_url=raw.get("ms_doc_url"),
    )


def load_preset(path: Path) -> tuple[str, list[Rule]]:
    """Загрузить один .yaml файл. Возвращает (preset_name, [rules])."""
    if not path.exists():
        raise RuleLoadError(f"file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise RuleLoadError(f"YAML syntax error in {path}: {e}") from e

    if not isinstance(data, dict):
        raise RuleLoadError(f"{path}: top-level must be a mapping")
    name = data.get("name")
    if not name:
        raise RuleLoadError(f"{path}: missing 'name'")
    rules_raw = data.get("rules", [])
    if not isinstance(rules_raw, list):
        raise RuleLoadError(f"{path}: 'rules' must be a list")

    category = name
    rules = [_parse_rule(r, category) for r in rules_raw]
    # Валидация уникальности id в пресете
    seen = set()
    for r in rules:
        if r.id in seen:
            raise RuleLoadError(f"{path}: duplicate rule id {r.id!r}")
        seen.add(r.id)
    return name, rules


def load_all(dirpath: Path | None = None) -> dict[str, Rule]:
    """Загрузить все *.yaml из директории. Возвращает {rule_id: Rule}."""
    d = dirpath or DEFAULT_RULES_DIR
    if not d.exists():
        return {}
    out: dict[str, Rule] = {}
    for path in sorted(d.glob("*.yaml")):
        _, rules = load_preset(path)
        for r in rules:
            if r.id in out:
                raise RuleLoadError(
                    f"rule {r.id!r} declared in multiple files (also in {out[r.id]!r})"
                )
            out[r.id] = r
    return out


def validate_file(path: Path) -> list[str]:
    """Валидировать YAML-файл. Возвращает список ошибок (пусто = ОК)."""
    errors: list[str] = []
    try:
        load_preset(path)
    except RuleLoadError as e:
        errors.append(str(e))
    return errors


def validate_dir(dirpath: Path | None = None) -> dict[Path, list[str]]:
    """Валидировать все YAML в директории. {path: [errors]}."""
    d = dirpath or DEFAULT_RULES_DIR
    out: dict[Path, list[str]] = {}
    for path in sorted(d.glob("*.yaml")):
        errs = validate_file(path)
        if errs:
            out[path] = errs
    return out
