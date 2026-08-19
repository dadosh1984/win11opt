"""Экспорт и импорт custom-пресетов в YAML.

ponytail: rung 4 — измеримый артефакт, шаринг конфигурации.
ponytail: rung 5 — переиспользуем существующий формат rules/*.yaml.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

import yaml

from .loader import RuleLoadError, load_preset


def install_profile(src: Path, dest_dir: Path | None = None) -> Path:
    """Скопировать профиль в dest_dir (по умолчанию — DEFAULT_RULES_DIR).

    Возвращает путь к скопированному файлу.
    """
    from .loader import DEFAULT_RULES_DIR
    target_dir = dest_dir or DEFAULT_RULES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / src.name
    shutil.copy2(src, dest)
    return dest


def _rule_to_yaml_dict(rule) -> dict:
    """Сериализовать одно Rule в YAML-словарь."""
    out = {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "risk": rule.risk.value,
        "actions": [_action_to_yaml(a) for a in rule.actions],
    }
    if rule.requires_reboot:
        out["requires_reboot"] = True
    if rule.ms_doc_url:
        out["ms_doc_url"] = rule.ms_doc_url
    return out


def _action_to_yaml(action) -> dict:
    """Сериализовать Action в YAML-словарь."""
    out = {"kind": action.kind.value, "target": action.target}
    if action.name is not None:
        out["name"] = action.name
    if action.value is not None:
        out["value"] = action.value
    if action.value_type is not None:
        out["value_type"] = action.value_type
    if action.undo_target is not None:
        out["undo_target"] = action.undo_target
    if action.undo_value is not None:
        out["undo_value"] = action.undo_value
    return out


def export_profile(
    name: str,
    description: str,
    rule_ids: Iterable[str],
    rules_lookup: dict,
    out_path: Path,
) -> Path:
    """Сохранить custom-пресет в YAML. Проверяет, что все rule_ids существуют.

    Формат совместим с rules/*.yaml — файлы можно положить в rules/ и они
    будут подхвачены через load_all().
    """
    rule_ids = list(rule_ids)
    missing = [rid for rid in rule_ids if rid not in rules_lookup]
    if missing:
        raise RuleLoadError(f"unknown rule ids: {missing}")
    data = {
        "name": name,
        "description": description,
        "rules": [_rule_to_yaml_dict(rules_lookup[rid]) for rid in rule_ids],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return out_path


def import_profile(path: Path) -> tuple[str, list[str]]:
    """Загрузить custom-пресет из YAML. Возвращает (name, [rule_ids]).

    re-использует load_preset для валидации (rule id, category prefix, actions).
    """
    name, rules = load_preset(path)
    return name, [r.id for r in rules]
