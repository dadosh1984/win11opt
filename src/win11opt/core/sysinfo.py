"""SysInfo — read-only снимок системы (OS, CPU, RAM, Disk, GPU, uptime).

ponytail: rung 4 — пользователь видит контекст ДО оптимизации.
Никаких изменений в системе, только чтение через Get-CimInstance.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field

from . import ps

log = logging.getLogger(__name__)


@dataclass
class SysInfo:
    """Снимок информации о системе."""
    os_caption: str = ""
    os_version: str = ""
    os_build: str = ""
    os_arch: str = ""
    install_date: str = ""
    uptime_hours: float = 0.0
    cpu_name: str = ""
    cpu_cores: int = 0
    cpu_threads: int = 0
    ram_total_mb: int = 0
    ram_free_mb: int = 0
    disk_c_free_mb: int = 0
    disk_c_total_mb: int = 0
    gpu_name: str = ""
    notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


_SYSINFO_SCRIPT = r"""
$ErrorActionPreference = 'SilentlyContinue'
$os = Get-CimInstance Win32_OperatingSystem | Select-Object -First 1
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object -First 1
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime

$obj = [PSCustomObject]@{
  os_caption     = if ($os) { $os.Caption } else { '' }
  os_version     = if ($os) { $os.Version } else { '' }
  os_build       = if ($os) { $os.BuildNumber } else { '' }
  os_arch        = if ($os) { $os.OSArchitecture } else { '' }
  install_date   = if ($os) { ($os.InstallDate -as [datetime]).ToString('yyyy-MM-dd') } else { '' }
  uptime_hours   = if ($boot) { [math]::Round(((Get-Date) - $boot).TotalHours, 1) } else { 0 }
  cpu_name       = if ($cpu) { $cpu.Name } else { '' }
  cpu_cores      = if ($cpu) { $cpu.NumberOfCores } else { 0 }
  cpu_threads    = if ($cpu) { $cpu.NumberOfLogicalProcessors } else { 0 }
  ram_total_mb   = if ($os) { [int]($os.TotalVisibleMemorySize / 1MB) } else { 0 }
  ram_free_mb    = if ($os) { [int]($os.FreePhysicalMemory / 1MB) } else { 0 }
  disk_c_free_mb = if ($disk) { [int](($disk.FreeSpace) / 1MB) } else { 0 }
  disk_c_total_mb= if ($disk) { [int](($disk.Size) / 1MB) } else { 0 }
  gpu_name       = if ($gpu) { $gpu.Name } else { '' }
}
$obj | ConvertTo-Json -Compress
"""


def collect() -> SysInfo:
    """Снять снимок системы. На non-Windows / без PowerShell вернёт SysInfo с пустыми полями."""
    try:
        out = ps.run_ps(_SYSINFO_SCRIPT, timeout=15)
    except (ps.PowerShellError, OSError, FileNotFoundError) as e:
        log.warning("sysinfo collection failed: %s", e)
        return SysInfo(notes={"error": str(e)})

    out = out.strip()
    if not out:
        return SysInfo(notes={"error": "empty powershell output"})

    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        log.warning("sysinfo JSON parse failed: %s; raw=%r", e, out[:200])
        return SysInfo(notes={"error": f"json parse: {e}"})

    if not isinstance(data, dict):
        return SysInfo(notes={"error": "unexpected payload"})

    known = {f for f in SysInfo.__dataclass_fields__ if f != "notes"}
    clean = {k: v for k, v in data.items() if k in known}
    return SysInfo(**clean)


def format_human(info: SysInfo) -> str:
    """Человекочитаемое представление для CLI / GUI."""
    lines = [
        f"OS:         {info.os_caption} {info.os_version} (build {info.os_build}, {info.os_arch})",
        f"Install:    {info.install_date}",
        f"Uptime:     {info.uptime_hours} h",
        f"CPU:        {info.cpu_name} ({info.cpu_cores}c/{info.cpu_threads}t)",
        f"RAM:        {info.ram_free_mb} MB free / {info.ram_total_mb} MB total",
        f"Disk C:     {info.disk_c_free_mb} MB free / {info.disk_c_total_mb} MB total",
        f"GPU:        {info.gpu_name}",
    ]
    if info.notes.get("error"):
        lines.append(f"(warning: {info.notes['error']})")
    return "\n".join(lines)
