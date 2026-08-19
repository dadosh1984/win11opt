"""Тесты для core/sysinfo.py."""
from __future__ import annotations

import json
from unittest.mock import patch

from win11opt.core import sysinfo as sysinfo_mod
from win11opt.core.sysinfo import SysInfo


def test_sysinfo_dataclass_defaults():
    s = SysInfo()
    d = s.to_dict()
    assert d["os_caption"] == ""
    assert d["ram_total_mb"] == 0
    assert "notes" in d


def test_collect_parses_powershell_json():
    payload = {
        "os_caption": "Microsoft Windows 11 Pro",
        "os_version": "10.0.22631",
        "os_build": "22631",
        "os_arch": "64-bit",
        "install_date": "2024-12-15",
        "uptime_hours": 12.5,
        "cpu_name": "Intel Core i7-12700K",
        "cpu_cores": 12,
        "cpu_threads": 20,
        "ram_total_mb": 32768,
        "ram_free_mb": 16384,
        "disk_c_free_mb": 200000,
        "disk_c_total_mb": 500000,
        "gpu_name": "NVIDIA GeForce RTX 4070",
    }
    with patch.object(sysinfo_mod.ps, "run_ps", return_value=json.dumps(payload)):
        info = sysinfo_mod.collect()
    assert info.os_caption == "Microsoft Windows 11 Pro"
    assert info.cpu_cores == 12
    assert info.ram_free_mb == 16384
    assert info.gpu_name.startswith("NVIDIA")
    assert info.notes == {}


def test_collect_handles_empty_output():
    with patch.object(sysinfo_mod.ps, "run_ps", return_value=""):
        info = sysinfo_mod.collect()
    assert info.os_caption == ""
    assert "empty powershell output" in info.notes.get("error", "")


def test_collect_handles_powershell_error():
    with patch.object(sysinfo_mod.ps, "run_ps",
                      side_effect=sysinfo_mod.ps.PowerShellError("nope")):
        info = sysinfo_mod.collect()
    assert info.notes.get("error")


def test_collect_handles_bad_json():
    with patch.object(sysinfo_mod.ps, "run_ps", return_value="not json {{{"):
        info = sysinfo_mod.collect()
    assert info.notes.get("error", "").startswith("json parse")


def test_collect_drops_unknown_fields():
    payload = {"os_caption": "Win11", "unknown_garbage": 42, "ram_total_mb": 8192}
    with patch.object(sysinfo_mod.ps, "run_ps", return_value=json.dumps(payload)):
        info = sysinfo_mod.collect()
    assert info.os_caption == "Win11"
    assert info.ram_total_mb == 8192
    # unknown_garbage не должно появиться как атрибут
    assert not hasattr(info, "unknown_garbage")


def test_format_human_contains_key_lines():
    info = SysInfo(
        os_caption="Win11", os_version="10.0.22631", os_build="22631", os_arch="64-bit",
        cpu_name="i7", cpu_cores=8, cpu_threads=16,
        ram_free_mb=4000, ram_total_mb=16000,
        disk_c_free_mb=100000, disk_c_total_mb=500000,
        gpu_name="RTX", install_date="2024-01-01", uptime_hours=5.5,
    )
    out = sysinfo_mod.format_human(info)
    assert "OS:" in out
    assert "Win11" in out
    assert "CPU:" in out
    assert "i7" in out
    assert "RAM:" in out
    assert "4000" in out
    assert "Disk C:" in out
    assert "GPU:" in out
    assert "RTX" in out
