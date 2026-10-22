
import json
import subprocess
from typing import Dict, Any

from .config import SystemConfig
from .fuzzy_engine import FuzzyEvaluationResult
from .wazuh_connector import WazuhSIEMConnector
from .discord_notifier import DiscordWebhookNotifier


class IncidentResponseOrchestrator:

    def __init__(self, config: SystemConfig) -> None:
        self.config = config
        self.wazuh = WazuhSIEMConnector(config.wazuh)
        self.discord = DiscordWebhookNotifier(config.discord)

    def build_remediation_plan(
        self,
        incident_meta: Dict[str, Any],
        fuzzy_result: FuzzyEvaluationResult,
    ) -> Dict[str, Any]:
        os_type = str(incident_meta.get("os_type", "windows")).lower()
        host = str(incident_meta.get("target_host", "UNKNOWN-HOST"))
        user = str(incident_meta.get("target_user", "unknown_user"))
        src_ip = str(incident_meta.get("source_ip", "0.0.0.0"))
        tier = fuzzy_result.response_tier
        risk_score = fuzzy_result.global_cyber_risk_score

        action_map = {
            "MONITOR_LOG": (
                "Monitorizare pasivă: indexare în Wazuh SIEM fără blocarea contului sau a stației."
            ),
            "ALERT_AND_AUDIT": (
                "Audit extins & Alertare SOC: interogare sesiuni Kerberos/SMB active, export artefacte "
                "EventLog/SSSD și notificare Discord + Wazuh Rule Level 8."
            ),
            "CONTAIN_ACCOUNT_AND_HOST": (
                "Izolare Cont & IP: dezactivare cont Active Directory / blocare SSSD, purjare tichete "
                "Kerberos (TGT/TGS) și blocare IP sursă în Firewall (Windows Defender / Linux UFW-IPTables)."
            ),
            "EMERGENCY_DOMAIN_LOCKDOWN": (
                "LOCKDOWN CRITIC TIER-0 AD: dezactivare imediată cont privilegiat, revocare tichete Kerberos "
                "(recomandare dublă rotație krbtgt), izolare host în firewall, blocare replicare DCSync neautorizată "
                "și escaladare maximă Wazuh Level 15."
            ),
        }

        extra_vars = {
            "target_host": host,
            "target_os": os_type,
            "ad_user": user,
            "attacker_ip": src_ip,
            "fuzzy_risk_score": risk_score,
            "response_tier": tier,
            "domain_name": self.config.domain_name,
        }
        extra_vars_json = json.dumps(extra_vars)

        ansible_cmd = (
            f"ansible-playbook -i {self.config.response.ansible_inventory_path} "
            f"{self.config.response.ansible_playbook_path} "
            f"--extra-vars '{extra_vars_json}'"
        )
        if self.config.response.dry_run:
            ansible_cmd += " --check"

        if os_type == "windows":
            script_cmd = (
                f"pwsh -NoProfile -ExecutionPolicy Bypass -File "
                f"{self.config.response.windows_ps1_script_path} "
                f"-Action \"{tier}\" -TargetUser \"{user}\" -SourceIP \"{src_ip}\" "
                f"-TargetHost \"{host}\" -RiskScore {risk_score:.2f}"
            )
            if self.config.response.dry_run:
                script_cmd += " -DryRun"
        else:
            dry_flag = "--dry-run" if self.config.response.dry_run else "--execute"
            script_cmd = (
                f"bash {self.config.response.linux_sh_script_path} "
                f"--action \"{tier}\" --user \"{user}\" --src-ip \"{src_ip}\" "
                f"--host \"{host}\" --risk-score \"{risk_score:.2f}\" {dry_flag}"
            )

        return {
            "response_tier": tier,
            "os_type": os_type,
            "action_summary": action_map.get(tier, "Acțiune standard de monitorizare."),
            "ansible_command": ansible_cmd,
            "script_command": script_cmd,
            "extra_vars": extra_vars,
            "wazuh_delegated_decision": self.config.response.wazuh_decides_active_response,
        }

    def execute_local_script_if_enabled(self, remediation_plan: Dict[str, Any]) -> Dict[str, Any]:
        tier = remediation_plan.get("response_tier", "MONITOR_LOG")
        if tier == "MONITOR_LOG":
            return {"executed": False, "mode": "skipped_monitor_only", "output": ""}

        extra = remediation_plan.get("extra_vars", {})
        cmd = [
            "bash",
            str(self.config.response.linux_sh_script_path),
            "--action",
            str(tier),
            "--user",
            str(extra.get("ad_user", "unknown")),
            "--src-ip",
            str(extra.get("attacker_ip", "0.0.0.0")),
            "--host",
            str(extra.get("target_host", "localhost")),
            "--risk-score",
            f"{float(extra.get('fuzzy_risk_score', 0.0)):.2f}",
            "--dry-run" if self.config.response.dry_run else "--execute",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
            return {
                "executed": True,
                "mode": "dry_run" if self.config.response.dry_run else "active",
                "return_code": proc.returncode,
                "output": proc.stdout.strip(),
            }
        except Exception as exc:
            return {
                "executed": False,
                "mode": "error",
                "output": str(exc),
            }

    def handle_incident(
        self,
        incident_meta: Dict[str, Any],
        fuzzy_result: FuzzyEvaluationResult,
    ) -> Dict[str, Any]:
        plan = self.build_remediation_plan(incident_meta, fuzzy_result)
        wazuh_report = self.wazuh.report_fuzzy_decision_to_wazuh(incident_meta, fuzzy_result, plan)
        discord_report = self.discord.send_alert(incident_meta, fuzzy_result, plan)
        script_exec = self.execute_local_script_if_enabled(plan)

        return {
            "remediation_plan": plan,
            "wazuh_report": wazuh_report,
            "discord_report": discord_report,
            "script_execution": script_exec,
        }
