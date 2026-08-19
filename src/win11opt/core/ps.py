"""PowerShell executor — единая точка выхода в систему.

Все изменения реестра / служб / restore point идут через powershell.exe.
Никаких прямых Win32 вызовов — чтобы поведение совпадало с тем, что
делает пользователь руками, и чтобы было легко читать undo-лог.

ponytail: rung 5 cost — subprocess + временный .ps1 вместо встроенного
PowerShell SDK. Дешевле, читаемо, отлаживаемо.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class PowerShellError(RuntimeError):
    """PowerShell вернул ненулевой exit code или исключение."""


def run_ps(script: str, *, timeout: int = 60) -> str:
    """Выполнить PowerShell-скрипт, вернуть stdout.

    Использует powershell.exe (Windows PowerShell 5.x), который есть на
    любой Win10/11. -NoProfile -NonInteractive — без пользовательских
    хуков и блокировок.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ps1", delete=False, encoding="utf-8"
    ) as f:
        f.write(script)
        path = f.name
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", path,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    finally:
        Path(path).unlink(missing_ok=True)

    if proc.returncode != 0:
        raise PowerShellError(
            f"powershell exit {proc.returncode}\n"
            f"STDOUT: {proc.stdout[:500]}\n"
            f"STDERR: {proc.stderr[:500]}"
        )
    return proc.stdout


def reg_get(hive: str, key_path: str, name: str | None = None) -> Any:
    """Прочитать значение реестра. None если нет."""
    target = f"{hive}:\\{key_path}"
    name_arg = f"-Name '{name}'" if name else ""
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$val = Get-ItemProperty -Path '{target}' {name_arg} -ErrorAction SilentlyContinue
if ($val -eq $null) {{ exit 0 }}
@($val.PSObject.Properties | ForEach-Object {{
  if ($_.Name -notmatch '^PS') {{
    [PSCustomObject]@{{ Name=$_.Name; Type=$_.TypeNameOfValue; Value=$_.Value }}
  }}
}} | ConvertTo-Json -Compress)
"""
    out = run_ps(script)
    if not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def reg_set(hive: str, key_path: str, name: str, value: Any, value_type: str = "DWord") -> None:
    """Записать значение в реестр. Создаёт ключ при отсутствии."""
    target = f"{hive}:\\{key_path}"
    if isinstance(value, str):
        val_literal = value.replace("'", "''")
        expr = f"'{val_literal}'"
    elif isinstance(value, bool):
        expr = "1" if value else "0"
    else:
        expr = str(value)
    script = f"""
$ErrorActionPreference = 'Stop'
if (-not (Test-Path '{target}')) {{ New-Item -Path '{target}' -Force | Out-Null }}
New-ItemProperty -Path '{target}' -Name '{name}' -Value {expr} -PropertyType '{value_type}' -Force | Out-Null
"""
    run_ps(script)


def reg_delete(hive: str, key_path: str, name: str) -> None:
    """Удалить значение реестра."""
    target = f"{hive}:\\{key_path}"
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
Remove-ItemProperty -Path '{target}' -Name '{name}' -Force -ErrorAction SilentlyContinue
"""
    run_ps(script)


def service_set_state(name: str, state: str) -> None:
    """Изменить состояние службы: 'Disabled' | 'Manual' | 'Automatic'."""
    script = f"""
$ErrorActionPreference = 'Stop'
Set-Service -Name '{name}' -StartupType {state} -ErrorAction Stop
"""
    run_ps(script)


def create_restore_point(description: str) -> int | None:
    """Создать точку восстановления. Возвращает sequence number или None."""
    script = f"""
$ErrorActionPreference = 'SilentlyContinue'
Checkpoint-Computer -Description '{description.replace(chr(39), chr(39)*2)}' -RestorePointType 'APPLICATION_UNINSTALL' -ErrorAction SilentlyContinue
"""
    try:
        run_ps(script, timeout=120)
    except PowerShellError:
        return None
    # Получаем sequence number созданной точки
    out = run_ps(f"""
Get-ComputerRestorePoint | Sort-Object -Property SequenceNumber -Descending | Select-Object -First 1 | ConvertTo-Json -Compress
""")
    try:
        return json.loads(out).get("SequenceNumber")
    except (json.JSONDecodeError, AttributeError):
        return None


def list_startup_apps() -> list[dict[str, str]]:
    """Список автозагрузки: Run-ключи реестра."""
    out = run_ps("""
$paths = @(
  'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
  'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'
)
$result = @()
foreach ($p in $paths) {
  if (Test-Path $p) {
    $items = Get-ItemProperty -Path $p -ErrorAction SilentlyContinue
    if ($items) {
      $items.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
        $result += [PSCustomObject]@{ Hive = ($p.Split(':')[0]); Path = ($p.Split(':')[1].TrimStart('\\')); Name = $_.Name; Value = ($_.Value -as [string]) }
      }
    }
  }
}
$result | ConvertTo-Json -Compress
""")
    if not out.strip():
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return []


def power_plan_activate(guid: str) -> None:
    """Активировать план электропитания по GUID."""
    script = f"""
powercfg /setactive {guid}
"""
    run_ps(script)
