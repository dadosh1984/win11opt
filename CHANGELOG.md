# Changelog

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
