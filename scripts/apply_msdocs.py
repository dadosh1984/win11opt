"""Дополняет ms_doc_url в каждом YAML на основе EXPECTED_URLS.

Использование: python scripts/apply_msdocs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Импортируем EXPECTED_URLS из audit
sys.path.insert(0, str(ROOT / "scripts"))
import yaml
from audit_msdocs import EXPECTED_URLS

RULES_DIR = ROOT / "rules"


def _str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_representer)


def main():
    applied = 0
    for ypath in sorted(RULES_DIR.glob("*.yaml")):
        text = ypath.read_text(encoding="utf-8")
        # Простой парсинг (top-level keys: name, description, rules)
        data = yaml.safe_load(text)
        if not isinstance(data, dict) or "rules" not in data:
            continue
        modified = False
        for rule in data["rules"]:
            rid = rule.get("id", "")
            if rid in EXPECTED_URLS and not rule.get("ms_doc_url"):
                rule["ms_doc_url"] = EXPECTED_URLS[rid]
                applied += 1
                modified = True
        if modified:
            # Сохраняем header order как было
            out = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
            ypath.write_text(out, encoding="utf-8")
            print(f"updated: {ypath.name}")
    print(f"\nApplied: {applied} ms_doc_url entries")


if __name__ == "__main__":
    main()
