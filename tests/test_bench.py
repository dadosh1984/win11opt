"""Тесты для core/bench.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from win11opt.core import bench


def test_benchresult_to_dict_roundtrip():
    r = bench.BenchResult(
        timestamp="2025-01-01T00:00:00",
        idle_ram_mb=8000, total_ram_mb=16000,
        idle_cpu_pct=12.5,
        startup_apps_count=10,
        services_running=80,
        sched_tasks_enabled=200,
        explorer_first_paint_ms=450.0,
    )
    d = r.to_dict()
    r2 = bench.BenchResult.from_dict(d)
    assert r2.idle_ram_mb == 8000
    assert r2.total_ram_mb == 16000
    assert r2.idle_cpu_pct == 12.5
    assert r2.services_running == 80


def test_diff_basic():
    a = bench.BenchResult(
        timestamp="t1", idle_ram_mb=1000, total_ram_mb=16000,
        idle_cpu_pct=20.0, startup_apps_count=10,
        services_running=100, sched_tasks_enabled=200,
        explorer_first_paint_ms=500.0,
    )
    b = bench.BenchResult(
        timestamp="t2", idle_ram_mb=2000, total_ram_mb=16000,
        idle_cpu_pct=5.0, startup_apps_count=8,
        services_running=80, sched_tasks_enabled=150,
        explorer_first_paint_ms=300.0,
    )
    deltas = bench.diff(a, b)
    assert deltas["idle_ram_mb"] == (1000, 2000, 1000)
    assert deltas["services_running"] == (100, 80, -20)
    assert deltas["explorer_first_paint_ms"] == (500.0, 300.0, -200.0)


def test_save_and_load_baseline(tmp_path, monkeypatch):
    """save_baseline + load_baseline round-trip."""
    # Подменяем путь к директории
    monkeypatch.setattr(bench, "_bench_dir", lambda: tmp_path)
    r = bench.BenchResult(
        timestamp="2025-01-01T00:00:00",
        idle_ram_mb=5000, total_ram_mb=16000,
        idle_cpu_pct=10.0, startup_apps_count=5,
        services_running=60, sched_tasks_enabled=120,
        explorer_first_paint_ms=400.0,
    )
    path = bench.save_baseline(r, label="pre")
    assert path.exists()
    assert "pre" in path.name
    r2 = bench.load_baseline(path)
    assert r2.idle_ram_mb == 5000
    assert r2.idle_cpu_pct == 10.0


def test_list_baselines_sorted(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "_bench_dir", lambda: tmp_path)
    # Создаём два файла
    (tmp_path / "20250101-120000.json").write_text("{}")
    (tmp_path / "20250102-120000.json").write_text("{}")
    bls = bench.list_baselines()
    assert len(bls) == 2
    # Сортировка по убыванию (свежие — первыми)
    assert "20250102" in bls[0].name


def test_measure_returns_benchresult():
    """measure() возвращает BenchResult без crash (мок через патч)."""
    # Подменяем _run чтобы не зависеть от реального PowerShell
    real = bench._run
    bench._run = lambda cmd, timeout=10: {
        "FreePhysicalMemory|TotalVisibleMemorySize": "8000|16000",
        "LoadPercentage": "12.5",
        "Count": "10",
    }.get(cmd.split("|")[0] if "|" in cmd else cmd, "0")
    try:
        r = bench.measure()
        assert isinstance(r, bench.BenchResult)
        assert r.timestamp  # ISO format заполнен
    finally:
        bench._run = real
