# Spec: single_exe_uac_elevated_native_gui_elect

## Назначение
Native single-EXE утилита (C# .NET 8 + WPF) под Win11 22H2+ (x64/arm64) для
оптимизации интерактивной отзывчивости UI — чтобы система ощущалась
такой же быстрой, как Windows XP. Не меняет железо, не нагружает сеть,
не отправляет телеметрию.

## Область

В области:
- Визуальные эффекты (анимации, тени, Mica/Acrylic, классическое меню)
- Службы и автозагрузка (SysMain, DiagTrack, SearchIndexer, Xbox и др.)
- Телеметрия и реклама (диагностика=0, рекламный ID, Activity History, OneDrive)
- Питание (Ultimate Performance, Game Bar/DVR)
- Реестр (UAC без задержек, lock screen/CAD)
- Безопасность операций (точка восстановления, snapshot, rollback, dry-run)
- CLI + WPF GUI
- Правила в YAML
- Бенчмарк до/после

Вне области (YAGNI rung 7):
- Реестр-дефрагментатор
- Memory booster
- Удаление Edge / MS Store без restore
- VBS/HVCI off по умолчанию
- Подпись бинаря (MVP — unsigned)
- Телеметрия в самой утилите
- Автообновления

## Критерии приёмки

- [ ] `dotnet build -c Release` собирает solution без warnings-as-errors
- [ ] `dotnet test` все тесты зелёные
- [ ] `dotnet publish -c Release -r win-x64 --self-contained -p:PublishSingleFile=true` даёт single EXE
- [ ] EXE запрашивает UAC elevation при запуске
- [ ] CLI `apply --profile Aggressive --dry-run` показывает дифф без модификации системы
- [ ] CLI `apply --profile Aggressive` создаёт restore point перед изменениями
- [ ] CLI `snapshot create/restore` работает round-trip (изменение → откат)
- [ ] GUI: категории слева, тумблеры справа, dry-run/apply бар внизу
- [ ] Бенчмарк: idle RAM, services count, autoruns count → JSON отчёт
- [ ] Нет сетевых вызовов (проверено статическим анализом)
- [ ] YAML правила валидируются и не применяются, если не прошли
- [ ] Профили: Aggressive, Balanced, Privacy, Gaming, Restore — все загружаются
- [ ] README + LICENSE в репозитории
