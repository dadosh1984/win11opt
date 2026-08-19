# Result — программу-оптимизации-windows-11

- **Status:** INCOMPLETE
- **Tasks:** 50/52 done
**Guard:** lint:SKIP, type:FAIL, test:SKIP, drift:PASS, yagni:SKIP, economy:PASS, security:PASS, policy:PASS, verifiability:WARN
- **Budget:** compact
- **Constraints:** compact
- **Generated:** 2026-08-19T14:10:28.936Z

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
- [x] [assumption] YAML rule loader: rules/*.yaml + валидация + `rules validate`
- [x] [fact] Integrate with the dry-run по умолчанию в CLI, snapshot перед apply, restore point через Checkpoint-Computer
- [x] [assumption] Undo log: capture undo для каждого действия
- [x] [assumption] CLI: `apply --profile/--rule [--dry-run]`
- [x] [assumption] CLI: `snapshot create/list/restore`
- [x] [assumption] CLI: `rules list/describe <id>`
- [x] [assumption] CLI: `bench` (базовый: startup apps, services count)
- [x] [assumption] Bench: list_startup_apps (autoruns-like)
- [x] [assumption] Bench: services count by state — services_by_state (Running/Stopped/Disabled/...)
- [x] [assumption] Bench: JSON отчёт до/после — diff_report() + save_diff_report() + `--out PATH`
- [x] [assumption] Tkinter GUI: категории слева, тумблеры справа, пресеты, dry-run/apply, snapshots, bench до/после
- [x] [assumption] README: install, usage, profiles, rollback
- [x] [assumption] LICENSE: MIT
- [x] [assumption] Verify: `pytest tests/` зелёные
- [x] PyInstaller single-EXE: `dist/win11opt.exe` 12 MB
- [x] UAC manifest: `requireAdministrator` встроен в EXE
- [x] YAML пресеты: `rules/*.yaml`, loader, валидация, `rules validate`
- [x] Tkinter GUI: `win11opt gui`
- [x] Новые правила v0.4: ui (3), gaming (2), onedrive (2)
- [x] Новые правила v0.5: explorer (4), debloat (4) + appx_remove в engine
- [x] Новые правила v0.6: defender (3), update (4). Hardened пресет.
- [x] Новые правила v0.7: гибернация (powercfg -h off), телеметрия CEIP/Activity/Tailored. Фикс POWER_PLAN в engine.
- [x] Новые правила v0.8: network (3), ntfs (3). Aggressive +4 правила.
- [x] Новые правила v1.0: scheduled_tasks (3 пакета, 13 задач), storage (3), appcompat (4). Итого 52 правила.
- [x] Bench v1.1: save/diff/list, 6 метрик (RAM, CPU, startup, services, tasks, explorer paint).
- [x] ms_doc_url v1.2: 42 правила дополнены ссылками на learn.microsoft.com, тест на полноту.
- [x] Git: v1.1.0 commit + tag
- [x] Git: v1.0.0 commit + tag
- [x] Git: v0.8.0 commit + tag
- [x] Git: v0.7.0 commit + tag
- [x] Git: v0.6.0 commit + tag
- [x] Git: v0.5.0 commit + tag
- [x] Преcет Debloat
- [x] Git: v0.4.0 commit + tag
- [ ] Подпись бинаря
- [ ] Тесты на реальной Win11 VM (snapshot/restore round-trip)

## Guard report

| Step | Status | Detail |
|------|--------|--------|
| lint | SKIP | no lint script in package.json |
| type | FAIL | Command failed: npm exec tsc --noEmit
npm warn Unknown cli config "--noEmit". This will stop working in the next major version of npm.
 |
| test | SKIP | no test script in package.json |
| drift | PASS | no capabilities in specs |
| yagni | SKIP | no existing .ts sources to build a baseline from |
| economy | PASS | cache 278.0 KB of 100.0 MB (703 entries) — within budget; ≈ 1463963 tok saved across 828 compress op(s) |
| security | PASS | no obvious issues |
| policy | PASS | no .orion/policy.json — no project gates to enforce |
| verifiability | WARN | oracles: none · verifiability level 0 · tests weak/missing — low verifiability: treat this PASS as lower-confidence (human review advised) |

## Artifacts

- `changes/программу-оптимизации-windows-11/proposal.md`
- `changes/программу-оптимизации-windows-11/design.md`
- `changes/программу-оптимизации-windows-11/tasks.md`
- `changes/программу-оптимизации-windows-11/forge-report.md`
- `reports/программу-оптимизации-windows-11/guard-report.md`
- `changes/программу-оптимизации-windows-11/snippets/`

## Next steps

Run `orion shield программу-оптимизации-windows-11` to get a guard verdict.
