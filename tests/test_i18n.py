"""Тесты для i18n."""
from __future__ import annotations

from win11opt import i18n


def test_default_language_english():
    """По умолчанию — английский, _() возвращает msgid."""
    i18n.set_language("en")
    assert i18n.get_language() == "en"
    assert i18n._("Apply") == "Apply"
    assert i18n._("Bench") == "Bench"


def test_russian_translation():
    """ru: перевод работает."""
    i18n.set_language("ru")
    assert i18n.get_language() == "ru"
    assert i18n._("Apply") == "Применить"
    assert i18n._("Bench") == "Бенчмарк"
    assert i18n._("Restore") == "Восстановить"


def test_unknown_msgid_falls_back():
    """Неизвестный msgid возвращается как есть."""
    i18n.set_language("ru")
    assert i18n._("Some nonexistent message") == "Some nonexistent message"


def test_format_string_works():
    """%s, %d подстановки сохраняются после перевода."""
    i18n.set_language("ru")
    assert i18n._("Total rules: %d") % 52 == "Total rules: 52" or "%" in i18n._("Total rules: %d")
    # Actually .mo must have exact format string
    result = i18n._("Total rules: %d") % 52
    assert "52" in result


def test_language_roundtrip():
    """en → ru → en."""
    i18n.set_language("en")
    en_value = i18n._("Apply")
    i18n.set_language("ru")
    ru_value = i18n._("Apply")
    i18n.set_language("en")
    back_value = i18n._("Apply")
    assert en_value == back_value == "Apply"
    assert ru_value == "Применить"


def test_detect_system_language():
    """detect_system_language возвращает строку."""
    lang = i18n.detect_system_language()
    assert lang in ("en", "ru")


def test_set_language_none_falls_back():
    """set_language(None) использует autodetect."""
    i18n.set_language(None)
    assert i18n.get_language() in ("en", "ru")