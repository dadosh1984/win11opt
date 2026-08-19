"""Generate ru.po from win11opt.pot with Russian translations."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POT = ROOT / "locale" / "win11opt.pot"
RU_PO = ROOT / "locale" / "ru" / "LC_MESSAGES" / "win11opt.po"
EN_PO = ROOT / "locale" / "en" / "LC_MESSAGES" / "win11opt.po"

# Translations: msgid -> msgstr (ru)
TRANSLATIONS: dict[str, str] = {
    "Apply": "Применить",
    "Dry-run": "Пробный запуск",
    "Restore point created": "Точка восстановления создана",
    "Snapshot": "Снимок",
    "Rule": "Правило",
    "Rules": "Правила",
    "Baseline": "Базовая линия",
    "Saved": "Сохранено",
    "Bench": "Бенчмарк",
    "Bench before": "Бенчмарк до",
    "Bench after": "Бенчмарк после",
    "Apply preset": "Применить пресет",
    "Preset": "Пресет",
    "Categories": "Категории",
    "Description": "Описание",
    "Documentation": "Документация",
    "Apply selected": "Применить выбранные",
    "Dry-run selected": "Пробный прогон",
    "Snapshots": "Снимки",
    "Confirm apply": "Подтвердить применение",
    "Restore": "Восстановить",
    "Rollback": "Откатить",
    "before": "до",
    "after": "после",
    "delta": "разница",
    "metric": "метрика",
    "Yes": "Да",
    "No": "Нет",
    "Cancel": "Отмена",
    "OK": "ОК",
    "Error": "Ошибка",
    "No rules selected": "Правила не выбраны",
    "No baseline": "Нет базовой линии",
    "Idle": "Готов",
    "ready": "готово",
    "open GUI": "открыть GUI",
    "show this help": "показать эту справку",
    "Version": "Версия",
    "Language": "Язык",
    "Source language": "Исходный язык",
    "Total rules: %d": "Всего правил: %d",
    "Profile: %s (%d rules)": "Профиль: %s (%d правил)",
    "snapshot %s": "снимок %s",
    "rolled back to %s": "откат к %s",
    "apply %d action(s)": "применить %d действий",
    "rollback %d action(s)": "откатить %d действий",
    "create restore point": "создать точку восстановления",
    "delete registry key %s": "удалить ключ реестра %s",
    "set registry %s": "установить реестр %s",
    "service %s → disabled": "служба %s → отключена",
    "service %s → manual": "служба %s → вручную",
    "delete service %s": "удалить службу %s",
    "disable scheduled task %s": "отключить задачу %s",
    "enable scheduled task %s": "включить задачу %s",
    "remove app %s": "удалить приложение %s",
    "activate power plan %s": "активировать план питания %s",
    "disable hibernation (%s)": "отключить гибернацию (%s)",
    "enable hibernation (%s)": "включить гибернацию (%s)",
    "Shell extension removed: %s": "Расширение оболочки удалено: %s",
    "Cannot rollback APPX_REMOVE — reinstallation required":
        "Невозможно откатить APPX_REMOVE — требуется переустановка",
    "dry-run: %d rule(s), %d action(s) planned":
        "пробный запуск: %d правил, %d действий запланировано",
    "applied %d action(s), snapshot %s": "применено %d действий, снимок %s",
    "rollback snapshot %s — %d action(s) to undo":
        "откат снимка %s — отменить %d действий",
    "rollback complete": "откат завершён",
    "All YAML presets are valid": "Все YAML-пресеты валидны",
    "YAML validation failed: %s": "Ошибка валидации YAML: %s",
    "Unknown preset: %s": "Неизвестный пресет: %s",
    "Rule not found: %s": "Правило не найдено: %s",
    "Bench BEFORE": "Бенчмарк ДО",
    "Bench AFTER": "Бенчмарк ПОСЛЕ",
    "Bench BEFORE: RAM %d/%d MB, CPU %.1f%%, services %d, tasks %d":
        "Бенчмарк ДО: RAM %d/%d МБ, CPU %.1f%%, служб %d, задач %d",
    "Bench AFTER: RAM %d MB (Δ%+d), services %d (Δ%+d), tasks %d (Δ%+d)":
        "Бенчмарк ПОСЛЕ: RAM %d МБ (Δ%+d), служб %d (Δ%+d), задач %d (Δ%+d)",
    "Bench after": "Бенчмарк после",
    "Bench diff": "Сравнить с baseline",
    "Bench list": "Список baseline",
    "Bench save": "Сохранить baseline",
    "Save baseline before applying rules: %s bench save --label pre":
        "Сохраните baseline перед применением: %s bench save --label pre",
    "Compare: %s bench diff latest": "Сравнить: %s bench diff latest",
    "Language: %s": "Язык: %s",
    "Tip: %s": "Подсказка: %s",
    "Examples": "Примеры",
    "Show current language": "Показать текущий язык",
    "Set language (en/ru)": "Установить язык (en/ru)",
    "List all available rules": "Список всех правил",
    "Describe a specific rule by id": "Описать правило по id",
    "Validate all YAML presets": "Проверить все YAML-пресеты",
    "Apply a preset by name": "Применить пресет по имени",
    "Apply one rule by id": "Применить одно правило по id",
    "Snapshot current state": "Снимок текущего состояния",
    "List all snapshots": "Список снимков",
    "Restore from a snapshot": "Восстановить из снимка",
    "Measure system responsiveness": "Измерить отзывчивость системы",
    "Save baseline with optional label": "Сохранить baseline с меткой",
    "Compare current state to a saved baseline": "Сравнить текущее состояние с baseline",
    "List all saved baselines": "Список всех baseline",
    "Restore selected": "Восстановить выбранный",
    "snapshot": "снимок",
    "stored in %s": "хранится в %s",
    "Confirm rollback to %s?": "Подтвердить откат к %s?",
    "Apply %d rule(s)? A restore point will be created.":
        "Применить %d правил? Будет создана точка восстановления.",
    "rule": "правило",
    "rules": "правил",
    "rules loaded": "правил загружено",
    "DRY-RUN: %d rules, %d actions": "ПРОБНЫЙ: %d правил, %d действий",
    "APPLIED %d actions — snapshot %s": "ПРИМЕНЕНО %d действий — снимок %s",
    "APPLY %d/%d: %s": "ПРИМЕНИТЬ %d/%d: %s",
    "DRY-RUN %d/%d: %s": "ПРОБНЫЙ %d/%d: %s",
    "risk": "риск",
    "reboot": "перезагрузка",
    "high": "высокий",
    "medium": "средний",
    "low": "низкий",
    "off": "выкл",
    "on": "вкл",
    "OK: %s": "ОК: %s",
    "FAIL: %s": "ОШИБКА: %s",
    "OK: applied": "ОК: применено",
    "Rollback only restores registry/service changes. APPX removal, power plan and hibernation changes require manual intervention.":
        "Откат восстанавливает только реестр/службы. Удаление APPX, план питания и гибернация требуют ручного вмешательства.",
    "Win11Optimizer %s": "Win11Оптимизатор %s",
    "Windows 11 optimization utility — make Win11 feel like WinXP":
        "Утилита оптимизации Windows 11 — сделай Win11 отзывчивой как WinXP",
    "Set language for this invocation only (en/ru)":
        "Установить язык только для этого вызова (en/ru)",
    "language: %s": "язык: %s",
    "available: %s": "доступно: %s",
    "supported": "поддерживается",
    "Metric": "Метрика",
    "Before": "До",
    "After": "После",
    "Delta": "Разница",
    "RAM": "RAM",
    "CPU": "CPU",
    "Apps": "Приложения",
    "Services": "Службы",
    "Tasks": "Задачи",
    "Explorer": "Проводник",
    "ms": "мс",
    "MB": "МБ",
    "%%": "%%",
    "Baseline: %s (%s)": "Baseline: %s (%s)",
    "Current: %s": "Текущее: %s",
    "Tip: save baseline before applying rules: %s bench save --label pre":
        "Подсказка: сохраните baseline перед применением: %s bench save --label pre",
    "then compare: %s bench diff latest": "затем сравните: %s bench diff latest",
    "Saved: %s": "Сохранено: %s",
    "Rules file: %s": "Файл правил: %s",
    "Apply? A restore point will be created.": "Применить? Будет создана точка восстановления.",
    "Validation failed: %s": "Ошибка валидации: %s",
}


def _parse_pot(text: str) -> list[tuple[str, str]]:
    """Returns list of (msgid, msgstr). Headers first."""
    pairs = []
    cur_id: str | None = None
    cur_str: str | None = None
    state = "none"
    for line in text.splitlines():
        line = line.rstrip("\r")
        if line.startswith("msgid "):
            cur_id = line[6:].strip().strip('"')
            state = "id"
        elif line.startswith("msgstr "):
            cur_str = line[7:].strip().strip('"')
            state = "str"
        elif line.startswith('"') and state == "id":
            cur_id = (cur_id or "") + line.strip().strip('"')
        elif line.startswith('"') and state == "str":
            cur_str = (cur_str or "") + line.strip().strip('"')
        elif not line.strip() and cur_id is not None and cur_str is not None:
            pairs.append((cur_id, cur_str))
            cur_id = None
            cur_str = None
            state = "none"
    if cur_id is not None and cur_str is not None:
        pairs.append((cur_id, cur_str))
    return pairs


def _format_po(msgids: list[str], lang: str) -> str:
    """Build .po file from msgids, translating via TRANSLATIONS dict."""
    lines = [
        'msgid ""',
        'msgstr ""',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        f'"Language: {lang}\\n"',
        '"Project: Win11Optimizer\\n"',
        '"Version: 1.3.0\\n"',
        "",
    ]
    for msgid in msgids:
        if not msgid:
            continue
        mid = msgid.replace("\\", "\\\\").replace('"', '\\"')
        if "\n" in msgid:
            mid_lines = msgid.split("\n")
            lines.append(f'msgid "{mid_lines[0]}"')
            for cont in mid_lines[1:]:
                lines.append(f'"{cont}"')
        else:
            lines.append(f'msgid "{mid}"')
        # Translate via dict (en == empty, ru == translated)
        if lang == "ru":
            ms = TRANSLATIONS.get(msgid, "")
        else:
            ms = ""
        ms = ms.replace("\\", "\\\\").replace('"', '\\"')
        if "\n" in ms:
            ms_lines = ms.split("\n")
            lines.append(f'msgstr "{ms_lines[0]}"')
            for cont in ms_lines[1:]:
                lines.append(f'"{cont}"')
        else:
            lines.append(f'msgstr "{ms}"')
        lines.append("")
    return "\n".join(lines) + "\n"


def _extract_msgids(text: str) -> list[str]:
    """Extract msgids from .pot (header + entries)."""
    ids = []
    cur_id: str | None = None
    state = "none"
    for line in text.splitlines():
        line = line.rstrip("\r")
        if line.startswith("msgid "):
            cur_id = line[6:].strip().strip('"')
            state = "id"
        elif line.startswith("msgstr "):
            if cur_id is not None:
                ids.append(cur_id)
            cur_id = None
            state = "str"
        elif line.startswith('"') and state == "id":
            cur_id = (cur_id or "") + line.strip().strip('"')
        elif line.startswith('"') and state == "str":
            pass
        elif not line.strip() and cur_id is not None:
            ids.append(cur_id)
            cur_id = None
            state = "none"
    if cur_id is not None:
        ids.append(cur_id)
    return ids


def main():
    pot_text = POT.read_text(encoding="utf-8")
    msgids = _extract_msgids(pot_text)
    print(f"POT msgids: {len(msgids)}")

    # English .po: empty msgstr (translations == msgid)
    EN_PO.parent.mkdir(parents=True, exist_ok=True)
    EN_PO.write_text(_format_po(msgids, "en"), encoding="utf-8")
    print(f"wrote: {EN_PO}")

    # Russian .po
    RU_PO.parent.mkdir(parents=True, exist_ok=True)
    RU_PO.write_text(_format_po(msgids, "ru"), encoding="utf-8")
    print(f"wrote: {RU_PO}")
    non_empty = [m for m in msgids if TRANSLATIONS.get(m)]
    print(f"translated: {len(non_empty)}/{len(msgids)}")


if __name__ == "__main__":
    main()