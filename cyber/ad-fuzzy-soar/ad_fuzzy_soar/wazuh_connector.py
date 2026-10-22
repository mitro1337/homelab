
from datetime import datetime, timezone
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import requests
import urllib3

from .config import WazuhConfig
from .fuzzy_engine import FuzzyEvaluationResult

# Dezactivăm avertismentele TLS self-signed specifice mediilor homelab/Wazuh
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WazuhSIEMConnector:

    def __init__(self, config: WazuhConfig) -> None:
        self.config = config
        self._jwt_token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = self.config.verify_ssl

    def authenticate_manager_api(self) -> Optional[str]:
        auth_url = f"{self.config.manager_url.rstrip('/')}/security/user/authenticate"
        try:
            resp = self.session.post(
                auth_url,
                auth=(self.config.api_user, self.config.api_password),
                timeout=self.config.timeout_seconds,
            )
            resp.raise_for_status()
            payload = resp.json()
            self._jwt_token = payload.get("data", {}).get("token")
            return self._jwt_token
        except requests.RequestException:
            self._jwt_token = None
            return None

    def fetch_active_directory_alerts_df(self, lookback_minutes: int = 30, max_alerts: int = 200) -> pd.DataFrame:
        search_url = f"{self.config.indexer_url.rstrip('/')}/wazuh-alerts-*/_search"
        query_body = {
            "size": max_alerts,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": f"now-{lookback_minutes}m",
                                    "lte": "now",
                                }
                            }
                        }
                    ],
                    "should": [
                        {"match": {"rule.groups": "windows"}},
                        {"match": {"rule.groups": "active_directory"}},
                        {"match": {"rule.groups": "sysmon"}},
                        {"match": {"rule.groups": "pam"}},
                        {"match": {"rule.groups": "sshd"}},
                        {"match": {"rule.groups": "sudo"}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        }

        try:
            resp = self.session.post(
                search_url,
                auth=(self.config.indexer_user, self.config.indexer_password),
                json=query_body,
                timeout=self.config.timeout_seconds,
            )
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            if not hits:
                return pd.DataFrame()
            return self.transform_raw_wazuh_hits_to_df([h.get("_source", {}) for h in hits])
        except requests.RequestException:
            return pd.DataFrame()

    @staticmethod
    def transform_raw_wazuh_hits_to_df(alerts: List[Dict[str, Any]]) -> pd.DataFrame:
        if not alerts:
            return pd.DataFrame()

        raw_rows = []
        for idx, alert in enumerate(alerts):
            agent = alert.get("agent", {})
            rule = alert.get("rule", {})
            win_sys = alert.get("data", {}).get("win", {}).get("system", {})
            win_ev = alert.get("data", {}).get("win", {}).get("eventdata", {})

            event_id_str = str(win_sys.get("eventID", rule.get("id", "0")))
            groups = rule.get("groups", [])
            os_type = "windows" if ("windows" in groups or win_sys) else "linux"
            host = agent.get("name", "UNKNOWN-HOST")
            user = (
                win_ev.get("targetUserName")
                or win_ev.get("subjectUserName")
                or alert.get("data", {}).get("dstuser")
                or "domain_user"
            )
            src_ip = (
                win_ev.get("ipAddress")
                or alert.get("data", {}).get("srcip")
                or agent.get("ip", "192.168.64.100")
            )
            mitre_ids = ", ".join(rule.get("mitre", {}).get("id", ["N/A"]))
            mitre_tactics = ", ".join(rule.get("mitre", {}).get("tactic", ["Unknown"]))
            rule_level = float(rule.get("level", 5))

            # Mapare euristică a EventID-urilor Active Directory către indecșii fuzzy
            failed_logons = 65.0 if event_id_str in {"4625", "4771", "4776", "4740"} else 10.0
            kerb_anom = 80.0 if event_id_str in {"4768", "4769", "4772"} else (55.0 if event_id_str == "4624" else 12.0)
            priv_lvl = 9.0 if any(k in user.lower() for k in ("admin", "krbtgt", "root", "dc")) else (
                6.5 if "svc" in user.lower() else 3.0
            )
            data_acc = 90.0 if event_id_str in {"4662", "5145", "4663"} else 15.0
            lat_proc = min(100.0, rule_level * 6.5) if event_id_str in {"4688", "7045", "4104", "1"} else 20.0
            ctx_anom = min(10.0, rule_level * 0.65)
            asset_crit = 10.0 if "dc" in host.lower() else (7.0 if "srv" in host.lower() or "sql" in host.lower() else 4.0)

            raw_rows.append({
                "event_id": f"WAZUH-{alert.get('id', idx + 1)}",
                "timestamp": alert.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "scenario_name": rule.get("description", "Wazuh SIEM Correlated Event"),
                "os_type": os_type,
                "target_host": host,
                "target_user": user,
                "source_ip": src_ip,
                "windows_event_ids": event_id_str,
                "mitre_tactic": mitre_tactics,
                "mitre_technique": mitre_ids,
                "failed_logons": failed_logons,
                "kerberos_anomaly": kerb_anom,
                "privilege_level": priv_lvl,
                "sensitive_data_access": data_acc,
                "lateral_process_anomaly": lat_proc,
                "context_anomaly": ctx_anom,
                "asset_criticality": asset_crit,
            })

        return pd.DataFrame(raw_rows)

    def report_fuzzy_decision_to_wazuh(
        self,
        incident_meta: Dict[str, Any],
        fuzzy_result: FuzzyEvaluationResult,
        remediation_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        wazuh_event_payload = {
            "integration": "ad_fuzzy_soar",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": incident_meta.get("event_id", "UNKNOWN"),
            "scenario_name": incident_meta.get("scenario_name", "AD Security Event"),
            "target": {
                "os_type": incident_meta.get("os_type", "windows"),
                "host": incident_meta.get("target_host", "UNKNOWN"),
                "user": incident_meta.get("target_user", "UNKNOWN"),
                "source_ip": incident_meta.get("source_ip", "0.0.0.0"),
                "windows_event_ids": incident_meta.get("windows_event_ids", ""),
            },
            "mitre": {
                "tactic": incident_meta.get("mitre_tactic", "Unknown"),
                "technique": incident_meta.get("mitre_technique", "Unknown"),
            },
            "fuzzy_inference": {
                "inputs": fuzzy_result.inputs,
                "identity_risk_score": fuzzy_result.identity_risk_score,
                "data_security_risk_score": fuzzy_result.data_security_risk_score,
                "global_cyber_risk_score": fuzzy_result.global_cyber_risk_score,
                "response_urgency_score": fuzzy_result.response_urgency_score,
                "risk_level": fuzzy_result.risk_level,
                "response_tier": fuzzy_result.response_tier,
                "wazuh_recommended_rule_level": fuzzy_result.wazuh_rule_level,
                "defuzzification_comparison": fuzzy_result.defuzz_comparison,
                "active_rules_summary": fuzzy_result.active_rules_summary,
            },
            "soar_orchestration": {
                "wazuh_decision_authority": True,
                "recommended_action": remediation_plan.get("action_summary", ""),
                "ansible_playbook": remediation_plan.get("ansible_command", ""),
                "script_command": remediation_plan.get("script_command", ""),
            },
        }

        # 1. Salvăm evenimentul în logul JSONL local (compatibil cu Wazuh `<localfile><log_format>json</log_format>`)
        self.config.fallback_events_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.fallback_events_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(wazuh_event_payload, ensure_ascii=False) + "\n")

        # 2. Încercăm transmiterea în timp real prin HTTP API către Wazuh Manager (`POST /events`)
        api_delivered = False
        api_status = "logged_to_local_wazuh_jsonl"

        token = self._jwt_token or self.authenticate_manager_api()
        if token:
            events_url = f"{self.config.manager_url.rstrip('/')}/events"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            try:
                resp = self.session.post(
                    events_url,
                    headers=headers,
                    json={"events": [json.dumps(wazuh_event_payload)]},
                    timeout=self.config.timeout_seconds,
                )
                if resp.status_code in (200, 201):
                    api_delivered = True
                    api_status = f"delivered_to_wazuh_api_http_{resp.status_code}"
                else:
                    api_status = f"wazuh_api_http_{resp.status_code}_fallback_jsonl"
            except requests.RequestException as exc:
                api_status = f"wazuh_api_unreachable ({type(exc).__name__}) -> fallback_jsonl_saved"

        return {
            "delivered_via_api": api_delivered,
            "status": api_status,
            "local_jsonl_path": str(self.config.fallback_events_log),
            "payload": wazuh_event_payload,
        }
