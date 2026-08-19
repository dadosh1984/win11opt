"""Tkinter GUI — минимальный, но полезный.

Структура:
  ┌────────────────────────────────────────────────────┐
  │ Preset: [Balanced ▾]   [Bench Before] [Bench After]│
  ├──────────────┬─────────────────────────────────────┤
  │ Categories   │ Rules (checkboxes + risk + docs)   │
  │ • visual     │ � disable_animations       [low]   │
  │ • services   │ ☑ classic_context_menu     [low]   │
  │ • telemetry  │ ☐ advertising_id           [low]   │
  │ • power      │ ☐ ...                              │
  │ • registry   │                                     │
  ├──────────────┴─────────────────────────────────────┤
  │ [Dry-run]  [Apply]  [Snapshots…]  [Undo…]          │
  │ Status: idle                                        │
  └────────────────────────────────────────────────────┘

ponytail: rung 2 — Tkinter вместо PyQt/PySide. Single-EXE без зависимостей.
"""
from __future__ import annotations

import datetime as dt
import logging
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .. import __version__
from ..core import bench as bench_mod
from ..core import engine, ps, snapshot as snap_mod
from ..core.models import Snapshot
from ..i18n import _
from ..rules import PRESETS, get_preset, get_rules

log = logging.getLogger(__name__)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(_("Win11Optimizer %s") % __version__)
        self.root.geometry("900x600")
        self.rules = get_rules()
        self.selected: dict[str, tk.BooleanVar] = {}
        self.bench_before: dict | None = None
        self._build()

    def _build(self) -> None:
        # Top bar: preset + bench
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(top, text=_("Preset:")).pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        cb = ttk.Combobox(
            top, textvariable=self.preset_var, state="readonly", width=20,
            values=[p.name for p in PRESETS],
        )
        cb.pack(side=tk.LEFT, padx=4)
        cb.bind("<<ComboboxSelected>>", self._on_preset)
        ttk.Button(top, text=_("Apply preset"), command=self._apply_preset_selection).pack(side=tk.LEFT, padx=4)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(top, text=_("Bench before"), command=self._bench_before).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=_("Bench after"), command=self._bench_after).pack(side=tk.LEFT, padx=4)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(top, text=_("System Info"), command=self._open_sysinfo).pack(side=tk.LEFT, padx=4)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(top, text=_("Export…"), command=self._export_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text=_("Import…"), command=self._import_dialog).pack(side=tk.LEFT, padx=4)

        # Search bar (фильтр по id + description)
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Label(search_frame, text=_("Search:")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Body: categories | rules
        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Categories tree (left)
        cats_frame = ttk.LabelFrame(body, text=_("Categories"))
        cats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.tree = ttk.Treeview(cats_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_category_select)
        self.cat_items: dict[str, str] = {}
        for cat in sorted({r.category for r in self.rules.values()}):
            iid = self.tree.insert("", tk.END, text=cat)
            self.cat_items[iid] = cat

        # Rules list (right)
        rules_frame = ttk.LabelFrame(body, text=_("Rules"))
        rules_frame.grid(row=0, column=1, sticky="nsew")
        self.rules_canvas = tk.Canvas(rules_frame, borderwidth=0, highlightthickness=0)
        scroll = ttk.Scrollbar(rules_frame, orient=tk.VERTICAL, command=self.rules_canvas.yview)
        self.rules_canvas.configure(yscrollcommand=scroll.set)
        self.rules_inner = ttk.Frame(self.rules_canvas)
        self.rules_inner.bind("<Configure>",
            lambda e: self.rules_canvas.configure(scrollregion=self.rules_canvas.bbox("all")))
        self.rules_canvas.create_window((0, 0), window=self.rules_inner, anchor="nw")
        self.rules_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._render_rules("visual")  # default

        # Bottom: actions
        bottom = ttk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(bottom, text=_("Dry-run selected"), command=self._dry_run).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom, text=_("Apply selected"), command=self._apply).pack(side=tk.LEFT, padx=4)
        ttk.Separator(bottom, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(bottom, text=_("Snapshots…"), command=self._open_snapshots).pack(side=tk.LEFT, padx=4)

        # Status bar
        self.status_var = tk.StringVar(value=f"idle — {len(self.rules)} rules loaded")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )

        # Progress bar (hidden until apply)
        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4))
        self.progress.pack_forget()

    def _render_rules(self, category: str) -> None:
        for w in self.rules_inner.winfo_children():
            w.destroy()
        self.selected.clear()
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        for rid in sorted(r for r, rule in self.rules.items() if rule.category == category):
            rule = self.rules[rid]
            if query and query not in rid.lower() and query not in rule.description.lower():
                continue
            var = tk.BooleanVar(value=False)
            self.selected[rid] = var
            frame = ttk.Frame(self.rules_inner)
            frame.pack(fill=tk.X, anchor=tk.W)
            ttk.Checkbutton(frame, variable=var).pack(side=tk.LEFT)
            label_text = f"{rid}  [{rule.risk.value}]"
            if rule.requires_reboot:
                label_text += "  (reboot)"
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
            ttk.Label(
                frame, text=rule.description, foreground="gray",
                wraplength=500, justify=tk.LEFT,
            ).pack(side=tk.LEFT, padx=8)

    def _on_search(self) -> None:
        """Перерисовать текущую категорию с учётом поискового запроса."""
        sel = self.tree.selection()
        cat = self.cat_items.get(sel[0]) if sel else "visual"
        self._render_rules(cat)

    def _open_sysinfo(self) -> None:
        """Открыть окно с информацией о системе (read-only)."""
        from ..core import sysinfo as sysinfo_mod
        win = tk.Toplevel(self.root)
        win.title(_("System Information"))
        win.geometry("600x300")
        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        info = sysinfo_mod.collect()
        txt.insert(tk.END, sysinfo_mod.format_human(info))
        txt.configure(state=tk.DISABLED)
        ttk.Button(win, text=_("Refresh"), command=lambda: self._refresh_sysinfo(txt)).pack(pady=4)

    def _refresh_sysinfo(self, txt: tk.Text) -> None:
        from ..core import sysinfo as sysinfo_mod
        info = sysinfo_mod.collect()
        txt.configure(state=tk.NORMAL)
        txt.delete("1.0", tk.END)
        txt.insert(tk.END, sysinfo_mod.format_human(info))
        txt.configure(state=tk.DISABLED)

    def _export_dialog(self) -> None:
        """Экспортировать выбранные чекбоксы в YAML-профиль."""
        from tkinter import filedialog, messagebox
        from ..rules import export as export_mod
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Export", "No rules selected")
            return
        path = filedialog.asksaveasfilename(
            title="Export profile",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml"), ("All", "*.*")],
            initialfile="my-profile.yaml",
        )
        if not path:
            return
        try:
            export_mod.export_profile(
                name="CustomProfile",
                description=f"Exported {len(ids)} rules from win11opt GUI",
                rule_ids=ids,
                rules_lookup=self.rules,
                out_path=Path(path),
            )
            self._set_status(f"exported {len(ids)} rules → {path}")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Export failed", str(e))

    def _import_dialog(self) -> None:
        """Импортировать YAML-профиль, отметить чекбоксы правил."""
        from tkinter import filedialog, messagebox
        from ..rules import export as export_mod
        path = filedialog.askopenfilename(
            title="Import profile",
            filetypes=[("YAML", "*.yaml"), ("All", "*.*")],
        )
        if not path:
            return
        try:
            name, ids = export_mod.import_profile(Path(path))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Import failed", str(e))
            return
        # Отметить все категории
        for var in self.selected.values():
            var.set(False)
        applied = 0
        for rid in ids:
            if rid in self.selected:
                self.selected[rid].set(True)
                applied += 1
        self._set_status(f"imported '{name}': {applied}/{len(ids)} rules selected")
        messagebox.showinfo(
            "Import",
            f"Profile '{name}': {applied} rules marked.\n"
            f"Use 'Apply preset' or 'Apply selected' to apply.",
        )

    def _selected_ids(self) -> list[str]:
        return [rid for rid, var in self.selected.items() if var.get()]

    def _on_preset(self, _evt=None) -> None:
        name = self.preset_var.get()
        if not name:
            return

    def _apply_preset_selection(self) -> None:
        name = self.preset_var.get()
        preset = get_preset(name)
        if preset is None:
            return
        for var in self.selected.values():
            var.set(False)
        for rid in preset.rule_ids:
            if rid in self.selected:
                self.selected[rid].set(True)
        self._set_status(f"preset '{name}': {len(preset.rule_ids)} rules selected")

    def _on_category_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        cat = self.cat_items.get(sel[0])
        if cat:
            self._render_rules(cat)

    def _bench(self) -> dict:
        """Полный bench через core.bench.measure() — 6 метрик."""
        try:
            r = bench_mod.measure()
            return {
                "idle_ram_mb": r.idle_ram_mb,
                "total_ram_mb": r.total_ram_mb,
                "idle_cpu_pct": r.idle_cpu_pct,
                "startup_apps": r.startup_apps_count,
                "services_running": r.services_running,
                "sched_tasks_enabled": r.sched_tasks_enabled,
                "explorer_first_paint_ms": r.explorer_first_paint_ms,
                "services_by_state": dict(r.services_by_state or {}),
            }
        except Exception as e:  # noqa: BLE001
            log.warning("bench failed: %s", e)
            return {"error": str(e)}

    def _bench_before(self) -> None:
        self.bench_before = self._bench()
        if "error" in self.bench_before:
            self._set_status(f"bench error: {self.bench_before['error']}")
            return
        b = self.bench_before
        svc_str = ""
        if b.get("services_by_state"):
            svc_str = " [" + ", ".join(f"{k}={v}" for k, v in sorted(b["services_by_state"].items())) + "]"
        self._set_status(
            f"bench BEFORE: RAM {b['idle_ram_mb']}/{b['total_ram_mb']}MB, "
            f"CPU {b['idle_cpu_pct']}%, services {b['services_running']}, "
            f"tasks {b['sched_tasks_enabled']}{svc_str}"
        )

    def _bench_after(self) -> None:
        b = self._bench()
        if "error" in b:
            self._set_status(f"bench error: {b['error']}")
            return
        if self.bench_before and "error" not in self.bench_before:
            d_ram = b["idle_ram_mb"] - self.bench_before["idle_ram_mb"]
            d_svc = b["services_running"] - self.bench_before["services_running"]
            d_tasks = b["sched_tasks_enabled"] - self.bench_before["sched_tasks_enabled"]
            svc_str = ""
            if b.get("services_by_state"):
                svc_str = " [" + ", ".join(f"{k}={v}" for k, v in sorted(b["services_by_state"].items())) + "]"
            self._set_status(
                f"bench AFTER: RAM {b['idle_ram_mb']}MB (Δ{d_ram:+d}), "
                f"services {b['services_running']} (Δ{d_svc:+d}), "
                f"tasks {b['sched_tasks_enabled']} (Δ{d_tasks:+d}){svc_str}"
            )
        else:
            self._set_status(f"bench AFTER: {b}  (no baseline)")

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        log.info(msg)

    def _dry_run(self) -> None:
        from tkinter import messagebox
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Dry-run", "No rules selected")
            return
        self._apply_or_dry_run(ids, dry_run=True)

    def _apply(self) -> None:
        from tkinter import messagebox
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Apply", "No rules selected")
            return
        if not messagebox.askyesno(
            "Confirm apply",
            f"Apply {len(ids)} rule(s)?\nA restore point will be created.",
        ):
            return
        self._apply_or_dry_run(ids, dry_run=False)

    def _apply_or_dry_run(self, ids: list[str], *, dry_run: bool) -> None:
        from tkinter import messagebox
        actions = []
        for rid in ids:
            actions.extend(self.rules[rid].actions)
        total = len(actions)
        # Показываем прогресс-бар
        self.progress.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 4))
        self.progress.configure(maximum=total, value=0)
        self.root.update_idletasks()
        try:
            if dry_run:
                # dry-run: применяем по одному, обновляя прогресс
                for i, a in enumerate(actions, 1):
                    engine.apply([a], dry_run=True)
                    self.progress.configure(value=i)
                    self._set_status(f"DRY-RUN {i}/{total}: {a.describe()}")
                    self.root.update_idletasks()
                self._set_status(f"DRY-RUN: {len(ids)} rules, {total} actions")
            else:
                snap_pre = snap_mod.make_snapshot(ids, [])
                applied = []
                for i, a in enumerate(actions, 1):
                    applied.extend(engine.apply([a], dry_run=False))
                    self.progress.configure(value=i)
                    self._set_status(f"APPLY {i}/{total}: {a.describe()}")
                    self.root.update_idletasks()
                snap_obj = Snapshot(
                    id=snap_pre.id, created_at=snap_pre.created_at,
                    rules_applied=ids, actions_undone=applied,
                    restore_point_id=snap_pre.restore_point_id,
                )
                snap_mod.save(snap_obj)
                self._set_status(
                    f"APPLIED {len(applied)} actions — snapshot {snap_obj.id}"
                )
        except Exception as e:  # noqa: BLE001
            log.exception("apply failed")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress.pack_forget()

    def _open_snapshots(self) -> None:
        """Открыть окно со списком snapshot'ов."""
        from tkinter import messagebox
        win = tk.Toplevel(self.root)
        win.title("Snapshots")
        win.geometry("500x400")
        ttk.Label(win, text=f"Stored in {snap_mod._snapshots_dir()}").pack(pady=4)
        lb = tk.Listbox(win, font=("Consolas", 10))
        lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        snaps = snap_mod.list_snapshots()
        for s in snaps:
            lb.insert(tk.END, s)

        def restore():
            if not lb.curselection():
                return
            sid = lb.get(lb.curselection()[0])
            if not messagebox.askyesno("Restore", f"Rollback to {sid}?"):
                return
            try:
                snap = snap_mod.load(sid)
                engine.rollback(snap)
                self._set_status(f"rolled back {sid}")
                win.destroy()
            except Exception as e:  # noqa: BLE001
                messagebox.showerror("Error", str(e))

        ttk.Button(win, text="Restore selected", command=restore).pack(pady=4)


def _apply_dark_theme(root: tk.Tk) -> None:
    """Тёмная тема через ttk styling (без внешних зависимостей)."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:  # noqa: BLE001
        return
    bg = "#1e1e1e"
    fg = "#d4d4d4"
    accent = "#007acc"
    style.configure(".", background=bg, foreground=fg, fieldbackground="#2d2d2d")
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("TButton", background="#333333", foreground=fg)
    style.map("TButton", background=[("active", accent)])
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.map("TCheckbutton", background=[("active", bg)])
    style.configure("TCombobox", fieldbackground="#2d2d2d", background="#2d2d2d", foreground=fg)
    style.configure("Treeview", background="#252526", foreground=fg, fieldbackground="#252526")
    style.configure("TProgressbar", background=accent, troughcolor="#333333")
    root.configure(bg=bg)


def main_gui() -> int:
    root = tk.Tk()
    _apply_dark_theme(root)
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main_gui())
