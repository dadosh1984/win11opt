"""Tests: ps.py (PowerShell wrappers)."""
from __future__ import annotations

from unittest.mock import patch

import pytest


def test_sched_task_enable_calls_run_ps():
    """Regression: ps.sched_task_enable был мёртвым кодом (script без run_ps)."""
    from win11opt.core import ps
    with patch.object(ps, "run_ps") as mock_run:
        ps.sched_task_enable("\\Foo\\Bar")
    assert mock_run.called
    script = mock_run.call_args[0][0]
    assert "\\Foo\\Bar" in script
    assert "Disable:$false" in script


def test_sched_task_disable_calls_run_ps():
    """Парный тест: disable должен вызывать run_ps."""
    from win11opt.core import ps
    with patch.object(ps, "run_ps") as mock_run:
        ps.sched_task_disable("\\Foo\\Bar")
    assert mock_run.called
    script = mock_run.call_args[0][0]
    assert "\\Foo\\Bar" in script
    assert "Disable:$true" in script


def test_run_ps_raises_on_missing_powershell(monkeypatch):
    """Если powershell.exe не найден — понятная ошибка."""
    import subprocess as sp

    from win11opt.core import ps
    monkeypatch.setattr(sp, "run", lambda *a, **kw: (_ for _ in ()).throw(
        FileNotFoundError("powershell.exe")))
    with pytest.raises(ps.PowerShellError, match="not found"):
        ps.run_ps("Write-Host hi")


def test_is_admin_returns_bool():
    """_is_admin() возвращает bool без исключений."""
    from win11opt.core.engine import _is_admin
    result = _is_admin()
    assert isinstance(result, bool)


def test_run_ps_uses_utf8_encoding():
    """run_ps() должен ставить encoding='utf-8' для subprocess.run.

    Без этого PowerShell 5.1 выводит в системной кодировке (cp1251/cp866
    на русской Windows), и Python читает мусор.
    """
    import inspect

    from win11opt.core import ps
    source = inspect.getsource(ps.run_ps)
    assert 'encoding="utf-8"' in source, (
        "run_ps() должен читать stdout как UTF-8"
    )
    assert "utf-8-sig" in source, (
        "run_ps() должен писать .ps1 с UTF-8 BOM (utf-8-sig) "
        "— иначе PowerShell 5.1 трактует скрипт как cp1251"
    )
