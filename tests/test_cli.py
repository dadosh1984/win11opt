"""Tests: CLI smoke (аргументы + exit codes)."""
from win11opt.cli import main, build_parser


def test_help_runs():
    """--help не падает."""
    parser = build_parser()
    # parse_args с --help выходит через SystemExit(0); argparse сам
    import pytest
    with pytest.raises(SystemExit) as e:
        parser.parse_args(["--help"])
    assert e.value.code == 0


def test_rules_list_exit_zero(capsys, fake_ps):
    rc = main(["rules", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "visual.disable_animations" in out
    assert "Aggressive" in out


def test_rules_describe_unknown(capsys, fake_ps):
    rc = main(["rules", "describe", "nonexistent"])
    assert rc == 2


def test_apply_dry_run_prints(capsys, fake_ps):
    rc = main(["apply", "--profile", "Balanced", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "visual.disable_animations" in out


def test_apply_unknown_profile(capsys, fake_ps):
    rc = main(["apply", "--profile", "Bogus", "--dry-run"])
    assert rc == 2


def test_snapshot_list_empty(capsys, fake_ps, tmp_path, monkeypatch):
    # Подменяем LOCALAPPDATA, чтобы не дёргать реальную папку
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    rc = main(["snapshot", "list"])
    assert rc == 0
    assert "no snapshots" in capsys.readouterr().out


def test_apply_then_snapshot_list(capsys, fake_ps, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    main(["apply", "--rule", "telemetry.advertising_id"])
    rc = main(["snapshot", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.strip() != "no snapshots"
    assert len(out.strip().splitlines()) >= 1
