"""CLI — argparse, sub-commands: apply, snapshot, rules.

ponytail: rung 2 — argparse вместо click/typer. Идёт в stdlib, меньше
зависимостей для single-EXE.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .. import __version__
from ..core import engine, ps, snapshot as snap_mod
from ..core.models import Snapshot
from ..i18n import _, N_, get_language, set_language
from ..rules import PRESETS, get_preset, get_rules, validate_dir


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )


def cmd_rules_list(_args: argparse.Namespace) -> int:
    """Список всех доступных правил с категорией и риском."""
    rules = get_rules()
    rows = []
    for rid, rule in rules.items():
        rows.append((rid, rule.category, rule.risk.value, rule.name))
    rows.sort()
    print(f"{'ID':<40} {'CATEGORY':<12} {'RISK':<8} NAME")
    print("-" * 90)
    for rid, cat, risk, name in rows:
        print(f"{rid:<40} {cat:<12} {risk:<8} {name}")
    print()
    print("Presets:")
    for p in PRESETS:
        print(f"  {p.name:<12} — {p.description}")
    return 0


def cmd_rules_describe(args: argparse.Namespace) -> int:
    rules = get_rules()
    rule = rules.get(args.id)
    if rule is None:
        print(f"rule not found: {args.id}", file=sys.stderr)
        return 2
    print(f"id          {rule.id}")
    print(f"name        {rule.name}")
    print(f"category    {rule.category}")
    print(f"risk        {rule.risk.value}")
    print(f"description {rule.description}")
    if rule.ms_doc_url:
        print(f"docs        {rule.ms_doc_url}")
    print(f"actions     {len(rule.actions)}")
    for i, a in enumerate(rule.actions, 1):
        print(f"  {i}. {a.describe()}")
    return 0


def cmd_rules_validate(_args: argparse.Namespace) -> int:
    """Валидировать все YAML-пресеты в rules/."""
    errs = validate_dir()
    if not errs:
        print(_("OK: all YAML presets are valid"))
        return 0
    for path, msgs in errs.items():
        print(_("FAIL: %s") % path)
        for m in msgs:
            print(f"  • {m}")
    return 1


def cmd_apply(args: argparse.Namespace) -> int:
    """Применить пресет или одиночное правило."""
    rules = get_rules()
    if args.profile:
        preset = get_preset(args.profile)
        if preset is None:
            print(f"preset not found: {args.profile}", file=sys.stderr)
            return 2
        rule_ids = list(preset.rule_ids)
    elif args.rule:
        if args.rule not in rules:
            print(f"rule not found: {args.rule}", file=sys.stderr)
            return 2
        rule_ids = [args.rule]
    else:
        print("specify --profile or --rule", file=sys.stderr)
        return 2

    actions = []
    for rid in rule_ids:
        rule = rules[rid]
        actions.extend(rule.actions)

    if args.dry_run:
        print(_("DRY-RUN: %d rules, %d actions") % (len(rule_ids), len(actions)))
        for rid in rule_ids:
            print(f"  • {rid}")
        applied = engine.apply(actions, dry_run=True)
    else:
        snap = snap_mod.make_snapshot(rule_ids, [])
        # Сначала apply и capture, потом сохранить snapshot с actions_undone
        applied = engine.apply(actions, dry_run=False)
        snap_obj = Snapshot(
            id=snap.id, created_at=snap.created_at,
            rules_applied=rule_ids, actions_undone=applied,
            restore_point_id=snap.restore_point_id,
        )
        snap_mod.save(snap_obj)
        print(_("APPLIED %d actions — snapshot %s") % (len(applied), snap_obj.id))
        print(f"snapshot: {snap_obj.id}  restore_point: {snap_obj.restore_point_id}")

    for a in applied:
        print(f"  [{a.kind.value}] {a.target} {a.name or ''}")
    return 0


def cmd_snapshot_list(_args: argparse.Namespace) -> int:
    snaps = snap_mod.list_snapshots()
    if not snaps:
        print("no snapshots")
        return 0
    for sid in snaps:
        print(sid)
    return 0


def cmd_snapshot_restore(args: argparse.Namespace) -> int:
    try:
        snap = snap_mod.load(args.id)
    except FileNotFoundError:
        print(f"snapshot not found: {args.id}", file=sys.stderr)
        return 2
    if args.dry_run:
        print(f"DRY-RUN: would rollback {len(snap.actions_undone)} action(s) from {snap.id}")
        return 0
    engine.rollback(snap)
    print(f"OK: rolled back snapshot {snap.id}")
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    """Бенчмарк: измерение отзывчивости, save/diff."""
    from ..core import bench as benchmod

    if getattr(args, "bench_action", None) == "save":
        label = getattr(args, "label", None)
        result = benchmod.measure()
        path = benchmod.save_baseline(result, label)
        print(f"saved: {path}")
        print(f"  idle_ram: {result.idle_ram_mb} MB / {result.total_ram_mb} MB")
        print(f"  idle_cpu: {result.idle_cpu_pct}%")
        print(f"  startup_apps: {result.startup_apps_count}")
        print(f"  services_running: {result.services_running}")
        print(f"  sched_tasks_enabled: {result.sched_tasks_enabled}")
        print(f"  explorer_first_paint: {result.explorer_first_paint_ms} ms")
        if result.services_by_state:
            parts = ", ".join(f"{k}={v}" for k, v in sorted(result.services_by_state.items()))
            print(f"  services_by_state: {{{parts}}}")
        return 0

    if getattr(args, "bench_action", None) == "diff":
        baselines = benchmod.list_baselines()
        if not baselines:
            print("no baselines — run: win11opt bench save")
            return 1
        target = baselines[0] if args.bench_target == "latest" else Path(args.bench_target)
        if not target.exists():
            print(f"baseline not found: {target}")
            return 1
        before = benchmod.load_baseline(target)
        after = benchmod.measure()
        print(f"baseline: {target.name} ({before.timestamp})")
        print(f"current:  {after.timestamp}")
        print()
        print(f"{'metric':<24} {'before':>12} {'after':>12} {'delta':>12}")
        print("-" * 64)
        deltas = benchmod.diff(before, after)
        for metric, (va, vb, delta) in deltas.items():
            sign = "+" if delta > 0 else ""
            print(f"{metric:<24} {va:>12} {vb:>12} {sign}{delta:>11}")
        out_path = getattr(args, "out", None)
        if out_path:
            saved = benchmod.save_diff_report(before, after, Path(out_path))
            print(f"\nsaved diff report: {saved}")
        return 0

    if getattr(args, "bench_action", None) == "list":
        baselines = benchmod.list_baselines()
        if not baselines:
            print("no baselines")
        for b in baselines:
            print(b.name)
        return 0

    # default: measure and print
    result = benchmod.measure()
    print(f"timestamp: {result.timestamp}")
    print(f"idle_ram: {result.idle_ram_mb} MB / {result.total_ram_mb} MB")
    print(f"idle_cpu: {result.idle_cpu_pct}%")
    print(f"startup_apps: {result.startup_apps_count}")
    print(f"services_running: {result.services_running}")
    print(f"sched_tasks_enabled: {result.sched_tasks_enabled}")
    print(f"explorer_first_paint: {result.explorer_first_paint_ms} ms")
    print()
    print("tip: save baseline before applying rules: win11opt bench save --label pre")
    print("     then compare:   win11opt bench diff latest")
    return 0


def cmd_gui(_args: argparse.Namespace) -> int:
    """Запустить Tkinter GUI."""
    from ..gui.app import main_gui
    return main_gui()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="win11opt",
        description="Win11Optimizer — отзывчивость уровня Windows XP",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--lang", choices=["en", "ru"], help="язык для этого вызова (en/ru)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_rules = sub.add_parser("rules", help="управление правилами")
    p_rules_sub = p_rules.add_subparsers(dest="subcmd", required=True)
    p_rules_sub.add_parser("list").set_defaults(func=cmd_rules_list)
    p_describe = p_rules_sub.add_parser("describe")
    p_describe.add_argument("id")
    p_describe.set_defaults(func=cmd_rules_describe)
    p_rules_sub.add_parser("validate").set_defaults(func=cmd_rules_validate)

    p_apply = sub.add_parser("apply", help="применить пресет или правило")
    p_apply.add_argument("--profile", help="имя пресета (Aggressive/Balanced/Privacy)")
    p_apply.add_argument("--rule", help="id одиночного правила")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.set_defaults(func=cmd_apply)

    p_snap = sub.add_parser("snapshot", help="снимки и откат")
    p_snap_sub = p_snap.add_subparsers(dest="subcmd", required=True)
    p_snap_sub.add_parser("list").set_defaults(func=cmd_snapshot_list)
    p_snap_restore = p_snap_sub.add_parser("restore")
    p_snap_restore.add_argument("id")
    p_snap_restore.add_argument("--dry-run", action="store_true")
    p_snap_restore.set_defaults(func=cmd_snapshot_restore)

    p_bench = sub.add_parser("bench", help="базовый бенчмарк с save/diff")
    p_bench_sub = p_bench.add_subparsers(dest="bench_action")
    p_bench_save = p_bench_sub.add_parser("save", help="сохранить baseline")
    p_bench_save.add_argument("--label", help="метка (например 'pre', 'after-tier1')")
    p_bench_diff = p_bench_sub.add_parser("diff", help="сравнить с baseline")
    p_bench_diff.add_argument("bench_target", nargs="?", default="latest", help="latest или путь к .json")
    p_bench_diff.add_argument("--out", help="сохранить diff-отчёт в JSON по указанному пути")
    p_bench_sub.add_parser("list", help="список baselines")
    p_bench.set_defaults(func=cmd_bench)

    p_gui = sub.add_parser("gui", help="запустить графический интерфейс")
    p_gui.set_defaults(func=cmd_gui)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Apply --lang if specified
    if getattr(args, "lang", None):
        set_language(args.lang)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
