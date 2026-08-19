# Forge Report — программу-оптимизации-windows-11

- **Status:** paused
- **Done:** 0 · **Skipped (cache):** 0 · **Pending:** 31
- **Generated:** 2026-08-19T09:50:14.383Z

| Task | Status |
|------|--------|
| [assumption] Scaffold .NET solution: Win11Optimizer.Core, .Rules, .Bench, .CLI, .App + tests | pending |
| [fact] Integrate with the C# .NET 8 + WPF, single EXE via PublishSingleFile, Win11 22H2+ | pending |
| [assumption] Add NuGet deps: YamlDotNet, System.CommandLine, xUnit | pending |
| [assumption] Rule model: `Tweak` (id, name, category, risk, reg/svc/scheduled actions, undo map) | pending |
| [assumption] RuleSet loader: parse YAML → validate → immutable list | pending |
| [assumption] Snapshot service: capture touched registry keys + services (reg export + sc query) → .json | pending |
| [assumption] Apply service: dry-run/apply/rollback, idempotent, transactional per-tweak | pending |
| [assumption] Built-in presets: Aggressive, Balanced, Privacy, Gaming, Restore | pending |
| [assumption] YAML rule: визуал — отключить анимации/тени/Mica (`HKCU\...\Desktop\WindowMetrics`, Themes) | pending |
| [assumption] YAML rule: классическое контекст-меню (`HKCU\Software\...\Explorer\Advanced\HideFileExt`-related) | pending |
| [assumption] YAML rule: службы — SysMain, DiagTrack, SearchIndexer, Xbox, Biometric, PhoneLink → Manual/Disabled | pending |
| [assumption] YAML rule: телеметрия — диагностика=0, рекламный ID, Activity History | pending |
| [assumption] YAML rule: питание — Ultimate Performance plan, Game Bar/DVR off | pending |
| [assumption] YAML rule: реестр — UAC ConsentPromptBehaviorAdmin, lock screen, CAD | pending |
| [fact] Integrate with the Обязательно: dry-run, snapshot, rollback, точка восстановления Win11 22H2+ | pending |
| [assumption] Restore point: PowerShell `Checkpoint-Computer` перед apply | pending |
| [assumption] Undo log: каждое изменение → undo-action → применяется в обратном порядке при rollback | pending |
| [assumption] CLI: `apply --profile <name> [--dry-run] [--no-restore-point]` | pending |
| [assumption] CLI: `snapshot create|list|restore` | pending |
| [assumption] CLI: `rules list|describe <id>|validate` | pending |
| [assumption] Bench: idle RAM (WMI Win32_OperatingSystem + GC) | pending |
| [assumption] Bench: startup apps count (autoruns-like enumeration) | pending |
| [assumption] Bench: services count by state | pending |
| [assumption] Bench: write JSON report before/after | pending |
| [assumption] WPF main window: category tree (left) + tweaks list (right) + dry-run/apply bar | pending |
| [assumption] Profile selector dropdown | pending |
| [assumption] Bench before/after panel (numbers + JSON save) | pending |
| [assumption] Undo button → restore snapshot | pending |
| [assumption] README: install, usage, profiles, rollback, contributing rules | pending |
| [assumption] LICENSE: MIT | pending |
| [assumption] Verify: `dotnet build -c Release` без warnings-as-errors, `dotnet test` зелёные, single EXE < 30 MB | pending |

Waiting for implementation snippets:
- `changes/программу-оптимизации-windows-11/snippets/scaffold_net_solution.ts`
- `changes/программу-оптимизации-windows-11/snippets/integrate_c_net.ts`
- `changes/программу-оптимизации-windows-11/snippets/add_nuget_deps.ts`
- `changes/программу-оптимизации-windows-11/snippets/rule_model_tweak.ts`
- `changes/программу-оптимизации-windows-11/snippets/ruleset_loader_parse.ts`
- `changes/программу-оптимизации-windows-11/snippets/snapshot_service_capture.ts`
- `changes/программу-оптимизации-windows-11/snippets/apply_service_dry.ts`
- `changes/программу-оптимизации-windows-11/snippets/built_presets_aggressive.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_визуал.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_классическое.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_службы.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_телеметрия.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_питание.ts`
- `changes/программу-оптимизации-windows-11/snippets/yaml_rule_реестр.ts`
- `changes/программу-оптимизации-windows-11/snippets/integrate_обязательно_dry.ts`
- `changes/программу-оптимизации-windows-11/snippets/restore_point_powershell.ts`
- `changes/программу-оптимизации-windows-11/snippets/undo_log_каждое.ts`
- `changes/программу-оптимизации-windows-11/snippets/cli_apply_profile.ts`
- `changes/программу-оптимизации-windows-11/snippets/cli_snapshot_create.ts`
- `changes/программу-оптимизации-windows-11/snippets/cli_rules_list.ts`
- `changes/программу-оптимизации-windows-11/snippets/bench_idle_ram.ts`
- `changes/программу-оптимизации-windows-11/snippets/bench_startup_apps.ts`
- `changes/программу-оптимизации-windows-11/snippets/bench_services_count.ts`
- `changes/программу-оптимизации-windows-11/snippets/bench_write_json.ts`
- `changes/программу-оптимизации-windows-11/snippets/wpf_main_window.ts`
- `changes/программу-оптимизации-windows-11/snippets/profile_selector_dropdown.ts`
- `changes/программу-оптимизации-windows-11/snippets/bench_before_after.ts`
- `changes/программу-оптимизации-windows-11/snippets/undo_button_restore.ts`
- `changes/программу-оптимизации-windows-11/snippets/readme_install_usage.ts`
- `changes/программу-оптимизации-windows-11/snippets/license_mit.ts`
- `changes/программу-оптимизации-windows-11/snippets/verify_dotnet_build.ts`
