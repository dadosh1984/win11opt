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

# Информация о системе (OS/CPU/RAM/Disk/GPU) — read-only
win11opt info
win11opt info --json

# Применить пресет (dry-run, ничего не меняет)
win11opt apply --profile Balanced --dry-run

# Рекомендованная точка входа для новичков (7 low-risk твиков)
win11opt apply --profile Safe --dry-run

# Для геймеров: Game Bar/DVR off + Ultimate Performance (без удаления Xbox Game Pass)
win11opt apply --profile Gaming --dry-run

# Реально применить (попросит UAC)
win11opt apply --profile Balanced

# Список snapshot'ов
win11opt snapshot list

# Откатить к snapshot
win11opt snapshot restore 20250101-120000

# Бенчмарк (стартовая точка)
win11opt bench

# Сохранить baseline (например 'pre')
win11opt bench save --label pre

# Применить твики
win11opt apply --profile Balanced

# Сравнить с baseline + HTML-отчёт
win11opt bench diff latest --out E:/reports/pre.json
win11opt bench diff latest --html E:/reports/report.html

# Список baselines
win11opt bench list

# Подкоманды:
#   bench save [--label LABEL]          → измерить и сохранить
#   bench diff [PATH|latest] [--out P] [--html H]  → сравнить current с baseline (JSON и/или HTML-отчёт)
#   bench list                          → показать все baselines
#   bench report [PATH]                 → напечатать diff-отчёт (последний, если PATH не указан)

# Графический интерфейс
win11opt gui
```

## Пресеты

| Имя | Что делает |
|---|---|
| **Balanced** | Безопасный: анимации, UI, Explorer, телеметрия, питание, гибернация |
| **Aggressive** | Максимум отзывчивости: службы, Game Bar, OneDrive, network, NTFS |
| **Privacy** | Полная телеметрия/реклама: CEIP, Activity History, Tailored, Cortana |
| **Debloat** | Удаление UWP-приложений (Xbox, Bing, GetHelp). Необратимо. |
| **Hardened** | Продвинутый: ослабление Defender Cloud + отложенные Update. **НЕ удаляет Defender/Edge.** |
| **Safe** | 7 самых безопасных твиков. Рекомендованная точка входа для новичков. |
| **Gaming** | Для геймеров: Game Bar/DVR off, Ultimate Performance, без Xbox-фон-сервисов. **Не удаляет Xbox Game Pass.** |

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
- **telemetry** — рекламный ID, CEIP, Activity History, Tailored Experiences
- **power** — Ultimate Performance, отключение гибернации (hiberfil.sys)
- **tasks** *(scheduled_tasks)* — отключение телеметрии, Xbox-tasks, FEH
- **storage** — Storage Sense, Delivery Optimization (P2P upstream)
- **appcompat** — PCA, Steps Recorder, Suggestions, Windows Copilot
- **network** — отключение Nagle, throttling, Gaming QoS (низкая задержка)
- **ntfs** — отключение last-access-time, 8.3 имён (ускорение файловых операций)
- **registry** — UAC no-delay

## Полный список правил (52)

| ID | Категория | Риск | Reboot | Описание |
|---|---|---|---|---|
| `appcompat.disable_copilot` | appcompat | low |  | DisableWindowsCopilot=1 — убирает AI-помощник из панели задач. Фоновая обработка отключается. |
| `appcompat.disable_pca_engine` | appcompat | low |  | PCA каждый раз проверяет установленные программы на совместимость. На SSD тормозит систему. |
| `appcompat.disable_steps_recorder` | appcompat | low |  | Steps Recorder не запускается автоматически, но отключает фоновые процессы. |
| `appcompat.disable_windows_suggestions` | appcompat | low |  | Отключает подсказки в Settings и рекомендации приложений. |
| `debloat.remove_apps_duplicates` | debloat | medium |  | Удаляет MixedReality, PhoneLink, People — дублируют стандартные функции. |
| `debloat.remove_bing_apps` | debloat | medium |  | Удаляет BingWeather, BingNews, BingFinance, BingSports. Используйте Edge/браузер для погоды. |
| `debloat.remove_help_apps` | debloat | low |  | Удаляет GetHelp, Tips (Microsoft Tips), FeedbackHub. Не нужны обычному пользователю. |
| `debloat.remove_xbox_apps` | debloat | medium |  | Удаляет XboxGameOverlay, XboxGameCallableUI, XboxIdentityProvider, XboxSpeechToTextOverlay. Освобождает фоновые процессы. |
| `defender.disable_cloud_protection` | defender | medium |  | SpyNetReporting=0, SubmitSamplesConsent=0 — Defender перестаёт слать образцы в Microsoft. Уменьшает фоновый трафик. |
| `defender.disable_mp_telemetry` | defender | low |  | MpTelemetry=0 — отключает ETW-канал телеметрии Defender. Уменьшает нагрузку на диск (меньше записей в Event Log). |
| `defender.disable_smart_screen` | defender | medium |  | EnableSmartScreen=0 для Edge/Store/Explorer. Предупреждения о скачиваемых файлах отключаются. Защита от фишинга остаётся через DNS/Network protection. |
| `explorer.launch_to_this_pc` | explorer | low |  | LaunchTo=1 — при запуске Проводник открывает This PC (XP-style), а не Home. |
| `explorer.show_extensions` | explorer | low |  | HideFileExt=0 — Windows показывает .txt, .exe и т.п. Безопасность + меньше фишинга. |
| `explorer.show_full_path_in_title` | explorer | low |  | FullPath=1 — заголовок Проводника показывает полный путь к текущей папке. |
| `explorer.show_status_bar` | explorer | low |  | ShowStatusBar=1 — внизу Проводника информация о выделенных файлах. |
| `gaming.disable_gamebar` | gaming | low | ✅ | GameDVR_Enabled=0 + AppCaptureEnabled=0 — Game Bar жрёт CPU при alt-tab и записи игр. Требуется ребут. |
| `gaming.disable_xbox_gamebar_hotkey` | gaming | low |  | GameBarAutoStartEnabled=0 — Win+G не открывает Game Bar при нажатии. |
| `network.disable_gaming_qos` | network | low |  | Do not use NLA=1 — отключает приоритизацию трафика Windows (DSCP). Убирает лишнюю обработку пакетов. |
| `network.disable_nagle` | network | low |  | TcpAckFrequency=1 + TCPNoDelay=1 — отключает задержку Nagle. Меньше latency в играх и при удалённой работе. Незначительно увеличивает трафик. |
| `network.disable_throttling` | network | low |  | NetworkThrottlingIndex=0xffffffff — Windows не ограничивает сетевую пропускную способность для мультимедиа. Полезно для стриминга и игр. |
| `ntfs.disable_8dot3_names` | ntfs | low |  | NtfsDisable8dot3NameCreation=1 — NTFS не создаёт короткие DOS-имена (PROGRA~1). Ускоряет создание файлов в папках с тысячами файлов. |
| `ntfs.disable_last_access_time` | ntfs | low |  | NtfsDisableLastAccessUpdate=1 — NTFS не обновляет время последнего доступа к файлу. Ускоряет чтение файлов (меньше записей на диск). |
| `ntfs.disable_short_name_creation` | ntfs | low |  | Win31FileSystem=0 — отключает совместимость с Win3.1 (короткие имена). Ускоряет файловые операции. |
| `onedrive.disable_autostart` | onedrive | low |  | SilentAcquiredTier=DWORD:000000f5 — отключает запуск OneDrive при логине. |
| `onedrive.disable_startup` | onedrive | low |  | DisableFileSyncNGSC=1 — отключает фоновую синхронизацию OneDrive. OneDrive остаётся установленным. |
| `power.disable_hibernation` | power | low |  | powercfg -h off — удаляет hiberfil.sys (40-75% RAM). Освобождает место на SSD и ускоряет TRIM. На десктопе без UPS безопасно. |
| `power.ultimate_performance` | power | low |  | Скрытый план питания, который не экономит энергию — максимум отзывчивости. На ноутбуке разряжает быстрее. |
| `registry.uac_no_delay` | registry | medium |  | ConsentPromptBehaviorAdmin=0 — UAC появляется, но без затемнения экрана и без задержки. Безопасность не снижается. |
| `services.disable_diagtrack` | services | medium |  | Microsoft Connected User Experiences and Telemetry — отправляет диагностические данные. |
| `services.disable_search_indexer` | services | medium |  | Индексация диска на SSD создаёт лишний I/O. Полнотекстовый поиск в меню Пуск перестаёт работать. |
| `services.disable_xbox` | services | medium |  | XGameRouter, XboxGipSvc и т.п. — нужны только для Xbox Game Pass / Xbox-контроллеров. |
| `storage.disable_delivery_optimization` | storage | low |  | Отключает P2P-доставку обновлений Windows. Твоя машина не используется как раздатчик для других. |
| `storage.disable_storage_sense_temp` | storage | low |  | Storage Sense удаляет папку Temp каждые 30 дней. Отключает если мешает сборке/компиляции. |
| `storage.enable_storage_sense` | storage | low |  | Storage Sense автоматически удаляет временные файлы и файлы из Корзины старше 30 дней. Освобождает место без участия пользователя. |
| `tasks.disable_fehcache` | scheduled_tasks | low |  | Фоновый cleanup файла-эскизов. На SSD бесполезен, на HDD включается по требованию. |
| `tasks.disable_telemetry` | scheduled_tasks | medium |  | Отключает 10+ scheduled tasks под Microsoft\\Windows, которые собирают и отправляют телеметрические данные. |
| `tasks.disable_xbox_related` | scheduled_tasks | low |  | XboxGameSaveTask, Consolidator — фоновые задачи Xbox (нужны только для Xbox Game Pass). |
| `telemetry.advertising_id` | telemetry | low |  | Рекламный ID используется приложениями UWP для таргетированной рекламы. |
| `telemetry.disable_activity_history` | telemetry | low |  | Activity History синхронизирует историю действий между устройствами. Отключает сбор и отправку. |
| `telemetry.disable_ceip` | telemetry | low |  | CEIP собирает данные об использовании Windows. AllowTelemetry=0 + CEIPEnable=0 отключает сбор. |
| `telemetry.disable_feedback_frequency` | telemetry | low |  | DoNotShowFeedbackNotifications=1 — Windows не спрашивает "как вам Windows?". |
| `telemetry.disable_tailored_experiences` | telemetry | low |  | TailoredExperiencesWithDiagnosticDataEnabled=0 — Windows не использует диагностику для персонализации рекламы. |
| `ui.instant_menu` | ui | low |  | MenuShowDelay=0 — контекстные меню появляются без 400мс задержки. XP-style поведение. |
| `ui.instant_tooltips` | ui | low |  | MouseHoverTime=10 — тултипы появляются через ~17мс вместо 400мс по умолчанию. |
| `ui.no_cortana` | ui | medium |  | AllowCortana=0 — отключает поиск Cortana. Плоский поиск Windows остаётся работать. |
| `ui.no_lockscreen` | ui | medium | ✅ | DisableLockScreenAppNotifications=1 — убрать рекламный lockscreen. Требуется ребут. |
| `update.defer_feature_updates` | update | low |  | DeferFeatureUpdatesPeriodInMonths=12 — major updates (23H2 → 24H2) не ставятся автоматически. Security updates продолжают ставиться. |
| `update.defer_quality_updates` | update | low |  | DeferQualityUpdatesPeriodInDays=7 — ежемесячные патчи безопасности ставятся через неделю после выхода (время на стабилизацию). |
| `update.disable_driver_search` | update | low |  | ExcludeWUDriversInQualityUpdate=1 — Windows Update не подтягивает драйверы автоматически (ты сам ставишь через Device Manager). |
| `update.notify_only` | update | medium |  | SetPolicy=2 — Windows Update скачивает обновления только когда ты сам нажмёшь "Скачать". Автоматическая загрузка отключена. |
| `visual.classic_context_menu` | visual | low | ✅ | Win11 прячет часть команд за "Show more options". Возвращаем полное меню сразу. |
| `visual.disable_animations` | visual | low |  | Убирает анимацию свёртывания/развёртывания/закрытия окон. Сильно влияет на ощущение скорости UI. |

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
- `power_plan` — план электропитания (target = GUID)
- `hibernate_off` / `hibernate_on` — гибернация (powercfg -h)
- `appx_remove` — удаление UWP-приложения (target = маска имени)
- `sched_task_disable`, `shell_ext` — зарезервированы

Перед использованием: `win11opt rules validate`.

## Метрики bench

- `idle_ram_mb` — свободная RAM в MB
- `idle_cpu_pct` — %CPU idle (среднее за 2 сек)
- `startup_apps_count` — количество автозагрузки
- `services_running` — количество запущенных служб
- `sched_tasks_enabled` — количество включённых scheduled tasks
- `explorer_first_paint_ms` — время до появления главного окна Проводника
- `services_by_state` — разбивка служб по состоянию (Running / Stopped / Disabled / ...)

Baseline хранится в `%LOCALAPPDATA%\win11opt\bench\`.

Diff-отчёт `до/после` можно сохранить в JSON (`bench diff latest --out report.json`)
и затем напечатать в человекочитаемом виде (`bench report [path]` — по умолчанию последний).

## Документация Microsoft

Каждое правило имеет `ms_doc_url` — ссылку на официальную документацию Microsoft,
которая описывает соответствующий ключ реестра / службу / задачу. Увидеть можно через:

```bash
win11opt rules describe <id>
```

Это гарантирует: правила не выдуманы, каждое задокументировано вендором.

## Безопасность

- Каждое действие перед изменением читает текущее значение и сохраняет его в snapshot
- Перед apply создаётся Windows Restore Point
- Snapshot хранится в `%LOCALAPPDATA%\win11opt\snapshots\`
- Rollback восстанавливает значения в обратном порядке

## Лицензия

MIT
