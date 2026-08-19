# Дизайн — v1.6.0: System Info + Safe пресет + GUI UX

## Обзор
Три изменения в существующем Python-стеке (без новых зависимостей):

1. **Новый модуль `core/sysinfo.py`** — read-only сборка OS/CPU/RAM/Disk/GPU через
   PowerShell `Get-CimInstance`. Результат — dataclass `SysInfo`. JSON-serializable.
2. **Новый пресет `rules/safe.yaml`** — 5-7 low-risk правил. Использует существующий
   loader (`PRESETS` dict), ноль изменений в engine.
3. **GUI улучшения** — collapsible группы через `ttk.LabelFrame` + `ttk.Entry` поиск,
   фильтрующий список правил по подстроке id/description.

## Модули

- `src/win11opt/core/sysinfo.py` — сбор информации о системе
- `src/win11opt/cli/main.py` — добавить `cmd_info`, subparser `info`
- `src/win11opt/gui/app.py` — collapsible + search + System Info секция
- `src/win11opt/rules/safe.yaml` — новый пресет
- `tests/test_sysinfo.py` — новые тесты

## Допущения

- Сборка через существующий `win11opt.spec` без изменений (sysinfo — обычный модуль)
- Никаких новых pip-зависимостей
- PowerShell-запросы уже изолированы в `core/ps.py` — расширим существующий паттерн
- GUI не блокирует (поиск через `StringVar.trace_add`, без thread)

## YAGNI

- Не делаем GPO-редактор (rung 7 — избыточно)
- Не делаем winget-install (rung 7 — сеть)
- Не делаем авто-обновления (rung 7)
- Не делаем HTML bench-отчёт (P2, отложен)

## Верификация

- [ ] `pytest tests/` — все зелёные
- [ ] `win11opt info` показывает OS/CPU/RAM/Disk
- [ ] `win11opt apply --profile safe --dry-run` показывает 5-7 твиков
- [ ] GUI: 52 правила отображаются, поиск фильтрует, группы сворачиваются
- [ ] EXE < 15 MB после rebuild
