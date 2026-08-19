"""Bench — измерение отзывчивости системы.

Метрики:
- idle_ram_mb: количество свободной RAM (MB)
- idle_cpu_pct: %CPU idle (среднее за 2 сек)
- startup_apps_count: количество автозагрузки
- services_running: количество запущенных служб
- sched_tasks_enabled: количество включённых scheduled tasks
- explorer_first_paint_ms: время запуска explorer.exe (от start до видимого окна)

ponytail: rung 4 — замеры нужны для сравнения до/после твиков,
не заменяя ощущение пользователя но давая объективные числа.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class BenchResult:
    """Снимок состояния системы для сравнения до/после."""
    timestamp: str
    idle_ram_mb: int = 0
    total_ram_mb: int = 0
    idle_cpu_pct: float = 0.0
    startup_apps_count: int = 0
    services_running: int = 0
    sched_tasks_enabled: int = 0
    # explorer_first_paint_ms: запуск explorer.exe и замер до готовности окна
    explorer_first_paint_ms: float = 0.0
    # services_by_state: {Running: n, Stopped: m, Disabled: k, ...}
    services_by_state: dict[str, int] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> BenchResult:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def _run(cmd: str, timeout: int = 10) -> str:
    """Запустить PowerShell-команду и вернуть stdout."""
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
{cmd}
"""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=timeout,
        )
        return (out.stdout or "").strip()
    except Exception as e:
        log.warning("bench command failed: %s: %s", cmd[:60], e)
        return ""


def _parse_int(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0


def _parse_float(s: str) -> float:
    m = re.search(r"[\d.]+", s or "")
    return float(m.group()) if m else 0.0


def measure() -> BenchResult:
    """Снять текущий снимок состояния."""
    # 1. RAM
    ram = _run("(Get-CimInstance Win32_OperatingSystem | Select-Object -First 1 | ForEach-Object { '{0}|{1}' -f [int]($_.FreePhysicalMemory/1MB), [int]($_.TotalVisibleMemorySize/1MB) })")
    parts = ram.split("|") if ram else ["0", "0"]
    idle_ram = _parse_int(parts[0]) if len(parts) >= 1 else 0
    total_ram = _parse_int(parts[1]) if len(parts) >= 2 else 0

    # 2. CPU idle (среднее за 2 сек)
    cpu = _run("$samples = 1..4 | ForEach-Object { (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average }; [math]::Round(($samples | Measure-Object -Average).Average, 1)")
    idle_cpu = _parse_float(cpu)

    # 3. Startup apps count
    startup_out = _run("(Get-CimInstance Win32_StartupCommand | Measure-Object).Count")
    startup_count = _parse_int(startup_out)

    # 4. Services by state
    svc_by_state_raw = _run("(Get-Service | Group-Object Status | ForEach-Object { '{0}={1}' -f $_.Name, $_.Count }) -join ';'")
    services_by_state: dict[str, int] = {}
    for chunk in (svc_by_state_raw or "").split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        name, _, count = chunk.partition("=")
        try:
            services_by_state[name.strip()] = int(count.strip())
        except ValueError:
            continue
    svc_count = services_by_state.get("Running", 0)

    # 5. Scheduled tasks enabled
    tasks = _run("((Get-ScheduledTask | Where-Object { $_.State -eq 'Ready' }) | Measure-Object).Count")
    tasks_count = _parse_int(tasks)

    # 6. Explorer first paint (approximate)
    # Запускаем explorer и замеряем через [System.Diagnostics.Process]
    # В headless среде (CI, RDP без desktop) вернёт 0
    explorer_ms = _measure_explorer_paint()

    return BenchResult(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        idle_ram_mb=idle_ram,
        total_ram_mb=total_ram,
        idle_cpu_pct=idle_cpu,
        startup_apps_count=startup_count,
        services_running=svc_count,
        sched_tasks_enabled=tasks_count,
        explorer_first_paint_ms=explorer_ms,
        services_by_state=services_by_state,
    )


def _measure_explorer_paint() -> float:
    """Замерить время до появления главного окна Проводника.

    Только если есть desktop session (иначе вернёт 0).
    """
    script = """
$ErrorActionPreference = 'SilentlyContinue'
if (-not [Environment]::UserInteractive) { return 0 }
try {
    $proc = Start-Process -FilePath 'explorer.exe' -PassThru
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $proc.WaitForInputIdle(5000) | Out-Null
    $sw.Stop()
    $ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 0)
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    return $ms
} catch { return 0 }
"""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=8,
        )
        return _parse_float(out.stdout)
    except Exception:
        return 0.0


# ---------- Persistence ----------

def _bench_dir() -> Path:
    base = Path.home() / "AppData" / "Local" / "win11opt" / "bench"
    base.mkdir(parents=True, exist_ok=True)
    return base


def list_baselines() -> list[Path]:
    return sorted(_bench_dir().glob("*.json"), reverse=True)


def save_baseline(result: BenchResult, label: str | None = None) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{ts}-{label}" if label else ts
    path = _bench_dir() / f"{name}.json"
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_baseline(path: Path) -> BenchResult:
    return BenchResult.from_dict(json.loads(path.read_text(encoding="utf-8")))


def diff(a: BenchResult, b: BenchResult) -> dict[str, tuple[float, float, float]]:
    """Сравнить два снимка. Возвращает {metric: (value_a, value_b, delta)}."""
    fields_to_compare = [
        "idle_ram_mb", "idle_cpu_pct", "startup_apps_count",
        "services_running", "sched_tasks_enabled", "explorer_first_paint_ms",
    ]
    out = {}
    for f in fields_to_compare:
        va = getattr(a, f, 0)
        vb = getattr(b, f, 0)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            out[f] = (va, vb, vb - va)
    return out


def diff_report(a: BenchResult, b: BenchResult) -> dict:
    """JSON-отчёт до/после: полные снимки + дельты. ponytail: rung 4 — измеримый артефакт."""
    return {
        "before": a.to_dict(),
        "after": b.to_dict(),
        "deltas": {m: {"before": va, "after": vb, "delta": vb - va}
                   for m, (va, vb, delta) in diff(a, b).items()},
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def save_diff_report(a: BenchResult, b: BenchResult, path: Path | None = None) -> Path:
    """Сохранить diff-отчёт в JSON. Если path не указан — в _bench_dir()/diff-<ts>.json."""
    if path is None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = _bench_dir() / f"diff-{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(diff_report(a, b), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
