"""i18n wrapper around gettext.

Usage:
    from win11opt.i18n import _, set_language
    set_language("ru")  # or None to autodetect from system
    print(_("Apply"))  # "Применить"

Locale files live in `<project_root>/locale/<lang>/LC_MESSAGES/win11opt.{po,mo}`.
Default language is English (no translation file needed).
"""
from __future__ import annotations

import locale
import os
import sys
from pathlib import Path

# ponytail: rung 1 — built-in gettext, zero external deps.

_DOMAIN = "win11opt"
_LOCALE_DIRNAME = "locale"
_DEFAULT_LANG = "en"


def _find_locale_dir() -> Path | None:
    """Find locale dir in dev tree or next to frozen EXE."""
    candidates = []
    # 1. Env override
    env = os.environ.get("WIN11OPT_LOCALE_DIR")
    if env:
        candidates.append(Path(env))
    # 2. Dev tree: project_root/locale
    here = Path(__file__).resolve()
    candidates.append(here.parent.parent.parent / _LOCALE_DIRNAME)
    # 3. Frozen EXE: _MEIPASS/locale
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / _LOCALE_DIRNAME)
    # 4. Next to EXE: <exe_dir>/locale
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / _LOCALE_DIRNAME)
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _load_mo(path: Path) -> dict[str, str]:
    """Parse .mo file (singular-only) and return {msgid: msgstr} dict."""
    import struct
    if not path.exists():
        return {}
    data = path.read_bytes()
    if len(data) < 20:
        return {}
    magic = struct.unpack("<I", data[:4])[0]
    if magic == 0x950412DE:
        endian = "<"
    elif magic == 0xDE120495:
        endian = ">"
    else:
        return {}
    _, n, off1, off2 = struct.unpack(f"{endian}4I", data[4:20])
    result: dict[str, str] = {}
    for i in range(n):
        id_off, id_len = struct.unpack(f"{endian}2I", data[off1 + i*8:off1 + i*8 + 8])
        str_off, str_len = struct.unpack(f"{endian}2I", data[off2 + i*8:off2 + i*8 + 8])
        msgid = data[id_off:id_off + id_len].decode("utf-8", errors="replace").rstrip("\x00")
        msgstr = data[str_off:str_off + str_len].decode("utf-8", errors="replace").rstrip("\x00")
        if msgstr:
            result[msgid] = msgstr
    return result


def detect_system_language() -> str:
    """Detect OS language, fallback to 'en'.

    ponytail: rung 1 — stdlib only, no external locale lib.
    """
    try:
        # Python 3.11+: locale.getlocale() instead of deprecated getdefaultlocale()
        loc = locale.getlocale()[0] or os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
        if loc and loc.lower().startswith("ru"):
            return "ru"
    except Exception:  # noqa: S110
        pass
    return _DEFAULT_LANG


_translation: dict[str, str] = {}
_current_lang: str = _DEFAULT_LANG


def set_language(lang: str | None = None) -> str:
    """Activate translation. Returns the language actually activated."""
    global _translation, _current_lang
    if not lang:
        lang = _DEFAULT_LANG
    if lang == _DEFAULT_LANG:
        _translation = {}
        _current_lang = _DEFAULT_LANG
        return _current_lang
    ldir = _find_locale_dir()
    if ldir is not None:
        mo = ldir / lang / "LC_MESSAGES" / f"{_DOMAIN}.mo"
        if mo.exists():
            _translation = _load_mo(mo)
            _current_lang = lang
        else:
            _translation = {}
            _current_lang = _DEFAULT_LANG
    else:
        _translation = {}
        _current_lang = _DEFAULT_LANG
    return _current_lang


def get_language() -> str:
    return _current_lang


def _(message: str) -> str:
    """Translate a message."""
    return _translation.get(message, message)


def N_(message: str) -> str:
    """Mark a string for translation without translating (use in module-level constants)."""
    return message


# Auto-init at import time
auto_lang = detect_system_language()
set_language(auto_lang)