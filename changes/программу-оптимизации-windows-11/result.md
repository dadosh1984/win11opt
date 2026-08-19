# Result — программу-оптимизации-windows-11

- **Status:** INCOMPLETE
- **Tasks:** 26/36 done
**Guard:** no guard report
- **Budget:** compact
- **Constraints:** compact
- **Generated:** 2026-08-19T10:07:43.481Z

## Checklist

- [x] [assumption] Scaffold project structure (Python пакет `win11opt/` + tests/)
- [x] [fact] Integrate with the Python 3.11+, PowerShell для system ops, single EXE через PyInstaller
- [x] [assumption] pyproject.toml + pip install -e
- [x] [assumption] Domain models: Action, ActionKind, Risk, Rule, Profile, Snapshot, Result
- [x] [assumption] PowerShell executor: reg_get/reg_set/reg_delete, service_set_state, create_restore_point, list_startup_apps
- [x] [assumption] Apply engine: dry-run, apply, rollback (round-trip через Snapshot)
- [x] [assumption] Snapshot persistence: JSON в %LOCALAPPDATA%\win11opt\snapshots\
- [x] [assumption] Rule: visual.disable_animations
- [x] [assumption] Rule: visual.classic_context_menu
- [x] [assumption] Rule: services.disable_search_indexer
- [x] [assumption] Rule: services.disable_diagtrack
- [x] [assumption] Rule: services.disable_xbox
- [x] [assumption] Rule: telemetry.advertising_id
- [x] [assumption] Rule: power.ultimate_performance
- [x] [assumption] Rule: registry.uac_no_delay
- [x] [assumption] Presets: Balanced, Aggressive, Privacy
- [ ] [assumption] YAML rule loader (YamlDotNet → PyYAML) — отложено в v0.2
- [x] [fact] Integrate with the dry-run по умолчанию в CLI, snapshot перед apply, restore point через Checkpoint-Computer
- [x] [assumption] Undo log: capture undo для каждого действия
- [x] [assumption] CLI: `apply --profile/--rule [--dry-run]`
- [x] [assumption] CLI: `snapshot create/list/restore`
- [x] [assumption] CLI: `rules list/describe <id>`
- [x] [assumption] CLI: `bench` (базовый: startup apps, services count)
- [x] [assumption] Bench: list_startup_apps (autoruns-like)
- [ ] [assumption] Bench: services count by state — отложено
- [ ] [assumption] Bench: JSON отчёт до/после — отложено
- [ ] [assumption] Tkinter GUI — отложено в v0.2
- [x] [assumption] README: install, usage, profiles, rollback
- [x] [assumption] LICENSE: MIT
- [x] [assumption] Verify: `pytest tests/` зелёные
- [ ] YAML пресеты
- [ ] PyInstaller single-EXE
- [ ] Tkinter GUI
- [ ] UAC manifest
- [ ] Подпись бинаря
- [ ] Тесты на реальной Win11 VM (snapshot/restore round-trip)

## Artifacts

- `changes/программу-оптимизации-windows-11/proposal.md`
- `changes/программу-оптимизации-windows-11/design.md`
- `changes/программу-оптимизации-windows-11/tasks.md`
- `changes/программу-оптимизации-windows-11/forge-report.md`
- `changes/программу-оптимизации-windows-11/specs/single_exe_uac_elevated_native_gui_elect/spec.md`
- `changes/программу-оптимизации-windows-11/snippets/`

## Next steps

Run `orion shield программу-оптимизации-windows-11` to get a guard verdict.
