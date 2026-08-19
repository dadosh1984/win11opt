"""Apply engine — dry-run, apply, rollback.

Идемпотентность: перед каждым действием читаем текущее значение и
сохраняем его в Snapshot.actions_undone. Rollback применяет их в
обратном порядке.

ponytail: rung 4 — MVP делает apply+rollback по одному правилу;
батч-режим (профили) идёт через apply_many() — та же логика в цикле.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Iterable

from .models import Action, ActionKind, Result, Snapshot
from . import ps

log = logging.getLogger(__name__)


def _capture_undo(action: Action) -> Action:
    """Прочитать текущее значение и вернуть Action с заполненным undo_*."""
    if action.kind in (ActionKind.REG_SET, ActionKind.REG_DELETE):
        # Парсим target как "HKCU:\Path"
        if ":" not in action.target:
            return action
        hive, path = action.target.split(":", 1)
        current = ps.reg_get(hive, path.lstrip("\\"), action.name)
        return Action(
            kind=action.kind,
            target=action.target, name=action.name,
            value=action.value, value_type=action.value_type,
            undo_target=action.target,
            undo_value=current,
        )
    if action.kind == ActionKind.SCHED_TASK_DISABLE:
        # Запоминаем что отключили (откат = enable)
        return Action(
            kind=action.kind,
            target=action.target,
            undo_target=action.target,
            undo_value="enabled",
        )
    return action


def apply(rule_actions: Iterable[Action], *, dry_run: bool = False) -> list[Action]:
    """Применить список действий. Возвращает список с undo-данными для snapshot."""
    applied: list[Action] = []
    for action in rule_actions:
        captured = _capture_undo(action)
        log.info("[%s] %s", "DRY" if dry_run else "APPLY", action.describe())
        if not dry_run:
            _execute(captured)
        applied.append(captured)
    return applied


def rollback(snapshot: Snapshot, *, dry_run: bool = False) -> None:
    """Откатить snapshot — выполнить обратные действия в обратном порядке."""
    for action in reversed(snapshot.actions_undone):
        log.info("[%s] undo %s", "DRY" if dry_run else "ROLLBACK", action.describe())
        if not dry_run:
            _undo_one(action)


def _execute(action: Action) -> None:
    if action.kind == ActionKind.REG_SET:
        if ":" not in action.target:
            raise ValueError(f"bad reg target: {action.target}")
        hive, path = action.target.split(":", 1)
        ps.reg_set(hive, path.lstrip("\\"), action.name or "", action.value, action.value_type or "DWord")
    elif action.kind == ActionKind.REG_DELETE:
        hive, path = action.target.split(":", 1)
        ps.reg_delete(hive, path.lstrip("\\"), action.name or "")
    elif action.kind == ActionKind.SERVICE_DISABLE:
        ps.service_set_state(action.target, "Disabled")
    elif action.kind == ActionKind.SERVICE_MANUAL:
        ps.service_set_state(action.target, "Manual")
    elif action.kind == ActionKind.APPX_REMOVE:
        ps.appx_remove(action.target)
    elif action.kind == ActionKind.POWER_PLAN:
        # target = GUID плана (например "8c5e7fda-...")
        ps.power_plan_activate(action.target)
    elif action.kind == ActionKind.POWER_HIBERNATE_DISABLE:
        ps.power_hibernate_set(False)
    elif action.kind == ActionKind.POWER_HIBERNATE_ENABLE:
        ps.power_hibernate_set(True)
    elif action.kind == ActionKind.SCHED_TASK_DISABLE:
        ps.sched_task_disable(action.target)
    else:
        raise NotImplementedError(f"action kind not implemented: {action.kind}")


def _undo_one(action: Action) -> None:
    """Восстановить исходное состояние по undo_* полям."""
    if action.kind == ActionKind.APPX_REMOVE:
        # APPX удаление не имеет undo — пакет пропал после apply.
        log.warning("APPX package removal is irreversible: %s", action.target)
        return
    if action.undo_target is None:
        # Ничего не знаем о прошлом — пропускаем
        log.warning("no undo data for %s, skipping", action.describe())
        return
    if action.kind == ActionKind.REG_SET:
        if action.undo_value is None:
            # Исходного значения не было — удаляем то, что создали
            hive, path = action.target.split(":", 1)
            ps.reg_delete(hive, path.lstrip("\\"), action.name or "")
        else:
            hive, path = action.target.split(":", 1)
            v = action.undo_value
            # Если пришло как dict {Name, Type, Value} из reg_get — извлекаем
            if isinstance(v, dict) and "Value" in v:
                ps.reg_set(hive, path.lstrip("\\"), action.name or "", v["Value"], v.get("Type", "DWord"))
            elif isinstance(v, dict) and "value" in v:
                ps.reg_set(hive, path.lstrip("\\"), action.name or "", v["value"], v.get("type", "DWord"))
            else:
                ps.reg_set(hive, path.lstrip("\\"), action.name or "", v, action.value_type or "DWord")
    elif action.kind == ActionKind.REG_DELETE:
        # Возвращаем исходное значение
        if action.undo_value is not None:
            hive, path = action.target.split(":", 1)
            ps.reg_set(hive, path.lstrip("\\"), action.name or "", action.undo_value, action.value_type or "DWord")
    elif action.kind in (ActionKind.SERVICE_DISABLE, ActionKind.SERVICE_MANUAL):
        # Возвращаем исходный тип запуска
        original = action.undo_value if action.undo_value in ("Automatic", "Manual", "Disabled") else "Automatic"
        ps.service_set_state(action.target, original)
    elif action.kind == ActionKind.SCHED_TASK_DISABLE:
        # undo_value="enabled" — значит задача была включена, возвращаем
        ps.sched_task_enable(action.target)
