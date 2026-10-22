
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import numpy as np
import pandas as pd


REFERENCE_SCENARIOS: List[Dict[str, Any]] = [
    {
        "event_id": "AD-SIM-001",
        "scenario_name": "Activitate Normală Utilizator Standard (Workstation)",
        "os_type": "windows",
        "target_host": "WS-CONTAB01.CORP.CYBERLAB.LOCAL",
        "target_user": "ion.popescu",
        "source_ip": "192.168.64.51",
        "windows_event_ids": "4624, 5140",
        "mitre_tactic": "None (Baseline)",
        "mitre_technique": "N/A - Legitimate Domain Activity",
        "failed_logons": 2.0,
        "kerberos_anomaly": 5.0,
        "privilege_level": 1.5,
        "sensitive_data_access": 10.0,
        "lateral_process_anomaly": 4.0,
        "context_anomaly": 1.0,
        "asset_criticality": 2.0,
    },
    {
        "event_id": "AD-SIM-002",
        "scenario_name": "Password Spraying & Brute-Force pe Conturi Domeniu",
        "os_type": "windows",
        "target_host": "WS-HR02.CORP.CYBERLAB.LOCAL",
        "target_user": "elena.ionescu",
        "source_ip": "192.168.64.188",
        "windows_event_ids": "4625, 4771, 4740",
        "mitre_tactic": "Credential Access",
        "mitre_technique": "T1110.003 - Password Spraying / Brute Force",
        "failed_logons": 68.0,
        "kerberos_anomaly": 35.0,
        "privilege_level": 3.5,
        "sensitive_data_access": 18.0,
        "lateral_process_anomaly": 25.0,
        "context_anomaly": 5.5,
        "asset_criticality": 3.5,
    },
    {
        "event_id": "AD-SIM-003",
        "scenario_name": "Atac Kerberoasting pe Cont de Serviciu SQL (RC4 0x17 TGS)",
        "os_type": "windows",
        "target_host": "SQL-PROD01.CORP.CYBERLAB.LOCAL",
        "target_user": "svc_mssql_prod",
        "source_ip": "192.168.64.112",
        "windows_event_ids": "4769 (Encryption 0x17), 4624",
        "mitre_tactic": "Credential Access",
        "mitre_technique": "T1558.003 - Steal or Forge Kerberos Tickets: Kerberoasting",
        "failed_logons": 14.0,
        "kerberos_anomaly": 82.0,
        "privilege_level": 6.5,
        "sensitive_data_access": 48.0,
        "lateral_process_anomaly": 64.0,
        "context_anomaly": 6.8,
        "asset_criticality": 7.0,
    },
    {
        "event_id": "AD-SIM-004",
        "scenario_name": "Pass-the-Hash (NTLM LogonType 3) & Mișcare Laterală PsExec/WMI",
        "os_type": "windows",
        "target_host": "SRV-FILESHARE01.CORP.CYBERLAB.LOCAL",
        "target_user": "adm_workstation_support",
        "source_ip": "192.168.64.145",
        "windows_event_ids": "4624 (LogonType=3 NTLM), 4672, 4688, 7045",
        "mitre_tactic": "Lateral Movement / Defense Evasion",
        "mitre_technique": "T1550.002 - Use Alternate Authentication Material: Pass the Hash",
        "failed_logons": 28.0,
        "kerberos_anomaly": 74.0,
        "privilege_level": 7.8,
        "sensitive_data_access": 68.0,
        "lateral_process_anomaly": 85.0,
        "context_anomaly": 7.5,
        "asset_criticality": 6.8,
    },
    {
        "event_id": "AD-SIM-005",
        "scenario_name": "Linux AD Node Compromise: SSSD Keytab Dump & Kerberos Cache Abuse",
        "os_type": "linux",
        "target_host": "cyber-node01",
        "target_user": "svc_linux_ansible",
        "source_ip": "192.168.64.210",
        "windows_event_ids": "pam_sss(sshd:auth), krb5cc_0 dump, auditd EXECVE",
        "mitre_tactic": "Credential Access / Privilege Escalation",
        "mitre_technique": "T1558.004 / T1003.008 - Linux Domain Keytab & SSSD Credential Dumping",
        "failed_logons": 45.0,
        "kerberos_anomaly": 70.0,
        "privilege_level": 7.2,
        "sensitive_data_access": 62.0,
        "lateral_process_anomaly": 78.0,
        "context_anomaly": 7.0,
        "asset_criticality": 6.5,
    },
    {
        "event_id": "AD-SIM-006",
        "scenario_name": "Exfiltrare Masivă Date SMB & Ransomware Pre-Encryption pe SYSVOL",
        "os_type": "windows",
        "target_host": "SRV-FINANCE-VAULT.CORP.CYBERLAB.LOCAL",
        "target_user": "adm_fin_operator",
        "source_ip": "192.168.64.199",
        "windows_event_ids": "5145 (SYSVOL/Finance$), 4663, 4104 (PowerShell Encoded)",
        "mitre_tactic": "Exfiltration / Impact",
        "mitre_technique": "T1048 / T1486 - Exfiltration Over SMB & Data Encrypted for Impact",
        "failed_logons": 18.0,
        "kerberos_anomaly": 58.0,
        "privilege_level": 7.5,
        "sensitive_data_access": 94.0,
        "lateral_process_anomaly": 88.0,
        "context_anomaly": 8.5,
        "asset_criticality": 8.2,
    },
    {
        "event_id": "AD-SIM-007",
        "scenario_name": "Atac Critic DCSync & Golden Ticket pe Domain Controller (Tier-0)",
        "os_type": "windows",
        "target_host": "DC01.CORP.CYBERLAB.LOCAL",
        "target_user": "krbtgt / DomainAdmin_Backup",
        "source_ip": "192.168.64.250",
        "windows_event_ids": "4662 (DS-Replication-Get-Changes-All), 4768, 4672, 5136",
        "mitre_tactic": "Credential Access / Persistence (Domain Dominance)",
        "mitre_technique": "T1003.006 & T1558.001 - DCSync & Golden Ticket on Tier-0 DC",
        "failed_logons": 35.0,
        "kerberos_anomaly": 96.0,
        "privilege_level": 9.8,
        "sensitive_data_access": 97.0,
        "lateral_process_anomaly": 95.0,
        "context_anomaly": 9.5,
        "asset_criticality": 10.0,
    },
    {
        "event_id": "AD-SIM-008",
        "scenario_name": "Audit Administrativ Nocturn Autorizat parțial (Anomalie Medie)",
        "os_type": "linux",
        "target_host": "cyber-node02",
        "target_user": "sec_auditor",
        "source_ip": "192.168.64.20",
        "windows_event_ids": "4624, 4672, sudo_audit",
        "mitre_tactic": "Discovery",
        "mitre_technique": "T1087.002 - Account Discovery: Domain Account",
        "failed_logons": 22.0,
        "kerberos_anomaly": 30.0,
        "privilege_level": 5.5,
        "sensitive_data_access": 38.0,
        "lateral_process_anomaly": 32.0,
        "context_anomaly": 5.0,
        "asset_criticality": 5.0,
    },
]


class ActiveDirectoryAttackSimulator:

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def get_reference_scenarios_df(self) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        rows = []
        for idx, sc in enumerate(REFERENCE_SCENARIOS):
            item = dict(sc)
            item["timestamp"] = (now - timedelta(minutes=(len(REFERENCE_SCENARIOS) - idx) * 4)).isoformat()
            rows.append(item)
        return pd.DataFrame(rows)

    def generate_synthetic_stream_df(self, count: int = 25) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        rows = []
        for i in range(count):
            template = dict(REFERENCE_SCENARIOS[i % len(REFERENCE_SCENARIOS)])
            jitter_pct = float(self.rng.normal(0.0, 4.5))
            jitter_10 = float(self.rng.normal(0.0, 0.4))

            template["event_id"] = f"AD-STREAM-{i + 1:03d}"
            template["timestamp"] = (now - timedelta(seconds=(count - i) * 30)).isoformat()
            template["failed_logons"] = round(float(np.clip(template["failed_logons"] + jitter_pct, 0, 100)), 2)
            template["kerberos_anomaly"] = round(float(np.clip(template["kerberos_anomaly"] + jitter_pct, 0, 100)), 2)
            template["privilege_level"] = round(float(np.clip(template["privilege_level"] + jitter_10, 0, 10)), 2)
            template["sensitive_data_access"] = round(
                float(np.clip(template["sensitive_data_access"] + jitter_pct, 0, 100)), 2
            )
            template["lateral_process_anomaly"] = round(
                float(np.clip(template["lateral_process_anomaly"] + jitter_pct, 0, 100)), 2
            )
            template["context_anomaly"] = round(float(np.clip(template["context_anomaly"] + jitter_10, 0, 10)), 2)
            template["asset_criticality"] = round(float(np.clip(template["asset_criticality"] + jitter_10, 0, 10)), 2)
            rows.append(template)

        return pd.DataFrame(rows)
