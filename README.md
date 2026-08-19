# Win11Optimizer

Native single-EXE утилита для оптимизации Windows 11 — чтобы система
ощущалась такой же отзывчивой, как Windows XP.

## Что делает

Отключает тяжёлые визуальные эффекты, фоновые службы и телеметрию,
которые мешают интерактивной отзывчивости UI. Не удаляет компоненты
системы (кроме явных случаев), всё обратимо через snapshot + restore.

## Стек

- Python 3.11+
- PowerShell 5.x (встроен в Windows) для реестра, служб, restore point
- PyInstaller для сборки single-EXE

## Установка (разработка)

```bash
git clone <repo>
cd win11-optimizer
pip install -e ".[dev]"
pytest
```

## Использование

```bash
# Список всех правил и пресетов
win11opt rules list

# Описание конкретного правила
win11opt rules describe visual.disable_animations

# Валидировать все YAML-пресеты в rules/
win11opt rules validate

# Применить пресет (dry-run, ничего не меняет)
win11opt apply --profile Balanced --dry-run

# Реально применить (попросит UAC)
win11opt apply --profile Balanced

# Список snapshot'ов
win11opt snapshot list

# Откатить к snapshot
win11opt snapshot restore 20250101-120000

# Бенчмарк (стартовая точка)
win11opt bench

# Графический интерфейс
win11opt gui
```

## Пресеты

| Имя | Что делает |
|---|---|
| **Balanced** | Безопасный: анимации, UI (мгновенные меню/тултипы), Explorer, телеметрия, питание |
| **Aggressive** | Максимум отзывчивости, отключает службы + Game Bar + OneDrive |
| **Privacy** | Только телеметрия/реклама, отключает Cortana |
| **Debloat** | Удаление UWP-приложений (Xbox, Bing, GetHelp). Необратимо. |
| **Hardened** | Продвинутый: ослабление Defender Cloud + отложенные Update. **НЕ удаляет Defender/Edge.** |

## Категории правил

- **visual** — анимации, классическое контекстное меню
- **ui** — мгновенные меню/тултипы, lockscreen, Cortana
- **explorer** — показ расширений, полный путь, статусбар, запуск в This PC
- **services** — Windows Search, DiagTrack, Xbox-сервисы
- **gaming** — Xbox Game Bar, Win+G hotkey
- **onedrive** — отключение синхронизации/автозапуска
- **debloat** — удаление UWP-приложений (Xbox/Bing/Help/дубли)
- **defender** — ослабление Cloud/SmartScreen/MpTelemetry (НЕ удаляет!)
- **update** — отложенные feature/quality updates
- **telemetry** — рекламный ID
- **power** — Ultimate Performance
- **registry** — UAC no-delay

## ⚠️ Что НЕ делает эта утилита

- **Не удаляет Microsoft Defender.** Он — часть ядра Win11. Удаление = BSOD.
  Твики только ослабляют телеметрию/SmartScreen, real-time защита остаётся.
- **Не удаляет Microsoft Edge.** WebView2 (на нём работают Calculator, Notepad,
  Paint, Settings) требует Edge. Удаление сломает ОС.
- **Не отключает Windows Update полностью.** Только откладывает feature updates
  на 12 мес и quality updates на 7 дней. Безопасность системы сохраняется.

## Расширение через YAML

Правила живут в `rules/*.yaml`. Формат:

```yaml
name: visual
description: Визуальные оптимизации.
rules:
  - id: visual.disable_animations
    name: Отключить анимации окон
    risk: low
    ms_doc_url: https://learn.microsoft.com/...
    actions:
      - kind: reg_set
        target: 'HKCU:\Control Panel\Desktop\WindowMetrics'
        name: MinAnimate
        value: '0'
        value_type: String
```

Поддерживаемые `kind`:
- `reg_set` / `reg_delete` — реестр
- `service_disable` / `service_manual` / `service_delete` — службы
- `power_plan` — план электропитания (value = GUID)
- `appx_remove`, `sched_task_disable`, `shell_ext` — зарезервированы

Перед использованием: `win11opt rules validate`.

## Безопасность

- Каждое действие перед изменением читает текущее значение и сохраняет его в snapshot
- Перед apply создаётся Windows Restore Point
- Snapshot хранится в `%LOCALAPPDATA%\win11opt\snapshots\`
- Rollback восстанавливает значения в обратном порядке

## Лицензия

MIT
