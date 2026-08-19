# Changelog

## v1.9.4 — Подготовка к VM-тесту (UTF-8, admin check, FileNotFoundError)

### Fixed
- **UTF-8 консоль**: EXE выводил русский текст в cp866 (мусор).
  `win11opt_entry.py` теперь ставит `SetConsoleOutputCP(65001)` +
  `sys.stdout.reconfigure(encoding="utf-8")`.
- **FileNotFoundError**: `ps.run_ps` теперь даёт понятную ошибку если
  `powershell.exe` не найден в PATH (раньше — голый traceback).
- **Admin check**: `engine.apply`/`rollback` поднимают `AdminRequiredError`
  с понятным сообщением если нет прав админа (раньше — непонятный
  Access Denied от PowerShell).

### Added
- `engine._is_admin()` + `engine.AdminRequiredError`.
- `tests/test_ps.py`: FileNotFoundError + is_admin.
- `tests/test_engine.py`: admin check (apply/rollback/dry-run).

### Tests
- 119/119 passed (было 114; +5 admin/FileNotFoundError).
- `ruff check`: 0 ошибок.

## v1.9.3 — Bugfixes (ruff + найденные баги)

### Fixed
- **snapshot.py:48** — NameError при `snapshot.load()`: использовался
  `ActionKind` без импорта. Модуль вообще не имел тестов. Добавлен
  `tests/test_snapshot.py` (4 теста, round-trip всех ActionKind).
- **ps.py:230** — `sched_task_enable` был мёртвым кодом (script собирался
  но `run_ps` не вызывался). **Критический баг rollback**: отключённые
  scheduled tasks не включались обратно. Добавлен `tests/test_ps.py`
  (2 теста — disable и enable вызывают `run_ps`).
- i18n.py: распаковка `version` → `_` (unused).

### Changed
- pyproject.toml: ruff ignore для намеренных паттернов
  (PLW1510 subprocess без check, BLE001 blind except, DTZ005 naive datetime).
- ruff --fix: 59 авто-фиксов (unused imports, multi-line import style).

### Tests
- 114/114 passed (было 108; +6: 4 snapshot + 2 ps).
- `ruff check`: 0 ошибок.

## v1.9.2 — `import` теперь устанавливает профиль

### Changed
- `win11opt import profile.yaml` по умолчанию копирует файл в `rules/`
  и печатает подсказку `use: win11opt apply --profile <name>`.
  Раньше только валидировал и требовал ручного копирования.
- Добавлен `--validate-only` — проверить файл без копирования.

### Added
- `rules/export.py::install_profile()` — копирует профиль в `dest_dir`
  (по умолчанию `DEFAULT_RULES_DIR`).

### Tests
- 108/108 passed (было 104; +4 install/validate-only)

## Unreleased — CI/CD

### Added
- GitHub Actions: авто-тесты (ubuntu + windows) на push/PR
- GitHub Actions: сборка EXE + авто-release на тег `v*`
- Отслеживание `win11opt.spec` (исключение в .gitignore) для воспроизводимых сборок

## v1.9.1 — GUI export/import

### Added
- GUI: кнопки "Export…" и "Import…" в top bar (filedialog + валидация)
- GUI export: выбранные чекбоксы → YAML-профиль
- GUI import: YAML-профиль → отмечает чекбоксы правил
- Lazy import messagebox (fix: тесты пересоздают мок-модуль)

### Tests
- 104/104 passed (было 101; +3 GUI export/import)

## v1.9.0 — Export/Import custom профилей

### Added
- `rules/export.py` — сериализация custom-профиля в YAML (тот же формат, что rules/*.yaml)
- `win11opt export --name N --rules R1,R2 --out P.yaml` — создать custom-профиль
- `win11opt import P.yaml` — загрузить и валидировать профиль (напечатать name + rule_ids)
- Round-trip: export → import даёт идентичные rule_ids (тест)

### Tests
- 101/101 passed (было 92; +9 export/import)

## v1.8.0 — Gaming пресет

### Added
- Пресет `Gaming` — 6 геймер-ориентированных low-risk правил: Game Bar/DVR off, Ultimate Performance, отключение Xbox-фон-сервисов и задач планировщика. Не удаляет Xbox Game Pass.

### Tests
- 92/92 passed (было 91; +1 Gaming preset)

## v1.7.0 — HTML bench diff report + GUI services_by_state

### Added
- `core/bench_html.py` — stdlib-only HTML renderer (no jinja2, single-EXE safe)
- `bench diff --html PATH` — флаг для сохранения HTML-отчёта (в дополнение к `--out` для JSON)
- HTML-страница: таблица метрик с CSS-классами good/bad/zero + блок services_by_state

### Changed
- GUI: status bar в `_bench_before/_bench_after` показывает `services_by_state` (был orphaned field)

### Tests
- 91/91 passed (было 83; +8 HTML renderer)

## v1.6.0 — System Info + Safe пресет + GUI search

### Added
- `win11opt info` — read-only снимок системы (OS/CPU/RAM/Disk/GPU/uptime), `--json` флаг
- Пресет `Safe` — 7 low-risk правил, рекомендованная точка входа для новичков
- GUI: поиск по id/description + кнопка "System Info" (окно с refresh)
- `core/sysinfo.py` — модуль сбора информации (PowerShell Get-CimInstance)

### Changed
- GUI: search bar над списком правил (фильтр по подстроке)

### Tests
- 83/83 passed (было 75; +8: sysinfo collect/parse/format, safe preset)

## v1.5.0 — Bench: services-by-state + JSON diff-report

### Added
- `bench.services_by_state` — разбивка служб по состоянию (Running/Stopped/Disabled/...)
- `bench diff --out PATH` — сохранение diff-отчёта до/после в JSON
- `bench report [PATH]` — печать diff-отчёта в human-readable (по умолчанию — последний)
- API: `bench.diff_report(a, b)` и `bench.save_diff_report(a, b, path=None)`

### Changed
- Удалена неактуальная спека `single_exe_uac_elevated_native_gui_elect/` (drift с Python)
- README: обновлена секция bench (новые метрики + команда `bench report`)

### Tests
- 75/75 passed (было 72; +3: services_by_state в measure, diff_report round-trip, services_by_state в deltas)

## v1.4.0 — i18n (English + Russian через .po/.mo)

## v1.3.0 — GUI (progress bar, full bench, dark theme)

## v1.2.0 — ms_doc_url для всех 52 правил

## v1.1.0 — Bench save/diff (измеримое подтверждение эффекта)

## v1.0.0 — Scheduled Tasks + Storage + AppCompat (+13 фишек)
