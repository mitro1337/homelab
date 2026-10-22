
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class WazuhConfig:
    manager_url: str = field(
        default_factory=lambda: os.getenv("WAZUH_MANAGER_URL", "https://127.0.0.1:55000")
    )
    indexer_url: str = field(
        default_factory=lambda: os.getenv("WAZUH_INDEXER_URL", "https://127.0.0.1:9200")
    )
    api_user: str = field(
        default_factory=lambda: os.getenv("WAZUH_API_USER", "wazuh-wui")
    )
    api_password: str = field(
        default_factory=lambda: os.getenv("WAZUH_API_PASSWORD", "wazuh-wui")
    )
    indexer_user: str = field(
        default_factory=lambda: os.getenv("WAZUH_INDEXER_USER", "admin")
    )
    indexer_password: str = field(
        default_factory=lambda: os.getenv("WAZUH_INDEXER_PASSWORD", "admin")
    )
    verify_ssl: bool = field(
        default_factory=lambda: os.getenv("WAZUH_VERIFY_SSL", "false").lower() == "true"
    )
    timeout_seconds: int = 10
    # Calea locală unde se salvează evenimentele JSON dacă Wazuh Manager este offline/în mod lab local
    fallback_events_log: Path = field(
        default_factory=lambda: BASE_DIR / "reports" / "wazuh_fuzzy_events.jsonl"
    )


@dataclass
class DiscordConfig:
    webhook_url: str = field(
        default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", "")
    )
    username: str = "AD-Fuzzy-SOAR Sentinel"
    avatar_url: str = "https://cdn-icons-png.flaticon.com/512/2092/2092663.png"
    min_risk_score_to_alert: float = 40.0
    fallback_alerts_log: Path = field(
        default_factory=lambda: BASE_DIR / "reports" / "discord_alerts_payloads.jsonl"
    )


@dataclass
class ResponseConfig:
    dry_run: bool = field(
        default_factory=lambda: os.getenv("FUZZY_SOAR_DRY_RUN", "true").lower() == "true"
    )
    wazuh_decides_active_response: bool = True
    ansible_playbook_path: Path = field(
        default_factory=lambda: BASE_DIR / "ansible" / "playbooks" / "ad_incident_response.yml"
    )
    ansible_inventory_path: Path = field(
        default_factory=lambda: BASE_DIR / "ansible" / "inventory.yml"
    )
    windows_ps1_script_path: Path = field(
        default_factory=lambda: BASE_DIR / "scripts" / "windows" / "ad_response.ps1"
    )
    linux_sh_script_path: Path = field(
        default_factory=lambda: BASE_DIR / "scripts" / "linux" / "linux_ad_response.sh"
    )
    reports_dir: Path = field(default_factory=lambda: BASE_DIR / "reports")
    plots_dir: Path = field(default_factory=lambda: BASE_DIR / "reports" / "plots")


@dataclass
class SystemConfig:
    domain_name: str = "CORP.CYBERLAB.LOCAL"
    wazuh: WazuhConfig = field(default_factory=WazuhConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    response: ResponseConfig = field(default_factory=ResponseConfig)

    def ensure_directories(self) -> None:
        self.response.reports_dir.mkdir(parents=True, exist_ok=True)
        self.response.plots_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "SystemConfig":
        cfg = cls()
        if not yaml_path.exists():
            return cfg
        with open(yaml_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f) or {}
        if "domain_name" in data:
            cfg.domain_name = str(data["domain_name"])
        if "wazuh" in data and isinstance(data["wazuh"], dict):
            for k, v in data["wazuh"].items():
                if hasattr(cfg.wazuh, k):
                    setattr(cfg.wazuh, k, v)
        if "discord" in data and isinstance(data["discord"], dict):
            for k, v in data["discord"].items():
                if hasattr(cfg.discord, k):
                    setattr(cfg.discord, k, v)
        if "response" in data and isinstance(data["response"], dict):
            for k, v in data["response"].items():
                if hasattr(cfg.response, k):
                    setattr(cfg.response, k, v)
        return cfg
