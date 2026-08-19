"""win11opt.rules — встроенные правила, пресеты и YAML loader."""
from .builtin import PRESETS, get_preset
from .loader import (
    DEFAULT_RULES_DIR, RuleLoadError, load_all, load_preset,
    validate_dir, validate_file,
)

__all__ = [
    "PRESETS", "get_preset",
    "DEFAULT_RULES_DIR", "RuleLoadError",
    "load_all", "load_preset",
    "validate_dir", "validate_file",
]


def get_rules(use_yaml: bool = True) -> dict:
    """Вернуть {rule_id: Rule}. YAML (если есть) перекрывает builtin."""
    from .builtin import BUILTIN_RULES
    merged = dict(BUILTIN_RULES)
    if use_yaml:
        try:
            yaml_rules = load_all()
            merged.update(yaml_rules)
        except RuleLoadError:
            # YAML не валиден — отдаём только builtin, не падаем
            pass
    return merged
