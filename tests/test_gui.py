"""Tests: GUI smoke (без реального display — мокаем Tk)."""
import sys
import types

import pytest


@pytest.fixture
def fake_tk(monkeypatch):
    """Подменяем tkinter на фейк, чтобы не открывать реальное окно."""
    tk_mod = types.ModuleType("tkinter")
    ttk_mod = types.ModuleType("tkinter.ttk")

    class FakeWidget:
        def __init__(self, *a, **k):
            self.children = []
            self._vars = {}
        def pack(self, *a, **k): return None
        def pack_forget(self): return None
        def grid(self, *a, **k): return None
        def bind(self, *a, **k): return None
        def configure(self, *a, **k): return None
        def winfo_children(self): return self.children
        def destroy(self): pass
        def insert(self, *a, **k): pass
        def selection(self): return []
        def curselection(self): return ()
        def get(self, *a, **k): return ""
        def set(self, *a, **k): pass
        def create_window(self, *a, **k): pass
        def bbox(self, *a, **k): return (0, 0, 0, 0)
        def yview(self, *a, **k): pass
        def columnconfigure(self, *a, **k): pass
        def rowconfigure(self, *a, **k): pass

    class FakeTk(FakeWidget):
        def __init__(self, *a, **k):
            super().__init__()
            self.title_text = ""
        def title(self, t): self.title_text = t
        def geometry(self, g): pass
        def mainloop(self): pass
        def update_idletasks(self): pass
        def columnconfigure(self, *a, **k): pass
        def rowconfigure(self, *a, **k): pass

    class FakeVar:
        def __init__(self, *a, **k): self._v = ""
        def get(self): return self._v
        def set(self, v): self._v = v
        def trace_add(self, *a, **k): return None

    tk_mod.Tk = FakeTk
    tk_mod.Toplevel = FakeTk
    tk_mod.BooleanVar = FakeVar
    tk_mod.StringVar = FakeVar
    tk_mod.LEFT = "left"
    tk_mod.RIGHT = "right"
    tk_mod.TOP = "top"
    tk_mod.BOTTOM = "bottom"
    tk_mod.X = "x"
    tk_mod.Y = "y"
    tk_mod.BOTH = "both"
    tk_mod.END = "end"
    tk_mod.SUNKEN = "sunken"
    tk_mod.W = "w"
    tk_mod.NW = "nw"
    tk_mod.VERTICAL = "vertical"
    tk_mod.Canvas = FakeWidget
    tk_mod.Listbox = FakeWidget

    ttk_mod.Frame = FakeWidget
    ttk_mod.Label = FakeWidget
    ttk_mod.Button = FakeWidget
    ttk_mod.Checkbutton = FakeWidget
    ttk_mod.Combobox = FakeWidget
    ttk_mod.Treeview = FakeWidget
    ttk_mod.Separator = FakeWidget
    ttk_mod.Scrollbar = FakeWidget
    ttk_mod.LabelFrame = FakeWidget
    ttk_mod.Progressbar = FakeWidget
    ttk_mod.Entry = FakeWidget
    ttk_mod.Style = type("Style", (), {
        "theme_names": lambda self: [],
        "theme_use": lambda self, t: None,
        "configure": lambda self, *a, **k: None,
        "map": lambda self, *a, **k: None,
    })

    monkeypatch.setitem(sys.modules, "tkinter", tk_mod)
    monkeypatch.setitem(sys.modules, "tkinter.ttk", ttk_mod)
    filedialog_mod = types.ModuleType("tkinter.filedialog")
    filedialog_mod.asksaveasfilename = lambda **k: ""
    filedialog_mod.askopenfilename = lambda **k: ""
    monkeypatch.setitem(sys.modules, "tkinter.filedialog", filedialog_mod)
    monkeypatch.setitem(sys.modules, "tkinter.messagebox", types.ModuleType("tkinter.messagebox"))
    sys.modules["tkinter.messagebox"].showinfo = lambda *a, **k: None
    sys.modules["tkinter.messagebox"].showerror = lambda *a, **k: None
    sys.modules["tkinter.messagebox"].askyesno = lambda *a, **k: True
    return tk_mod


def test_app_constructs(fake_tk, fake_ps):
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    assert app.rules is not None
    assert len(app.rules) >= 8
    # Конструктор рендерит default категорию "visual"
    assert "visual.disable_animations" in app.selected


def test_app_render_rules(fake_tk, fake_ps):
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    assert "visual.disable_animations" in app.selected
    assert "visual.classic_context_menu" in app.selected


def test_app_selected_ids(fake_tk, fake_ps):
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    app.selected["visual.disable_animations"].set(True)
    ids = app._selected_ids()
    assert ids == ["visual.disable_animations"]


def test_app_apply_preset_selection(fake_tk, fake_ps):
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    app.preset_var.set("Balanced")
    app._apply_preset_selection()
    # Balanced включает visual.disable_animations
    assert app.selected["visual.disable_animations"].get() is True


def test_export_dialog_writes_yaml(tmp_path, fake_tk, fake_ps, monkeypatch):
    """GUI export: выбранные правила → YAML файл."""
    from tkinter import filedialog
    out = tmp_path / "gui-export.yaml"
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(out))
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    app.selected["visual.disable_animations"].set(True)
    app._export_dialog()
    assert out.exists()
    import yaml
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "visual.disable_animations" in [r["id"] for r in data["rules"]]


def test_export_dialog_no_selection(tmp_path, fake_tk, fake_ps, monkeypatch):
    """Если ничего не выбрано — messagebox.showinfo, файл не создаётся."""
    from tkinter import filedialog, messagebox
    infos = []
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: infos.append(a))
    monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **k: str(tmp_path / "x.yaml"))
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    app._export_dialog()
    assert not (tmp_path / "x.yaml").exists()
    assert infos, "showinfo should be called when no selection"


def test_import_dialog_selects_rules(tmp_path, fake_tk, fake_ps, monkeypatch):
    """GUI import: импорт помечает правила в текущей категории."""
    from tkinter import filedialog

    from win11opt.rules import export as export_mod
    from win11opt.rules import get_rules
    profile = tmp_path / "p.yaml"
    export_mod.export_profile(
        name="P", description="", rule_ids=["visual.disable_animations"],
        rules_lookup=get_rules(), out_path=profile,
    )
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(profile))
    from win11opt.gui.app import App
    root = fake_tk.Tk()
    app = App(root)
    app._render_rules("visual")
    app._import_dialog()
    assert app.selected["visual.disable_animations"].get() is True
