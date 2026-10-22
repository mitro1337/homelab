
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


CRITICAL_SYSTEMS_ALLOWLIST: Set[str] = {
    "dc01", "dc01.corp.cyberlab.local",
    "dc02", "dc02.corp.cyberlab.local",
    "proxmox", "pve.corp.cyberlab.local",
    "wazuh-manager", "opnsense.corp.cyberlab.local"
}

CRITICAL_ACCOUNTS_ALLOWLIST: Set[str] = {
    "krbtgt", "administrator", "domain admin",
    "breakglass", "emergency_admin",
    "svc_wazuh", "svc_dns", "svc_dhcp"
}


@dataclass
class PolicyDecision:
    allowed: bool
    mode: str  # "SIMULATION" sau "ENFORCED"
    requires_human_approval: bool
    blocked_by_safety_rule: bool
    safety_rule_name: Optional[str]
    proposed_action: str
    reversibility_plan: str
    audit_id: str
    timestamp: str
    reason: str


class ResponsePolicyEngine:

    def __init__(
        self,
        simulation_mode: bool = True,
        require_human_approval: bool = True,
        cooldown_seconds: int = 300,
        audit_log_path: Optional[Path] = None
    ) -> None:
        self.simulation_mode = simulation_mode
        self.require_human_approval = require_human_approval
        self.cooldown_seconds = cooldown_seconds
        self.audit_log_path = audit_log_path or Path("reports/experiment/policy_audit.jsonl")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        # Istoric acțiuni pentru limitarea repetării: key -> last_timestamp
        self._action_history: Dict[str, datetime] = {}

    def evaluate_action_policy(
        self,
        risk_score: float,
        risk_level: str,
        target_user: str,
        target_host: str,
        has_missing_data: bool = False,
        operator_approved: bool = False
    ) -> PolicyDecision:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        audit_id = f"POL-{int(now.timestamp() * 1000)}"

        clean_user = target_user.lower().strip()
        clean_host = target_host.lower().strip()

        # Determinarea acțiunii propuse conform politicii din Secțiunea 8
        if risk_level == "Critic":
            proposed_action = "CONTAIN_AND_ISOLATE (Blocare cont + Izolare endpoint în firewall)"
            reversibility_plan = (
                f"Rollback: Enable-ADAccount -Identity '{clean_user}'; "
                f"Remove-NetFirewallRule -DisplayName 'AD_Fuzzy_Block_{clean_host}'"
            )
        elif risk_level == "Ridicat":
            proposed_action = "PROPOSE_CONTAINMENT (Revocare tichete Kerberos + Notificare SOC)"
            reversibility_plan = f"Rollback: klist purge; Re-autentificare utilizator '{clean_user}'"
        elif risk_level == "Mediu":
            proposed_action = "ALERT_AND_ENRICH (Colectare context suplimentar + Alertare)"
            reversibility_plan = "N/A - Acțiune non-distructivă de monitorizare"
        else:
            proposed_action = "LOG_AND_MONITOR (Înregistrare pasivă în Wazuh)"
            reversibility_plan = "N/A - Acțiune pasivă"

        # 1. Protectie Fail-Safe: daca datele sunt incomplete, NU se aplica actiuni distructive
        if has_missing_data and risk_level in ("Ridicat", "Critic"):
            decision = PolicyDecision(
                allowed=False,
                mode="SIMULATION" if self.simulation_mode else "BLOCKED",
                requires_human_approval=True,
                blocked_by_safety_rule=True,
                safety_rule_name="SAFETY_FAIL_SAFE_MISSING_DATA",
                proposed_action="FALLBACK_LOG_AND_AUDIT",
                reversibility_plan="N/A",
                audit_id=audit_id,
                timestamp=now_iso,
                reason="Datele de intrare sunt incomplete. S-a activat mecanismul fail-safe pentru prevenirea blocării nejustificate."
            )
            self._log_audit(decision)
            return decision

        # 2. Protectie Allowlist Sisteme Critice (Domain Controllers etc.)
        if clean_host in CRITICAL_SYSTEMS_ALLOWLIST and risk_level in ("Ridicat", "Critic"):
            decision = PolicyDecision(
                allowed=False,
                mode="SIMULATION" if self.simulation_mode else "BLOCKED",
                requires_human_approval=True,
                blocked_by_safety_rule=True,
                safety_rule_name="SAFETY_CRITICAL_SYSTEM_ALLOWLIST",
                proposed_action="ALERT_ADMIN_ONLY (Izolarea automată a sistemului critic este interzisă)",
                reversibility_plan="N/A",
                audit_id=audit_id,
                timestamp=now_iso,
                reason=f"Sistemul țintă '{clean_host}' este pe lista sistemelor critice protejate (Tier-0). Izolarea automată este blocată."
            )
            self._log_audit(decision)
            return decision

        # 3. Protectie Allowlist Conturi Critice (krbtgt, admin, servicii)
        if any(ca in clean_user for ca in CRITICAL_ACCOUNTS_ALLOWLIST) and risk_level in ("Ridicat", "Critic"):
            decision = PolicyDecision(
                allowed=False,
                mode="SIMULATION" if self.simulation_mode else "BLOCKED",
                requires_human_approval=True,
                blocked_by_safety_rule=True,
                safety_rule_name="SAFETY_CRITICAL_ACCOUNT_ALLOWLIST",
                proposed_action="SOC_ESCALATION_ONLY (Blocarea automată a contului critic este interzisă)",
                reversibility_plan="N/A",
                audit_id=audit_id,
                timestamp=now_iso,
                reason=f"Contul țintă '{clean_user}' este un cont de sistem / domeniu critic protejat. Blocarea automată necesită decizie umană directă."
            )
            self._log_audit(decision)
            return decision

        # 4. Limitarea repetarii (Cooldown / De-duplicare)
        action_key = f"{clean_user}:{clean_host}:{proposed_action}"
        last_time = self._action_history.get(action_key)
        if last_time and (now - last_time).total_seconds() < self.cooldown_seconds:
            decision = PolicyDecision(
                allowed=False,
                mode="SUPPRESSED",
                requires_human_approval=False,
                blocked_by_safety_rule=True,
                safety_rule_name="SAFETY_RATE_LIMIT_COOLDOWN",
                proposed_action="SUPPRESSED_DUPLICATE",
                reversibility_plan="N/A",
                audit_id=audit_id,
                timestamp=now_iso,
                reason=f"Acțiunea a fost deja executată/propusă recent pentru '{action_key}'. Cooldown activ."
            )
            self._log_audit(decision)
            return decision

        # 5. Verificare Aprobare Umana pentru actiuni de contentie
        if risk_level in ("Ridicat", "Critic") and self.require_human_approval and not operator_approved:
            decision = PolicyDecision(
                allowed=False,
                mode="AWAITING_HUMAN_APPROVAL",
                requires_human_approval=True,
                blocked_by_safety_rule=False,
                safety_rule_name=None,
                proposed_action=proposed_action,
                reversibility_plan=reversibility_plan,
                audit_id=audit_id,
                timestamp=now_iso,
                reason="Politica necesită aprobare umană explicită înainte de executarea oricărei acțiuni distructive de contenție."
            )
            self._action_history[action_key] = now
            self._log_audit(decision)
            return decision

        # 6. Modul de Simulare (Dry-Run activ)
        if self.simulation_mode:
            decision = PolicyDecision(
                allowed=True,
                mode="SIMULATION",
                requires_human_approval=False,
                blocked_by_safety_rule=False,
                safety_rule_name=None,
                proposed_action=f"[DRY-RUN] {proposed_action}",
                reversibility_plan=reversibility_plan,
                audit_id=audit_id,
                timestamp=now_iso,
                reason="Acțiunea este validată de politică, dar executată exclusiv în mod simulare (Dry-Run), fără impact operațional."
            )
            self._action_history[action_key] = now
            self._log_audit(decision)
            return decision

        # 7. Actiune permisa si autorizata pentru executie
        decision = PolicyDecision(
            allowed=True,
            mode="ENFORCED",
            requires_human_approval=False,
            blocked_by_safety_rule=False,
            safety_rule_name=None,
            proposed_action=proposed_action,
            reversibility_plan=reversibility_plan,
            audit_id=audit_id,
            timestamp=now_iso,
            reason="Toate politicile și măsurile de siguranță au fost validate. Acțiunea este autorizată."
        )
        self._action_history[action_key] = now
        self._log_audit(decision)
        return decision

    def _log_audit(self, decision: PolicyDecision) -> None:
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(decision.__dict__, ensure_ascii=False) + "\n")
        except Exception:
            pass
