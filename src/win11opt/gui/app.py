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
from tkinter import messagebox, ttk

from .. import __version__
from ..core import engine, ps, snapshot as snap_mod
from ..core.models import Snapshot
from ..rules import PRESETS, get_preset, get_rules

log = logging.getLogger(__name__)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"Win11Optimizer {__version__}")
        self.root.geometry("900x600")
        self.rules = get_rules()
        self.selected: dict[str, tk.BooleanVar] = {}
        self.bench_before: dict | None = None
        self._build()

    def _build(self) -> None:
        # Top bar: preset + bench
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(top, text="Preset:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        cb = ttk.Combobox(
            top, textvariable=self.preset_var, state="readonly", width=20,
            values=[p.name for p in PRESETS],
        )
        cb.pack(side=tk.LEFT, padx=4)
        cb.bind("<<ComboboxSelected>>", self._on_preset)
        ttk.Button(top, text="Apply preset", command=self._apply_preset_selection).pack(side=tk.LEFT, padx=4)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(top, text="Bench before", command=self._bench_before).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Bench after", command=self._bench_after).pack(side=tk.LEFT, padx=4)

        # Body: categories | rules
        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Categories tree (left)
        cats_frame = ttk.LabelFrame(body, text="Categories")
        cats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.tree = ttk.Treeview(cats_frame, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_category_select)
        self.cat_items: dict[str, str] = {}
        for cat in sorted({r.category for r in self.rules.values()}):
            iid = self.tree.insert("", tk.END, text=cat)
            self.cat_items[iid] = cat

        # Rules list (right)
        rules_frame = ttk.LabelFrame(body, text="Rules")
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
        ttk.Button(bottom, text="Dry-run selected", command=self._dry_run).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom, text="Apply selected", command=self._apply).pack(side=tk.LEFT, padx=4)
        ttk.Separator(bottom, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(bottom, text="Snapshots…", command=self._open_snapshots).pack(side=tk.LEFT, padx=4)

        # Status bar
        self.status_var = tk.StringVar(value=f"idle — {len(self.rules)} rules loaded")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )

    def _render_rules(self, category: str) -> None:
        for w in self.rules_inner.winfo_children():
            w.destroy()
        self.selected.clear()
        for rid in sorted(r for r, rule in self.rules.items() if rule.category == category):
            rule = self.rules[rid]
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
        startup = ps.list_startup_apps()
        return {"startup_apps": len(startup), "rules_loaded": len(self.rules)}

    def _bench_before(self) -> None:
        self.bench_before = self._bench()
        self._set_status(f"bench BEFORE: {self.bench_before}")

    def _bench_after(self) -> None:
        b = self._bench()
        if self.bench_before:
            d_startup = b["startup_apps"] - self.bench_before["startup_apps"]
            self._set_status(f"bench AFTER: {b}  Δ startup={d_startup:+d}")
        else:
            self._set_status(f"bench AFTER: {b}  (no baseline)")

    def _set_status(self, msg: str) -> None:
        self.status_var.set(msg)
        log.info(msg)

    def _dry_run(self) -> None:
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Dry-run", "No rules selected")
            return
        self._apply_or_dry_run(ids, dry_run=True)

    def _apply(self) -> None:
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
        actions = []
        for rid in ids:
            actions.extend(self.rules[rid].actions)
        try:
            if dry_run:
                engine.apply(actions, dry_run=True)
                self._set_status(f"DRY-RUN: {len(ids)} rules, {len(actions)} actions")
            else:
                snap_pre = snap_mod.make_snapshot(ids, [])
                applied = engine.apply(actions, dry_run=False)
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

    def _open_snapshots(self) -> None:
        """Открыть окно со списком snapshot'ов."""
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


def main_gui() -> int:
    root = tk.Tk()
    try:
        # Попытка применить тему (если есть ttkthemes — нет, но вдруг)
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:  # noqa: BLE001
        pass
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main_gui())
