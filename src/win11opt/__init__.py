"""Win11Optimizer — native single-EXE утилита для оптимизации Windows 11.

Цель: вернуть Win11 ощущение отзывчивости Windows XP за счёт отключения
тяжёлых визуальных эффектов, фоновых служб и телеметрии — без потери
совместимости.

Стек: Python 3.11+ для бизнес-логики, PowerShell для системных операций
(реестр, службы, restore point), Tkinter для GUI.
Single-EXE: PyInstaller --onefile.
"""

__version__ = "0.1.0"
__author__ = "win11opt contributors"
__license__ = "MIT"
