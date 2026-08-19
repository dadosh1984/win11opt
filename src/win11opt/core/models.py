"""Domain models — Rule, Action, Snapshot, Result.

Минимальные dataclass'ы; вся сериализация в JSON/YAML — в
отдельных модулях. ponytail: rung 2 smallest — без избыточных полей.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Risk(str, Enum):
    LOW = "low"          # визуал, реестр — откатываемо
    MEDIUM = "medium"    # службы, автозагрузка — нужен restore point
    HIGH = "high"        # удаление компонентов, изменение безопасности


class ActionKind(str, Enum):
    REG_SET = "reg_set"           # Set-ItemProperty
    REG_DELETE = "reg_delete"     # Remove-ItemProperty
    SERVICE_DISABLE = "svc_disable"
    SERVICE_MANUAL = "svc_manual"
    SERVICE_DELETE = "svc_delete"
    SCHED_TASK_DISABLE = "task_disable"
    APPX_REMOVE = "appx_remove"
    POWER_PLAN = "power_plan"     # powercfg /setactive
    SHELL_EXT = "shell_ext"       # будущее


@dataclass(frozen=True)
class Action:
    """Одна атомарная операция. У неё есть обратная — для undo."""
    kind: ActionKind
    target: str                    # путь реестра / имя службы / GUID
    name: str | None = None        # имя значения (для реестра)
    value: Any | None = None       # значение (для reg_set / power_plan)
    value_type: str | None = None  # "DWord", "String", "ExpandString"
    undo_target: str | None = None  # что вернуть при откате (исходное значение)
    undo_value: Any | None = None

    def describe(self) -> str:
        return f"{self.kind.value} {self.target}{('\\' + self.name) if self.name else ''}"


@dataclass(frozen=True)
class Rule:
    """Один твик: id, описание, категория, риск, действия."""
    id: str
    name: str
    description: str
    category: str                  # visual | services | startup | telemetry | power | registry
    risk: Risk
    actions: tuple[Action, ...]
    requires_reboot: bool = False
    ms_doc_url: str | None = None  # ссылка на документацию MS (как в ShutUp10)


@dataclass(frozen=True)
class Profile:
    """Именованный набор rule ids."""
    name: str
    description: str
    rule_ids: tuple[str, ...]


@dataclass
class Snapshot:
    """Снимок состояния — для rollback."""
    id: str
    created_at: str
    rules_applied: list[str] = field(default_factory=list)
    actions_undone: list[Action] = field(default_factory=list)
    restore_point_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "rules_applied": self.rules_applied,
            "restore_point_id": self.restore_point_id,
            "actions_undone": [
                {
                    "kind": a.kind.value, "target": a.target,
                    "name": a.name, "value": a.value,
                    "value_type": a.value_type,
                }
                for a in self.actions_undone
            ],
        }


@dataclass(frozen=True)
class Result:
    """Результат apply/dry-run/rollback."""
    ok: bool
    rule_id: str
    applied: tuple[Action, ...] = field(default_factory=tuple)
    skipped: tuple[Action, ...] = field(default_factory=tuple)
    error: str | None = None
