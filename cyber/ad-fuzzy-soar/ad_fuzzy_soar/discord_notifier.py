
from datetime import datetime, timezone
import json
from typing import Dict, Any
import requests

from .config import DiscordConfig
from .fuzzy_engine import FuzzyEvaluationResult


RISK_COLOR_MAP = {
    "LOW": 0x2ECC71,       # Verde
    "MEDIUM": 0xF1C40F,    # Galben / Portocaliu deschis
    "HIGH": 0xE67E22,      # Portocaliu intens
    "CRITICAL": 0xE74C3C,  # Roșu critic
}


class DiscordWebhookNotifier:

    def __init__(self, config: DiscordConfig) -> None:
        self.config = config

    def build_discord_payload(
        self,
        incident_meta: Dict[str, Any],
        fuzzy_result: FuzzyEvaluationResult,
        remediation_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        color = RISK_COLOR_MAP.get(fuzzy_result.risk_level, 0x95A5A6)
        os_badge = "🪟 Windows AD" if incident_meta.get("os_type") == "windows" else "🐧 Linux AD Node"

        rules_text = "\n".join(f"• `{r}`" for r in fuzzy_result.active_rules_summary[:6]) or "N/A"
        defuzz_text = " | ".join(
            f"**{k}**: `{v:.1f}`" for k, v in fuzzy_result.defuzz_comparison.items()
        )

        embed = {
            "title": (
                f"🚨 [{fuzzy_result.risk_level}] AD-Fuzzy-SOAR Alert — "
                f"{incident_meta.get('scenario_name', 'Security Event')}"
            ),
            "description": (
                f"Sistemul de inferență **Mamdani Multi-Strat** a evaluat evenimentul "
                f"`{incident_meta.get('event_id')}` și a raportat decizia către **Wazuh SIEM**."
            ),
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fields": [
                {
                    "name": "🎯 Țintă Active Directory / Nod",
                    "value": (
                        f"**OS:** {os_badge}\n"
                        f"**Host:** `{incident_meta.get('target_host')}`\n"
                        f"**Utilizator:** `{incident_meta.get('target_user')}`\n"
                        f"**IP Sursă:** `{incident_meta.get('source_ip')}`"
                    ),
                    "inline": True,
                },
                {
                    "name": "🧮 Scoruri Inferență Fuzzy (0-100)",
                    "value": (
                        f"**Risc Global Cibernetic:** `{fuzzy_result.global_cyber_risk_score:.2f} / 100`\n"
                        f"**Urgență Răspuns SOAR:** `{fuzzy_result.response_urgency_score:.2f} / 100`\n"
                        f"**Risc Identitate (L1):** `{fuzzy_result.identity_risk_score:.2f}`\n"
                        f"**Risc Date & Lateral (L2):** `{fuzzy_result.data_security_risk_score:.2f}`"
                    ),
                    "inline": True,
                },
                {
                    "name": "🛡️ MITRE ATT&CK & EventIDs",
                    "value": (
                        f"**Tactică:** `{incident_meta.get('mitre_tactic')}`\n"
                        f"**Tehnică:** `{incident_meta.get('mitre_technique')}`\n"
                        f"**Event IDs:** `{incident_meta.get('windows_event_ids')}`\n"
                        f"**Wazuh Rule Level:** `Level {fuzzy_result.wazuh_rule_level}`"
                    ),
                    "inline": False,
                },
                {
                    "name": "🔍 Termeni Lingvistici Activați (XAI)",
                    "value": rules_text,
                    "inline": False,
                },
                {
                    "name": "📐 Comparație Metode Defuzzificare",
                    "value": defuzz_text,
                    "inline": False,
                },
                {
                    "name": "⚡ Răspuns la Incidente (Wazuh SIEM + Ansible + PS1/SH)",
                    "value": (
                        f"**Nivel Răspuns:** `{fuzzy_result.response_tier}`\n"
                        f"**Acțiune:** {remediation_plan.get('action_summary')}\n"
                        f"**Playbook Ansible:** `{remediation_plan.get('ansible_command')}`\n"
                        f"**Script Nativ:** `{remediation_plan.get('script_command')}`"
                    ),
                    "inline": False,
                },
            ],
            "footer": {
                "text": "AD-Fuzzy-SOAR Engine • scikit-fuzzy + Wazuh SIEM + Ansible Automation"
            },
        }

        return {
            "username": self.config.username,
            "avatar_url": self.config.avatar_url,
            "embeds": [embed],
        }

    def send_alert(
        self,
        incident_meta: Dict[str, Any],
        fuzzy_result: FuzzyEvaluationResult,
        remediation_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        if fuzzy_result.global_cyber_risk_score < self.config.min_risk_score_to_alert:
            return {
                "sent": False,
                "status": f"skipped_below_threshold ({fuzzy_result.global_cyber_risk_score:.1f} < {self.config.min_risk_score_to_alert})",
            }

        payload = self.build_discord_payload(incident_meta, fuzzy_result, remediation_plan)

        # Salvăm local payload-ul JSONL pentru audit și demonstrație
        self.config.fallback_alerts_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.fallback_alerts_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

        if not self.config.webhook_url.strip():
            return {
                "sent": False,
                "status": "webhook_url_not_configured_saved_to_local_jsonl",
                "local_jsonl_path": str(self.config.fallback_alerts_log),
            }

        try:
            resp = requests.post(
                self.config.webhook_url.strip(),
                json=payload,
                timeout=8,
            )
            if resp.status_code in (200, 204):
                return {
                    "sent": True,
                    "status": f"discord_webhook_delivered_http_{resp.status_code}",
                    "local_jsonl_path": str(self.config.fallback_alerts_log),
                }
            return {
                "sent": False,
                "status": f"discord_webhook_http_{resp.status_code}",
                "local_jsonl_path": str(self.config.fallback_alerts_log),
            }
        except requests.RequestException as exc:
            return {
                "sent": False,
                "status": f"discord_webhook_error ({type(exc).__name__})_saved_to_jsonl",
                "local_jsonl_path": str(self.config.fallback_alerts_log),
            }
