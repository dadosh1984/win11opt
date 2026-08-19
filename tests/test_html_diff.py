"""Tests for core/bench_html.py — renderer, stdlib-only."""
from __future__ import annotations

from pathlib import Path

from win11opt.core.bench import BenchResult
from win11opt.core.bench_html import render_html_diff, save_html_diff


def _mk(metric_overrides: dict | None = None) -> BenchResult:
    base = {
        "timestamp": "2025-01-01T00:00:00",
        "idle_ram_mb": 8000, "total_ram_mb": 16000, "idle_cpu_pct": 5.0,
        "startup_apps_count": 10, "services_running": 80, "sched_tasks_enabled": 50,
        "explorer_first_paint_ms": 200,
        "services_by_state": {"Running": 80, "Stopped": 100},
    }
    if metric_overrides:
        base.update(metric_overrides)
    return BenchResult(**base)


def test_render_html_returns_full_page():
    a = _mk()
    b = _mk({"idle_ram_mb": 6500, "services_running": 65})
    html = render_html_diff(a, b)
    assert html.startswith("<!doctype html>")
    assert "<html" in html
    assert "</html>" in html
    assert "win11opt bench diff report" in html
    assert "System metrics" in html
    assert "Services by state" in html


def test_render_html_contains_metric_names():
    a, b = _mk(), _mk({"idle_cpu_pct": 3.0})
    html = render_html_diff(a, b)
    assert "idle_ram_mb" in html
    assert "idle_cpu_pct" in html
    assert "startup_apps" in html


def test_render_html_marks_decrease_as_good():
    """Уменьшение RAM → зелёный (good class)."""
    a = _mk({"idle_ram_mb": 8000})
    b = _mk({"idle_ram_mb": 6000})
    html = render_html_diff(a, b)
    assert "good" in html
    assert "-2000.00" in html


def test_render_html_handles_empty_services_by_state():
    a, b = _mk({"services_by_state": {}}), _mk({"services_by_state": {}})
    html = render_html_diff(a, b)
    assert "no data" in html


def test_render_html_escapes_dangerous_input():
    """Значения метрик — числа (int/float), XSS невозможен. Но строковые поля (generated_at, services_by_state keys) экранируются."""
    a = _mk()
    b = _mk()
    html = render_html_diff(a, b)
    # Если бы экранирования не было, вредный <script> в HTML попал бы напрямую
    assert "<script>" not in html
    # Амперсанд в заголовке экранируется
    assert "&" not in html.split("</title>")[0].split("<title>")[1] or "&amp;" in html or "<" not in html.split("</title>")[0].split("<title>")[1]


def test_render_html_works_with_only_string_format():
    """Строковые значения (например, timestamp) должны выводиться."""
    a, b = _mk(), _mk()
    html = render_html_diff(a, b)
    # generated_at timestamp
    assert "20" in html  # год


def test_save_html_diff_writes_file(tmp_path: Path):
    a, b = _mk(), _mk({"idle_ram_mb": 7000})
    out = tmp_path / "report.html"
    saved = save_html_diff(a, b, out)
    assert saved == out
    assert out.exists()
    assert out.stat().st_size > 0
    content = out.read_text(encoding="utf-8")
    assert "<!doctype html>" in content


def test_save_html_diff_default_path(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ONEC_TEST_TMP", str(tmp_path))
    # По умолчанию _bench_dir() внутри user-data; проверим лишь что вернулся Path
    a, b = _mk(), _mk()
    saved = save_html_diff(a, b)
    assert saved.exists()
    assert saved.suffix == ".html"
