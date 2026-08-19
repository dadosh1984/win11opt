# Задачи — v1.6.0: P0 + P1 фичи

## Фаза 1 — System Info дашборд (P0)

- [x] `core/sysinfo.py` — собирает OS/CPU/RAM/Disk/GPU через PowerShell+CIM, чистое чтение
- [x] `cli/main.py` — команда `win11opt info` (text + `--json` флаг)
- [x] `rules/loader.py` — `format_sysinfo(result)` для GUI/print
- [x] Тесты `tests/test_sysinfo.py`: мок CIM-ответов, JSON round-trip, обработка пустых полей
- [x] GUI `gui/app.py`: новая вкладка/секция "System Info" с auto-refresh
- [x] i18n: переводы `_("System Information")` и др. в `locale/ru/LC_MESSAGES/`
- [x] README: раздел "Просмотр системы"

## Фаза 2 — Quick Safe пресет (P0)

- [x] `rules/safe.yaml` — 5-7 безопасных правил (low risk, заметный эффект)
- [x] `rules/__init__.py` — добавить `safe` в `PRESETS`
- [x] Тест `tests/test_loader.py::test_safe_preset_exists_and_low_risk` — валидация safe.yaml
- [x] README: описать safe как "рекомендованная точка входа"
- [x] GUI: в combobox пресетов добавить "Quick Safe"

## Фаза 3 — GUI улучшения (P1)

- [x] `gui/app.py`: collapsible группы (ttk.LabelFrame или кастомный виджет)
- [x] `gui/app.py`: search Entry над списком правил, фильтрует по id+description
- [x] Тест `tests/test_gui.py`: smoke-test создания окна с 52 правилами
- [x] README: упомянуть поиск

## Фаза 4 — релиз v1.6.0

- [x] CHANGELOG.md: добавить секцию v1.6.0
- [x] Bump version 1.5.0 → 1.6.0 в `__init__.py` + `pyproject.toml`
- [x] Rebuild EXE, тег v1.6.0

## Фаза 5 — отложено (P2, не в v1.6.0)

- [ ] HTML bench-отчёт (P2)
- [ ] GUI: показывать `services_by_state` (P2)

## Verify

- [ ] `pytest tests/` — все зелёные (должно быть ≥ 80 тестов после добавления)
- [ ] `win11opt info --help` — работает
- [ ] `win11opt apply --profile safe --dry-run` — показывает дифф
- [ ] GUI запускается и показывает System Info + правила с поиском
