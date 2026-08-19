"""Тесты для core/bench.py."""
from __future__ import annotations

import json

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
    def fake_run(cmd, timeout=10):
        if "FreePhysicalMemory" in cmd:
            return "8000|16000"
        if "LoadPercentage" in cmd:
            return "12.5"
        if "Get-Service | Group-Object Status" in cmd:
            return "Running=80;Stopped=40;Disabled=5"
        if "Measure-Object" in cmd or "Count" in cmd:
            return "10"
        return "0"
    bench._run = fake_run
    try:
        r = bench.measure()
        assert isinstance(r, bench.BenchResult)
        assert r.timestamp  # ISO format заполнен
        assert r.services_by_state == {"Running": 80, "Stopped": 40, "Disabled": 5}
        assert r.services_running == 80  # производное от services_by_state["Running"]
    finally:
        bench._run = real


def test_diff_report_and_save(tmp_path, monkeypatch):
    """diff_report() + save_diff_report() — JSON-отчёт до/после."""
    monkeypatch.setattr(bench, "_bench_dir", lambda: tmp_path)
    a = bench.BenchResult(
        timestamp="t1", idle_ram_mb=1000, total_ram_mb=16000,
        idle_cpu_pct=20.0, startup_apps_count=10,
        services_running=100, sched_tasks_enabled=200,
        explorer_first_paint_ms=500.0,
        services_by_state={"Running": 100, "Stopped": 20},
    )
    b = bench.BenchResult(
        timestamp="t2", idle_ram_mb=2000, total_ram_mb=16000,
        idle_cpu_pct=5.0, startup_apps_count=8,
        services_running=80, sched_tasks_enabled=150,
        explorer_first_paint_ms=300.0,
        services_by_state={"Running": 80, "Stopped": 40},
    )
    report = bench.diff_report(a, b)
    assert report["before"]["services_running"] == 100
    assert report["after"]["services_running"] == 80
    assert report["deltas"]["services_running"]["delta"] == -20
    assert "generated_at" in report

    path = bench.save_diff_report(a, b, path=tmp_path / "report.json")
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["deltas"]["idle_ram_mb"]["delta"] == 1000


def test_save_diff_report_default_path(tmp_path, monkeypatch):
    """Без явного path — сохраняется в _bench_dir()/diff-<ts>.json."""
    monkeypatch.setattr(bench, "_bench_dir", lambda: tmp_path)
    a = bench.BenchResult(timestamp="t1", idle_ram_mb=1000)
    b = bench.BenchResult(timestamp="t2", idle_ram_mb=2000)
    p = bench.save_diff_report(a, b)
    assert p.parent == tmp_path
    assert p.name.startswith("diff-")
    assert p.suffix == ".json"


def test_diff_report_services_by_state_in_deltas():
    """services_by_state в before/after присутствует; deltas — для скалярных метрик."""
    a = bench.BenchResult(
        timestamp="t1", services_running=10,
        services_by_state={"Running": 10, "Stopped": 20, "Disabled": 5},
    )
    b = bench.BenchResult(
        timestamp="t2", services_running=7,
        services_by_state={"Running": 7, "Stopped": 23, "Disabled": 5},
    )
    rep = bench.diff_report(a, b)
    assert rep["before"]["services_by_state"] == {"Running": 10, "Stopped": 20, "Disabled": 5}
    assert rep["after"]["services_by_state"] == {"Running": 7, "Stopped": 23, "Disabled": 5}
    assert rep["deltas"]["services_running"]["delta"] == -3


def test_measure_ram_uses_kb_not_mb(monkeypatch):
    """Regression: bench.measure() скрипт делит RAM на 1KB, не 1MB.

    WMI возвращает KB. PowerShell делит на 1KB → MB.
    Мок возвращает уже-MB значения (как будто PowerShell сделал деление).
    """
    # PowerShell выводит "<free_mb>|<total_mb>" (после деления на 1KB)
    fake_output = "20480|40960"  # 20 GB free / 40 GB total (в MB)
    monkeypatch.setattr(bench, "_run", lambda *a, **kw: fake_output)
    result = bench.measure()
    assert result.idle_ram_mb == 20480
    assert result.total_ram_mb == 40960


def test_bench_powershell_script_divides_ram_by_kb():
    """Regression: bench PowerShell делит RAM на 1KB."""
    import inspect
    import re
    source = inspect.getsource(bench.measure)
    # Берём только строки без '#' (комментарии)
    code_lines = [
        l for l in source.split("\n")
        if "FreePhysicalMemory" in l and "1" in l and not l.strip().startswith("#")
    ]
    assert code_lines, "RAM-строка не найдена в measure()"
    assert re.search(r"/\s*1KB", code_lines[0]), (
        f"bench должен делить RAM на 1KB: {code_lines[0]}"
    )
    assert not re.search(r"/\s*1MB", code_lines[0]), (
        f"RAM делить на 1MB — баг: {code_lines[0]}"
    )
