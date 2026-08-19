# Задачи — программу-оптимизации-windows-11

Легенда: `[x]` — готово, `[ ]` — открыто.

**Стек:** Python 3.11+ (CLI + бизнес-логика) + PowerShell 5.x (реестр, службы, restore point) + Tkinter (GUI отложен). Single-EXE через PyInstaller.

## Фаза 0 — каркас ✅

- [x] [assumption] Scaffold project structure (Python пакет `win11opt/` + tests/)
- [x] [fact] Integrate with the Python 3.11+, PowerShell для system ops, single EXE через PyInstaller
- [x] [assumption] pyproject.toml + pip install -e

## Фаза 1 — ядро (Core)

- [x] [assumption] Domain models: Action, ActionKind, Risk, Rule, Profile, Snapshot, Result
- [x] [assumption] PowerShell executor: reg_get/reg_set/reg_delete, service_set_state, create_restore_point, list_startup_apps
- [x] [assumption] Apply engine: dry-run, apply, rollback (round-trip через Snapshot)
- [x] [assumption] Snapshot persistence: JSON в %LOCALAPPDATA%\win11opt\snapshots\

## Фаза 2 — правила (Rules)

- [x] [assumption] Rule: visual.disable_animations
- [x] [assumption] Rule: visual.classic_context_menu
- [x] [assumption] Rule: services.disable_search_indexer
- [x] [assumption] Rule: services.disable_diagtrack
- [x] [assumption] Rule: services.disable_xbox
- [x] [assumption] Rule: telemetry.advertising_id
- [x] [assumption] Rule: power.ultimate_performance
- [x] [assumption] Rule: registry.uac_no_delay
- [x] [assumption] Presets: Balanced, Aggressive, Privacy
- [x] [assumption] YAML rule loader: rules/*.yaml + валидация + `rules validate`

## Фаза 3 — безопасность операций

- [x] [fact] Integrate with the dry-run по умолчанию в CLI, snapshot перед apply, restore point через Checkpoint-Computer
- [x] [assumption] Undo log: capture undo для каждого действия

## Фаза 4 — CLI

- [x] [assumption] CLI: `apply --profile/--rule [--dry-run]`
- [x] [assumption] CLI: `snapshot create/list/restore`
- [x] [assumption] CLI: `rules list/describe <id>`
- [x] [assumption] CLI: `bench` (базовый: startup apps, services count)

## Фаза 5 — бенчмарк (Bench)

- [x] [assumption] Bench: list_startup_apps (autoruns-like)
- [ ] [assumption] Bench: services count by state — отложено
- [ ] [assumption] Bench: JSON отчёт до/после — отложено

## Фаза 6 — GUI (App)

- [x] [assumption] Tkinter GUI: категории слева, тумблеры справа, пресеты, dry-run/apply, snapshots, bench до/после

## Фаза 7 — выпуск

- [x] [assumption] README: install, usage, profiles, rollback
- [x] [assumption] LICENSE: MIT
- [x] [assumption] Verify: `pytest tests/` зелёные

## Фаза 8 — следующие шаги

- [x] PyInstaller single-EXE: `dist/win11opt.exe` 12 MB
- [x] UAC manifest: `requireAdministrator` встроен в EXE
- [x] YAML пресеты: `rules/*.yaml`, loader, валидация, `rules validate`
- [x] Tkinter GUI: `win11opt gui`
- [x] Новые правила v0.4: ui (3), gaming (2), onedrive (2)
- [x] Новые правила v0.5: explorer (4), debloat (4) + appx_remove в engine
- [x] Новые правила v0.6: defender (3), update (4). Hardened пресет.
- [x] Новые правила v0.7: гибернация (powercfg -h off), телеметрия CEIP/Activity/Tailored. Фикс POWER_PLAN в engine.
- [x] Новые правила v0.8: network (3), ntfs (3). Aggressive +4 правила.
- [x] Git: v0.7.0 commit + tag
- [x] Git: v0.6.0 commit + tag
- [x] Git: v0.5.0 commit + tag
- [x] Преcет Debloat
- [x] Git: v0.4.0 commit + tag
- [ ] Подпись бинаря
- [ ] Тесты на реальной Win11 VM (snapshot/restore round-trip)
