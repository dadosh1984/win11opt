# Дизайн — программу-оптимизации-windows-11

## Обзор
Native single-EXE утилита (C# .NET 8 + WPF) под Win11 22H2+, делающая
систему такой же отзывчивой, как Windows XP. Цель — **интерактивная
отзывчивость UI** (открытие меню, запуск приложений, переключение окон,
idle RAM/CPU), а не raw CPU-производительность.

Аналоги изучены: Win11Debloat, Optimizer (hellzerg), CTTWU, Sophia Script,
O&O ShutUp10, Autoruns, Tron. Взято: undo (Win11Debloat), модули+WPF
(Optimizer), категории-тумблеры (CTTWU), описания с ссылками (ShutUp10),
показ всех источников автозагрузки (Autoruns), обязательный restore point
(Tron). Отброшено: registry defragmenter, memory booster, удаление Edge,
принудительное VBS-off, скрытая телеметрия.

## Архитектура

```
src/
├── Win11Optimizer.Core/         # Rule engine, snapshot/rollback, models
├── Win11Optimizer.Rules/        # YAML правила + встроенные пресеты
├── Win11Optimizer.Bench/        # Бенчмарк до/после
├── Win11Optimizer.CLI/          # CLI (System.CommandLine)
└── Win11Optimizer.App/          # WPF GUI
rules/                           # YAML правила (внешние пресеты)
tests/
docs/
```

## Модули (по слоям оптимизации)

| Слой | Содержимое | Риск |
|---|---|---|
| 1. Визуал | Анимации, тени, Mica/Acrylic, классическое контекст-меню, скрыть Copilot/Widgets/Search | низкий |
| 2. Службы и автозагрузка | SysMain, DiagTrack, Search indexer, Xbox, Biometric, Phone Link; Startup-менеджер (Run/Services/ScheduledTasks/ShellExt/AppXSvc); деблoат предустановленного | средний |
| 3. Телеметрия/реклама | Диагностические данные=0, рекламный ID, Activity History, синхронизация; OneDrive; Edge-телеметрия | низкий |
| 4. Питание/железо | План Ultimate Performance, Game Bar/DVR, GPU perf preference | низкий |
| 5. Реестр | UAC без задержек (ConsentPromptBehaviorAdmin=0 для одобренных), отключение lock screen/CAD, метро-уведомления | средний |
| 6. Безопасность операций | Точка восстановления, снимок реестра, dry-run, rollback | обязательно |
| 7. UX | GUI на WPF, профили Aggressive/Balanced/Privacy/Gaming/Restore, бенчмарк до/после | обязательно |

## Пресеты (профили)

- **Aggressive** — слои 1+2+3+4+5, максимум отзывчивости
- **Balanced** — слои 1+3+4, разумный компромисс
- **Privacy** — слой 3 максимально
- **Gaming** — слой 4 + отключение Game Bar/DVR
- **Restore** — откат к snapshot, не модифицирует систему

## Допущения
- Стек .NET 8 SDK уже установлен
- Single EXE через `dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true`
- Подпись — out of scope MVP (через signtool позже)
- Правила в YAML парсятся через YamlDotNet
- Снимок реестра — `reg export` всех ключей, которые мы трогаем
- Точка восстановления — через PowerShell `Checkpoint-Computer`
- Бенчмарк: idle RAM (GC.GetTotalMemory + WMI), диск-IO (опц.), холодная загрузка (EventLog)

## Верификация
Задача считается сданной, только когда проходят все гейты:
- [ ] `dotnet build -c Release` без ошибок и предупреждений как ошибки
- [ ] `dotnet test` все зелёные
- [ ] CLI `--dry-run` показывает дифф без применения
- [ ] Snapshot → apply → rollback восстанавливает исходное состояние
- [ ] Нет сетевых вызовов в бинаре (verified via static analysis)

## YAGNI Ladder Trace

| Решение | Rung | Обоснование |
|---|---|---|
| Single-EXE | 2 smallest | portable, no install |
| WPF vs Avalonia vs Tauri | 6 alternatives | WPF — минимальная зависимость, нативно, готовые утилиты (hellzerg) есть |
| Своё vs fork Win11Debloat | 3 own vs buy | нужен нормальный GUI и бенчмарк |
| YAML правила | 4 now vs later | нужно сразу для пресетов |
| Бенчмарк до/после | 4 now vs later | MVP = базовый (RAM, диск), cold-boot est — v1.1 |
| VBS/HVCI toggle | 7 delete | дефолт off — слишком рискованно для безопасности |
| Registry defragmenter | 7 delete | шум, не оптимизация |
| Memory booster | 7 delete | шум |
| Edge removal | 7 delete | ломает многое, нет восстановления |
| Подпись бинаря | 4 later | MVP — unsigned, документируем |
| Telemetry в утилите | 7 delete | противоречит цели |
