"""Встроенные правила — hardcoded минимум для MVP.

YAML-пресеты пойдут в v0.2. Сейчас — набор правил в коде, чтобы не
плодить файлы на старте и не усложнять MVP.

ponytail: rung 2 — минимум, rung 4 — YAML отложен.
"""
from __future__ import annotations

from ..core.models import Action, ActionKind, Profile, Risk, Rule


# Категории — для группировки в GUI и фильтрации в CLI.
CAT_VISUAL = "visual"
CAT_SERVICES = "services"
CAT_STARTUP = "startup"
CAT_TELEMETRY = "telemetry"
CAT_POWER = "power"
CAT_REGISTRY = "registry"


def disable_animations() -> Rule:
    """Отключить анимации окон: MinAnimate=0, WindowMetrics\\MinAnimate=0."""
    return Rule(
        id="visual.disable_animations",
        name="Отключить анимации окон",
        description="Убирает анимацию свёртывания/развёртывания/закрытия окон. Сильно влияет на ощущение скорости UI.",
        category=CAT_VISUAL,
        risk=Risk.LOW,
        actions=(
            Action(
                kind=ActionKind.REG_SET,
                target=r"HKCU:\Control Panel\Desktop",
                name="UserPreferencesMask",
                # Без пересчёта битовой маски — оставляем совместимое значение,
                # которое выключает анимации (бит 1).
                value="0x90120A80D80100000090000090400000",
                value_type="String",
            ),
            Action(
                kind=ActionKind.REG_SET,
                target=r"HKCU:\Control Panel\Desktop\WindowMetrics",
                name="MinAnimate",
                value="0",
                value_type="String",
            ),
        ),
        ms_doc_url="https://learn.microsoft.com/en-us/windows/win32/uxguide/anim",
    )


def show_classic_context_menu() -> Rule:
    """Классическое контекстное меню Win10 (Show more options по умолчанию)."""
    return Rule(
        id="visual.classic_context_menu",
        name="Классическое контекстное меню",
        description="Win11 прячет часть команд за 'Show more options'. Возвращаем полное меню сразу.",
        category=CAT_VISUAL,
        risk=Risk.LOW,
        actions=(
            Action(
                kind=ActionKind.REG_SET,
                target=r"HKCU:\Software\Classes\CLSID\{86ca1aa0-2e05-4d4c-9827-7c91b7bcae34}\InprocServer32",
                name="(Default)",
                value="",
                value_type="String",
            ),
        ),
        requires_reboot=True,
        ms_doc_url="https://learn.microsoft.com/en-us/windows/win32/api/windows.ui.xaml.controls.primitives",
    )


def disable_search_indexer() -> Rule:
    """Отключить Windows Search индексатор (на SSD обычно вредит)."""
    return Rule(
        id="services.disable_search_indexer",
        name="Отключить Windows Search",
        description="Индексация диска на SSD создаёт лишний I/O. Полнотекстовый поиск в меню Пуск перестаёт работать.",
        category=CAT_SERVICES,
        risk=Risk.MEDIUM,
        actions=(
            Action(kind=ActionKind.SERVICE_DISABLE, target="WSearch"),
        ),
        ms_doc_url="https://learn.microsoft.com/en-us/windows/win32/search/-search-iface-indexer",
    )


def disable_diagtrack() -> Rule:
    """Отключить DiagTrack (Connected User Experiences and Telemetry)."""
    return Rule(
        id="services.disable_diagtrack",
        name="Отключить DiagTrack (телеметрия)",
        description="Microsoft Connected User Experiences and Telemetry — отправляет диагностические данные.",
        category=CAT_SERVICES,
        risk=Risk.MEDIUM,
        actions=(
            Action(kind=ActionKind.SERVICE_DISABLE, target="DiagTrack"),
            Action(kind=ActionKind.REG_SET,
                   target=r"HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                   name="AllowTelemetry",
                   value="0",
                   value_type="DWord"),
        ),
        ms_doc_url="https://learn.microsoft.com/en-us/windows/privacy/diagnostic-data",
    )


def disable_xbox_services() -> Rule:
    """Отключить Xbox-сервисы (часто ненужные на обычном ПК)."""
    return Rule(
        id="services.disable_xbox",
        name="Отключить Xbox-сервисы",
        description="XGameRouter, XboxGipSvc и т.п. — нужны только для Xbox Game Pass / Xbox-контроллеров.",
        category=CAT_SERVICES,
        risk=Risk.MEDIUM,
        actions=(
            Action(kind=ActionKind.SERVICE_DISABLE, target="XblGameSave"),
            Action(kind=ActionKind.SERVICE_DISABLE, target="XboxGipSvc"),
            Action(kind=ActionKind.SERVICE_DISABLE, target="XboxNetApiSvc"),
        ),
    )


def telemetry_advertising_id() -> Rule:
    """Отключить рекламный ID."""
    return Rule(
        id="telemetry.advertising_id",
        name="Отключить рекламный ID",
        description="Рекламный ID используется приложениями UWP для таргетированной рекламы.",
        category=CAT_TELEMETRY,
        risk=Risk.LOW,
        actions=(
            Action(kind=ActionKind.REG_SET,
                   target=r"HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                   name="Enabled",
                   value="0", value_type="DWord"),
        ),
        ms_doc_url="https://learn.microsoft.com/en-us/windows/privacy/advertising-id",
    )


def power_ultimate_performance() -> Rule:
    """Активировать план Ultimate Performance."""
    return Rule(
        id="power.ultimate_performance",
        name="План питания Ultimate Performance",
        description="Скрытый план питания, который не экономит энергию — максимум отзывчивости. На ноутбуке разряжает быстрее.",
        category=CAT_POWER,
        risk=Risk.LOW,
        actions=(
            # Сначала разблокируем план (на Win11 он скрыт)
            Action(kind=ActionKind.POWER_PLAN, target="ultimate", value="8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        ),
    )


# Реестр
def uac_no_prompt_for_approved() -> Rule:
    """Не показывать UAC-задержку для подписанных/одобренных операций."""
    return Rule(
        id="registry.uac_no_delay",
        name="UAC без задержки для одобренных операций",
        description="ConsentPromptBehaviorAdmin=0 — UAC появляется, но без затемнения экрана и без задержки. Безопасность не снижается.",
        category=CAT_REGISTRY,
        risk=Risk.MEDIUM,
        actions=(
            Action(kind=ActionKind.REG_SET,
                   target=r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                   name="ConsentPromptBehaviorAdmin",
                   value="0", value_type="DWord"),
        ),
        ms_doc_url="https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/user-account-control",
    )


# ── Пресеты ────────────────────────────────────────────────────────────

PRESETS: tuple[Profile, ...] = (
    Profile(
        name="Balanced",
        description="Безопасный набор: анимации, UI, Explorer, телеметрия, питание.",
        rule_ids=(
            "visual.disable_animations",
            "visual.classic_context_menu",
            "ui.instant_menu",
            "ui.instant_tooltips",
            "explorer.show_extensions",
            "explorer.show_status_bar",
            "telemetry.advertising_id",
            "telemetry.disable_ceip",
            "power.ultimate_performance",
            "power.disable_hibernation",
        ),
    ),
    Profile(
        name="Aggressive",
        description="Максимум отзывчивости. Включает отключение служб и UI.",
        rule_ids=(
            "visual.disable_animations",
            "visual.classic_context_menu",
            "ui.instant_menu",
            "ui.instant_tooltips",
            "explorer.show_extensions",
            "explorer.launch_to_this_pc",
            "telemetry.advertising_id",
            "telemetry.disable_ceip",
            "power.ultimate_performance",
            "power.disable_hibernation",
            "services.disable_search_indexer",
            "services.disable_diagtrack",
            "services.disable_xbox",
            "registry.uac_no_delay",
            "gaming.disable_gamebar",
            "onedrive.disable_startup",
            "network.disable_nagle",
            "network.disable_throttling",
            "ntfs.disable_last_access_time",
            "ntfs.disable_8dot3_names",
            "tasks.disable_telemetry",
            "tasks.disable_xbox_related",
            "storage.disable_delivery_optimization",
            "appcompat.disable_pca_engine",
            "appcompat.disable_copilot",
        ),
    ),
    Profile(
        name="Privacy",
        description="Только телеметрия/реклама.",
        rule_ids=(
            "telemetry.advertising_id",
            "telemetry.disable_ceip",
            "telemetry.disable_activity_history",
            "telemetry.disable_tailored_experiences",
            "telemetry.disable_feedback_frequency",
            "services.disable_diagtrack",
            "ui.no_cortana",
            "onedrive.disable_autostart",
            "tasks.disable_telemetry",
            "tasks.disable_xbox_related",
            "storage.disable_delivery_optimization",
            "appcompat.disable_windows_suggestions",
            "appcompat.disable_copilot",
        ),
    ),
    Profile(
        name="Debloat",
        description="Удаление UWP-приложений (Xbox, Bing, GetHelp). Необратимо.",
        rule_ids=(
            "debloat.remove_xbox_apps",
            "debloat.remove_bing_apps",
            "debloat.remove_help_apps",
        ),
    ),
    Profile(
        name="Hardened",
        description="Продвинутый: ослабление Defender Cloud + отложенные Update. Не удаляет Defender/Edge!",
        rule_ids=(
            "defender.disable_cloud_protection",
            "defender.disable_mp_telemetry",
            "update.defer_feature_updates",
            "update.defer_quality_updates",
            "update.notify_only",
        ),
    ),
)


BUILTIN_RULES: dict[str, Rule] = {
    "visual.disable_animations": disable_animations(),
    "visual.classic_context_menu": show_classic_context_menu(),
    "services.disable_search_indexer": disable_search_indexer(),
    "services.disable_diagtrack": disable_diagtrack(),
    "services.disable_xbox": disable_xbox_services(),
    "telemetry.advertising_id": telemetry_advertising_id(),
    "power.ultimate_performance": power_ultimate_performance(),
    "registry.uac_no_delay": uac_no_prompt_for_approved(),
}


def get_preset(name: str) -> Profile | None:
    for p in PRESETS:
        if p.name.lower() == name.lower():
            return p
    return None
