"""pytest fixtures: подменяем PowerShell-вызовы моками.

Тесты НЕ трогают реальный реестр/службы. Это критично для CI и
для безопасной разработки.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Добавляем src/ в sys.path, чтобы pytest видел пакет без установки
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from win11opt.core import ps


@pytest.fixture
def fake_ps(monkeypatch):
    """Подменяет все PowerShell-функции in-memory словарём."""
    state: dict[str, object] = {
        "registry": {},        # (hive, path, name) -> value
        "services": {},        # name -> state
        "appx_removed": [],    # list of package names removed
        "power_plans": [],     # list of activated GUIDs
        "hibernate": None,     # None | False | True (last set)
        "sched_tasks_disabled": [],  # list of disabled task paths
        "sched_tasks_enabled": [],   # list of (re-)enabled task paths
        "restore_points": [],
    }

    def _key(hive, path, name):
        return (hive, path.lower(), name)

    def fake_reg_get(hive, key_path, name=None):
        if name is None:
            return None
        return state["registry"].get(_key(hive, key_path, name))

    def fake_reg_set(hive, key_path, name, value, value_type="DWord"):
        state["registry"][_key(hive, key_path, name)] = {"value": value, "type": value_type}

    def fake_reg_delete(hive, key_path, name):
        state["registry"].pop(_key(hive, key_path, name), None)

    def fake_service_set_state(name, st):
        state["services"][name] = st

    def fake_appx_remove(package_name, all_users=True):
        state["appx_removed"].append(package_name)

    def fake_power_plan_activate(guid):
        state["power_plans"].append(guid)

    def fake_power_hibernate_set(enabled):
        state["hibernate"] = bool(enabled)

    def fake_sched_task_disable(task_path):
        state["sched_tasks_disabled"].append(task_path)

    def fake_sched_task_enable(task_path):
        state["sched_tasks_enabled"].append(task_path)

    def fake_create_restore_point(description):
        seq = len(state["restore_points"]) + 1
        state["restore_points"].append({"id": seq, "desc": description})
        return seq

    monkeypatch.setattr(ps, "reg_get", fake_reg_get)
    monkeypatch.setattr(ps, "reg_set", fake_reg_set)
    monkeypatch.setattr(ps, "reg_delete", fake_reg_delete)
    monkeypatch.setattr(ps, "service_set_state", fake_service_set_state)
    monkeypatch.setattr(ps, "appx_remove", fake_appx_remove)
    monkeypatch.setattr(ps, "power_plan_activate", fake_power_plan_activate)
    monkeypatch.setattr(ps, "power_hibernate_set", fake_power_hibernate_set)
    monkeypatch.setattr(ps, "sched_task_disable", fake_sched_task_disable)
    monkeypatch.setattr(ps, "sched_task_enable", fake_sched_task_enable)
    monkeypatch.setattr(ps, "create_restore_point", fake_create_restore_point)

    return state
