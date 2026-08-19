"""Tests: ps.py (PowerShell wrappers)."""
from __future__ import annotations

from unittest.mock import patch


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
