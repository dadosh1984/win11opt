"""Entry script for PyInstaller --onefile build."""
import sys


def _setup_utf8_console() -> None:
    """UTF-8 для консоли Windows (EXE без этого выводит cp866/cp1252)."""
    if sys.platform != "win32":
        return
    # 1. PyInstaller bootloader не всегда читает manifest — ставим кодовую страницу.
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # CP_UTF8
    except Exception:  # noqa: S110
        pass
    # 2. Перенастраиваем stdout/stderr на UTF-8 (Python 3.7+).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: S110
            pass


_setup_utf8_console()

from win11opt.cli import main

if __name__ == "__main__":
    sys.exit(main())
