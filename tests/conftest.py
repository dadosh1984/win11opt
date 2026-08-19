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

from win11opt.core import ps  # noqa: E402


@pytest.fixture
def fake_ps(monkeypatch):
    """Подменяет все PowerShell-функции in-memory словарём."""
    state: dict[str, object] = {
        "registry": {},        # (hive, path, name) -> value
        "services": {},        # name -> state
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

    def fake_create_restore_point(description):
        seq = len(state["restore_points"]) + 1
        state["restore_points"].append({"id": seq, "desc": description})
        return seq

    monkeypatch.setattr(ps, "reg_get", fake_reg_get)
    monkeypatch.setattr(ps, "reg_set", fake_reg_set)
    monkeypatch.setattr(ps, "reg_delete", fake_reg_delete)
    monkeypatch.setattr(ps, "service_set_state", fake_service_set_state)
    monkeypatch.setattr(ps, "create_restore_point", fake_create_restore_point)

    return state
