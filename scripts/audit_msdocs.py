"""Проверяет какие правила не имеют ms_doc_url и где странные URL."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from win11opt.rules.loader import load_all  # noqa: E402

EXPECTED_URLS = {
    # power
    "power.ultimate_performance": "https://learn.microsoft.com/en-us/windows-hardware/customize/power-settings/configure-processor-power-management",
    "power.disable_hibernation": "https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options",
    # ui
    "ui.instant_menu": "https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa",
    "ui.instant_tooltips": "https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa",
    "ui.no_cortana": "https://learn.microsoft.com/en-us/windows/privacy/manage-connections-from-windows-10-to-microsoft-services",
    "ui.no_lockscreen": "https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/local-accounts",
    # visual
    "visual.disable_animations": "https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa",
    "visual.classic_context_menu": "https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/microsoft-windows-shell-setup-startmenu",
    # explorer
    "explorer.show_extensions": "https://learn.microsoft.com/en-us/windows/win32/shell/folder-options",
    "explorer.show_full_path_in_title": "https://learn.microsoft.com/en-us/windows/win32/shell/folder-options",
    "explorer.show_status_bar": "https://learn.microsoft.com/en-us/windows/win32/shell/folder-options",
    "explorer.launch_to_this_pc": "https://learn.microsoft.com/en-us/windows/win32/shell/folder-options",
    # services
    "services.disable_diagtrack": "https://learn.microsoft.com/en-us/windows/privacy/manage-connections-from-windows-10-to-microsoft-services",
    "services.disable_search_indexer": "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/listservices",
    "services.disable_xbox": "https://learn.microsoft.com/en-us/gaming/gaming-services/",
    # gaming
    "gaming.disable_gamebar": "https://learn.microsoft.com/en-us/gaming/game-bar-overview",
    "gaming.disable_xbox_gamebar_hotkey": "https://learn.microsoft.com/en-us/gaming/game-bar-overview",
    # onedrive
    "onedrive.disable_autostart": "https://learn.microsoft.com/en-us/onedrive/turn-on-disable-onedrive",
    "onedrive.disable_startup": "https://learn.microsoft.com/en-us/onedrive/turn-on-disable-onedrive",
    # debloat
    "debloat.remove_xbox_apps": "https://learn.microsoft.com/en-us/windows/application-management/remove-appxpackage",
    "debloat.remove_bing_apps": "https://learn.microsoft.com/en-us/windows/application-management/remove-appxpackage",
    "debloat.remove_help_apps": "https://learn.microsoft.com/en-us/windows/application-management/remove-appxpackage",
    "debloat.remove_apps_duplicates": "https://learn.microsoft.com/en-us/windows/application-management/remove-appxpackage",
    # defender
    "defender.disable_cloud_protection": "https://learn.microsoft.com/en-us/defender-endpoint/cloud-protection-microsoft-defender-antivirus",
    "defender.disable_smart_screen": "https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/access-control",
    "defender.disable_mp_telemetry": "https://learn.microsoft.com/en-us/defender-endpoint/report-monitor-microsoft-defender-antivirus",
    # update
    "update.defer_feature_updates": "https://learn.microsoft.com/en-us/windows/deployment/update/waas-wu-settings",
    "update.defer_quality_updates": "https://learn.microsoft.com/en-us/windows/deployment/update/waas-wu-settings",
    "update.notify_only": "https://learn.microsoft.com/en-us/windows/deployment/update/waas-wu-settings",
    "update.disable_driver_search": "https://learn.microsoft.com/en-us/windows/deployment/update/waas-wu-settings",
    # telemetry
    "telemetry.advertising_id": "https://learn.microsoft.com/en-us/windows/privacy/advertising-id",
    "telemetry.disable_ceip": "https://learn.microsoft.com/en-us/windows/privacy/configure-windows-diagnostic-data-in-your-organization",
    "telemetry.disable_activity_history": "https://learn.microsoft.com/en-us/windows/privacy/Windows-10-activity-history",
    "telemetry.disable_tailored_experiences": "https://learn.microsoft.com/en-us/windows/privacy/enhanced-diagnostic-data",
    "telemetry.disable_feedback_frequency": "https://learn.microsoft.com/en-us/windows/privacy/feedback-diagnostics",
    # power (already in power)
    # network
    "network.disable_nagle": "https://learn.microsoft.com/en-us/windows/win32/winsock/ipproto-tcp",
    "network.disable_throttling": "https://learn.microsoft.com/en-us/windows-hardware/customize/power-settings/configure-processor-power-management",
    "network.disable_gaming_qos": "https://learn.microsoft.com/en-us/windows-server/networking/technologies/qos/qos-policy",
    # ntfs
    "ntfs.disable_last_access_time": "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil",
    "ntfs.disable_8dot3_names": "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-8dot3name",
    "ntfs.disable_short_name_creation": "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil-8dot3name",
    # registry
    "registry.uac_no_delay": "https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/user-account-control",
    # tasks
    "tasks.disable_telemetry": "https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/",
    "tasks.disable_xbox_related": "https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/",
    "tasks.disable_fehcache": "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/fsutil",
    # storage
    "storage.enable_storage_sense": "https://learn.microsoft.com/en-us/windows/manage-storage-senses",
    "storage.disable_delivery_optimization": "https://learn.microsoft.com/en-us/windows/deployment/do/waas-delivery-optimization",
    "storage.disable_storage_sense_temp": "https://learn.microsoft.com/en-us/windows/manage-storage-senses",
    # appcompat
    "appcompat.disable_pca_engine": "https://learn.microsoft.com/en-us/windows-security/identity-protection/access-control/application-control",
    "appcompat.disable_steps_recorder": "https://learn.microsoft.com/en-us/windows/client-management/record-steps-to-reproduce-a-problem",
    "appcompat.disable_windows_suggestions": "https://learn.microsoft.com/en-us/windows/privacy/Windows-10-privacy-content-delivery-manager",
    "appcompat.disable_copilot": "https://learn.microsoft.com/en-us/copilot/overview",
}


def main():
    rules = load_all()
    missing = []
    for rid, expected in EXPECTED_URLS.items():
        if rid not in rules:
            print(f"UNKNOWN: {rid}")
            continue
        rule = rules[rid]
        if not rule.ms_doc_url:
            missing.append((rid, expected))
        elif rule.ms_doc_url != expected:
            print(f"DIFFER: {rid}: have={rule.ms_doc_url} expect={expected}")
    print(f"\nMissing ms_doc_url: {len(missing)}")
    for rid, url in missing:
        print(f"  {rid} -> {url}")


if __name__ == "__main__":
    main()
