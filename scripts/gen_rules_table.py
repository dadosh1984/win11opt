"""Генерирует markdown-таблицу всех правил из rules/*.yaml.

Использование:
    python scripts/gen_rules_table.py > rules_table.md

Таблица вставляется в README.md вручную (или через sed).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from win11opt.rules.loader import load_all  # noqa: E402


def main() -> None:
    rules = load_all()
    print("| ID | Категория | Риск | Reboot | Описание |")
    print("|---|---|---|---|---|")
    for rid in sorted(rules):
        r = rules[rid]
        reboot = "✅" if r.requires_reboot else ""
        desc = r.description.replace("|", "\\|").replace("\n", " ")
        print(f"| `{rid}` | {r.category} | {r.risk.value} | {reboot} | {desc} |")


if __name__ == "__main__":
    main()
