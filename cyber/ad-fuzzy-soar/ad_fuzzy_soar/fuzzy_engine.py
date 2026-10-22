
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


@dataclass
class FuzzyEvaluationResult:
    # Intrări brute
    inputs: Dict[str, float]
    # Scoruri intermediare și finale defuzzificate (Centroid)
    identity_risk_score: float
    data_security_risk_score: float
    global_cyber_risk_score: float
    response_urgency_score: float
    # Clasificare lingvistică și nivel de severitate
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    response_tier: str  # MONITOR_LOG, ALERT_AND_AUDIT, CONTAIN_ACCOUNT_AND_HOST, EMERGENCY_DOMAIN_LOCKDOWN
    wazuh_rule_level: int  # 3..15 (compatibil cu Wazuh SIEM)
    # Gradele de apartenență (Membership Degrees mu) pentru explicabilitate (XAI)
    memberships: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Compararea metodelor de defuzzificare pe ieșirea globală
    defuzz_comparison: Dict[str, float] = field(default_factory=dict)
    # Explicație tehnică a regulilor activate
    active_rules_summary: List[str] = field(default_factory=list)


class ActiveDirectoryFuzzyEngine:

    def __init__(self, defuzzify_method: str = "centroid") -> None:
        self.defuzzify_method = defuzzify_method

        # Universuri de discurs (Universe of Discourse)
        self.u_pct = np.linspace(0, 100, 201)   # [0.0, 0.5, ..., 100.0]
        self.u_scale10 = np.linspace(0, 10, 101)  # [0.0, 0.1, ..., 10.0]

        self._build_layer1_identity_fis()
        self._build_layer2_data_lateral_fis()
        self._build_layer3_master_soar_fis()

    # =========================================================================
    # SUB-SISTEMUL 1: Risc de Identitate și Autentificare Active Directory
    # =========================================================================
    def _build_layer1_identity_fis(self) -> None:
        self.failed_logons = ctrl.Antecedent(self.u_pct, "failed_logons")
        self.kerberos_anomaly = ctrl.Antecedent(self.u_pct, "kerberos_anomaly")
        self.privilege_level = ctrl.Antecedent(self.u_scale10, "privilege_level")
        self.identity_risk = ctrl.Consequent(
            self.u_pct, "identity_risk", defuzzify_method=self.defuzzify_method
        )

        # Funcții de apartenență pentru failed_logons [0..100]
        self.failed_logons["normal"] = fuzz.trapmf(self.u_pct, [0, 0, 8, 20])
        self.failed_logons["moderat"] = fuzz.trimf(self.u_pct, [12, 30, 50])
        self.failed_logons["ridicat"] = fuzz.trimf(self.u_pct, [40, 65, 85])
        self.failed_logons["bruteforce_critic"] = fuzz.trapmf(self.u_pct, [70, 88, 100, 100])

        # Funcții de apartenență pentru kerberos_anomaly [0..100]
        self.kerberos_anomaly["benign"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 30])
        self.kerberos_anomaly["suspect"] = fuzz.trimf(self.u_pct, [20, 45, 65])
        self.kerberos_anomaly["kerberoasting_pth"] = fuzz.trimf(self.u_pct, [55, 75, 92])
        self.kerberos_anomaly["golden_ticket"] = fuzz.trapmf(self.u_pct, [82, 92, 100, 100])

        # Funcții de apartenență pentru privilege_level [0..10]
        self.privilege_level["standard_user"] = fuzz.trapmf(self.u_scale10, [0, 0, 2.0, 4.0])
        self.privilege_level["service_account"] = fuzz.trimf(self.u_scale10, [2.5, 5.0, 7.5])
        self.privilege_level["local_admin"] = fuzz.trimf(self.u_scale10, [6.0, 7.5, 9.0])
        self.privilege_level["tier0_domain_admin"] = fuzz.trapmf(self.u_scale10, [8.0, 9.0, 10.0, 10.0])

        # Funcții de apartenență pentru ieșirea identity_risk [0..100]
        self.identity_risk["scazut"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 30])
        self.identity_risk["mediu"] = fuzz.trimf(self.u_pct, [20, 42, 62])
        self.identity_risk["ridicat"] = fuzz.trimf(self.u_pct, [52, 72, 88])
        self.identity_risk["critic"] = fuzz.trapmf(self.u_pct, [80, 90, 100, 100])

        # Baza de reguli Mamdani pentru Sub-sistemul 1
        rules_l1 = [
            # Reguli de bază pentru trafic legitim
            ctrl.Rule(
                self.failed_logons["normal"] & self.kerberos_anomaly["benign"] & self.privilege_level["standard_user"],
                self.identity_risk["scazut"],
            ),
            ctrl.Rule(
                self.failed_logons["normal"] & self.kerberos_anomaly["benign"] & self.privilege_level["service_account"],
                self.identity_risk["scazut"],
            ),
            ctrl.Rule(
                self.failed_logons["normal"] & self.kerberos_anomaly["benign"]
                & (self.privilege_level["local_admin"] | self.privilege_level["tier0_domain_admin"]),
                self.identity_risk["mediu"],
            ),
            # Reguli Brute-Force / Password Spraying
            ctrl.Rule(
                self.failed_logons["moderat"] & self.kerberos_anomaly["benign"]
                & (self.privilege_level["standard_user"] | self.privilege_level["service_account"]),
                self.identity_risk["mediu"],
            ),
            ctrl.Rule(
                self.failed_logons["moderat"] & self.privilege_level["local_admin"],
                self.identity_risk["ridicat"],
            ),
            ctrl.Rule(
                self.failed_logons["moderat"] & self.privilege_level["tier0_domain_admin"],
                self.identity_risk["critic"],
            ),
            ctrl.Rule(
                self.failed_logons["ridicat"] & self.privilege_level["standard_user"],
                self.identity_risk["ridicat"],
            ),
            ctrl.Rule(
                self.failed_logons["ridicat"]
                & (self.privilege_level["service_account"] | self.privilege_level["local_admin"] | self.privilege_level["tier0_domain_admin"]),
                self.identity_risk["critic"],
            ),
            ctrl.Rule(
                self.failed_logons["bruteforce_critic"],
                self.identity_risk["critic"],
            ),
            # Reguli Anomalii Kerberos (Kerberoasting, Pass-the-Hash, Golden Ticket)
            ctrl.Rule(
                self.kerberos_anomaly["suspect"]
                & (self.privilege_level["standard_user"] | self.privilege_level["service_account"]),
                self.identity_risk["mediu"],
            ),
            ctrl.Rule(
                self.kerberos_anomaly["suspect"]
                & (self.privilege_level["local_admin"] | self.privilege_level["tier0_domain_admin"]),
                self.identity_risk["ridicat"],
            ),
            ctrl.Rule(
                self.kerberos_anomaly["kerberoasting_pth"]
                & (self.privilege_level["standard_user"] | self.privilege_level["service_account"]),
                self.identity_risk["ridicat"],
            ),
            ctrl.Rule(
                self.kerberos_anomaly["kerberoasting_pth"]
                & (self.privilege_level["local_admin"] | self.privilege_level["tier0_domain_admin"]),
                self.identity_risk["critic"],
            ),
            ctrl.Rule(
                self.kerberos_anomaly["golden_ticket"],
                self.identity_risk["critic"],
            ),
        ]

        self.l1_ctrl = ctrl.ControlSystem(rules_l1)

    # =========================================================================
    # SUB-SISTEMUL 2: Risc de Securitate a Datelor și Mișcare Laterală
    # =========================================================================
    def _build_layer2_data_lateral_fis(self) -> None:
        self.sensitive_data_access = ctrl.Antecedent(self.u_pct, "sensitive_data_access")
        self.lateral_process_anomaly = ctrl.Antecedent(self.u_pct, "lateral_process_anomaly")
        self.context_anomaly = ctrl.Antecedent(self.u_scale10, "context_anomaly")
        self.data_security_risk = ctrl.Consequent(
            self.u_pct, "data_security_risk", defuzzify_method=self.defuzzify_method
        )

        # Funcții de apartenență pentru sensitive_data_access [0..100]
        self.sensitive_data_access["normal"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 30])
        self.sensitive_data_access["neobisnuit"] = fuzz.trimf(self.u_pct, [20, 45, 65])
        self.sensitive_data_access["acces_masiv_smb"] = fuzz.trimf(self.u_pct, [55, 75, 90])
        self.sensitive_data_access["exfiltrare_dcsync"] = fuzz.trapmf(self.u_pct, [80, 90, 100, 100])

        # Funcții de apartenență pentru lateral_process_anomaly [0..100]
        self.lateral_process_anomaly["benign"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 28])
        self.lateral_process_anomaly["suspect"] = fuzz.trimf(self.u_pct, [20, 45, 68])
        self.lateral_process_anomaly["exploatare_activa"] = fuzz.trimf(self.u_pct, [58, 78, 92])
        self.lateral_process_anomaly["compromitere_totala"] = fuzz.trapmf(self.u_pct, [84, 92, 100, 100])

        # Funcții de apartenență pentru context_anomaly [0..10]
        self.context_anomaly["uzual"] = fuzz.trapmf(self.u_scale10, [0, 0, 2.5, 4.5])
        self.context_anomaly["atipic"] = fuzz.trimf(self.u_scale10, [3.0, 5.5, 8.0])
        self.context_anomaly["extrem"] = fuzz.trapmf(self.u_scale10, [6.5, 8.2, 10.0, 10.0])

        # Funcții de apartenență pentru ieșirea data_security_risk [0..100]
        self.data_security_risk["sigur"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 30])
        self.data_security_risk["vulnerabil"] = fuzz.trimf(self.u_pct, [20, 42, 62])
        self.data_security_risk["pericol_ridicat"] = fuzz.trimf(self.u_pct, [52, 72, 88])
        self.data_security_risk["breach_iminent"] = fuzz.trapmf(self.u_pct, [80, 90, 100, 100])

        rules_l2 = [
            ctrl.Rule(
                self.sensitive_data_access["normal"] & self.lateral_process_anomaly["benign"] & self.context_anomaly["uzual"],
                self.data_security_risk["sigur"],
            ),
            ctrl.Rule(
                self.sensitive_data_access["normal"] & self.lateral_process_anomaly["benign"] & self.context_anomaly["atipic"],
                self.data_security_risk["vulnerabil"],
            ),
            ctrl.Rule(
                self.sensitive_data_access["normal"] & self.lateral_process_anomaly["benign"] & self.context_anomaly["extrem"],
                self.data_security_risk["pericol_ridicat"],
            ),
            # Acces neobișnuit la fișiere / AD Objects
            ctrl.Rule(
                self.sensitive_data_access["neobisnuit"] & self.lateral_process_anomaly["benign"]
                & (self.context_anomaly["uzual"] | self.context_anomaly["atipic"]),
                self.data_security_risk["vulnerabil"],
            ),
            ctrl.Rule(
                self.sensitive_data_access["neobisnuit"] & self.context_anomaly["extrem"],
                self.data_security_risk["pericol_ridicat"],
            ),
            # Acces masiv SMB / Ransomware staging / Exfiltrare / DCSync
            ctrl.Rule(
                self.sensitive_data_access["acces_masiv_smb"] & self.context_anomaly["uzual"],
                self.data_security_risk["pericol_ridicat"],
            ),
            ctrl.Rule(
                self.sensitive_data_access["acces_masiv_smb"]
                & (self.context_anomaly["atipic"] | self.context_anomaly["extrem"] | self.lateral_process_anomaly["suspect"]),
                self.data_security_risk["breach_iminent"],
            ),
            ctrl.Rule(
                self.sensitive_data_access["exfiltrare_dcsync"],
                self.data_security_risk["breach_iminent"],
            ),
            # Procese suspecte și mișcare laterală (PsExec, WMI, Mimikatz, Linux krb5cc)
            ctrl.Rule(
                self.lateral_process_anomaly["suspect"]
                & (self.context_anomaly["uzual"] | self.context_anomaly["atipic"]),
                self.data_security_risk["vulnerabil"],
            ),
            ctrl.Rule(
                self.lateral_process_anomaly["suspect"] & self.context_anomaly["extrem"],
                self.data_security_risk["pericol_ridicat"],
            ),
            ctrl.Rule(
                self.lateral_process_anomaly["exploatare_activa"]
                & (self.sensitive_data_access["normal"] | self.sensitive_data_access["neobisnuit"]),
                self.data_security_risk["pericol_ridicat"],
            ),
            ctrl.Rule(
                self.lateral_process_anomaly["exploatare_activa"]
                & (self.sensitive_data_access["acces_masiv_smb"] | self.context_anomaly["extrem"]),
                self.data_security_risk["breach_iminent"],
            ),
            ctrl.Rule(
                self.lateral_process_anomaly["compromitere_totala"],
                self.data_security_risk["breach_iminent"],
            ),
        ]

        self.l2_ctrl = ctrl.ControlSystem(rules_l2)

    # =========================================================================
    # SUB-SISTEMUL 3 (MASTER): Scor Global de Risc & Urgența Răspunsului SOAR
    # =========================================================================
    def _build_layer3_master_soar_fis(self) -> None:
        self.l3_identity_in = ctrl.Antecedent(self.u_pct, "identity_risk_in")
        self.l3_data_in = ctrl.Antecedent(self.u_pct, "data_security_risk_in")
        self.asset_criticality = ctrl.Antecedent(self.u_scale10, "asset_criticality")

        self.global_cyber_risk = ctrl.Consequent(
            self.u_pct, "global_cyber_risk", defuzzify_method=self.defuzzify_method
        )
        self.response_urgency = ctrl.Consequent(
            self.u_pct, "response_urgency", defuzzify_method=self.defuzzify_method
        )

        for ant in (self.l3_identity_in, self.l3_data_in):
            ant["scazut"] = fuzz.trapmf(self.u_pct, [0, 0, 18, 32])
            ant["mediu"] = fuzz.trimf(self.u_pct, [22, 45, 65])
            ant["ridicat"] = fuzz.trimf(self.u_pct, [55, 74, 88])
            ant["critic"] = fuzz.trapmf(self.u_pct, [80, 90, 100, 100])

        self.asset_criticality["workstation"] = fuzz.trapmf(self.u_scale10, [0, 0, 2.5, 4.5])
        self.asset_criticality["member_server"] = fuzz.trimf(self.u_scale10, [3.0, 6.0, 8.5])
        self.asset_criticality["domain_controller"] = fuzz.trapmf(self.u_scale10, [7.5, 8.8, 10.0, 10.0])

        # Ieșire 1: global_cyber_risk [0..100]
        self.global_cyber_risk["low"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 28])
        self.global_cyber_risk["medium"] = fuzz.trimf(self.u_pct, [20, 42, 62])
        self.global_cyber_risk["high"] = fuzz.trimf(self.u_pct, [52, 72, 86])
        self.global_cyber_risk["critical"] = fuzz.trapmf(self.u_pct, [78, 88, 100, 100])

        # Ieșire 2: response_urgency [0..100]
        self.response_urgency["monitor"] = fuzz.trapmf(self.u_pct, [0, 0, 15, 30])
        self.response_urgency["alert_audit"] = fuzz.trimf(self.u_pct, [22, 45, 65])
        self.response_urgency["contain_host_account"] = fuzz.trimf(self.u_pct, [55, 75, 90])
        self.response_urgency["domain_lockdown"] = fuzz.trapmf(self.u_pct, [82, 91, 100, 100])

        rules_l3 = [
            # Scăzut + Scăzut
            ctrl.Rule(
                self.l3_identity_in["scazut"] & self.l3_data_in["scazut"] & self.asset_criticality["workstation"],
                (self.global_cyber_risk["low"], self.response_urgency["monitor"]),
            ),
            ctrl.Rule(
                self.l3_identity_in["scazut"] & self.l3_data_in["scazut"]
                & (self.asset_criticality["member_server"] | self.asset_criticality["domain_controller"]),
                (self.global_cyber_risk["low"], self.response_urgency["monitor"]),
            ),
            # Combinații Medii
            ctrl.Rule(
                (self.l3_identity_in["mediu"] & self.l3_data_in["scazut"])
                | (self.l3_identity_in["scazut"] & self.l3_data_in["mediu"]),
                (self.global_cyber_risk["medium"], self.response_urgency["alert_audit"]),
            ),
            ctrl.Rule(
                self.l3_identity_in["mediu"] & self.l3_data_in["mediu"]
                & (self.asset_criticality["workstation"] | self.asset_criticality["member_server"]),
                (self.global_cyber_risk["medium"], self.response_urgency["alert_audit"]),
            ),
            ctrl.Rule(
                self.l3_identity_in["mediu"] & self.l3_data_in["mediu"] & self.asset_criticality["domain_controller"],
                (self.global_cyber_risk["high"], self.response_urgency["contain_host_account"]),
            ),
            # Combinații Ridicate
            ctrl.Rule(
                (self.l3_identity_in["ridicat"] | self.l3_data_in["ridicat"])
                & (self.asset_criticality["workstation"] | self.asset_criticality["member_server"]),
                (self.global_cyber_risk["high"], self.response_urgency["contain_host_account"]),
            ),
            ctrl.Rule(
                (self.l3_identity_in["ridicat"] | self.l3_data_in["ridicat"])
                & self.asset_criticality["domain_controller"],
                (self.global_cyber_risk["critical"], self.response_urgency["domain_lockdown"]),
            ),
            ctrl.Rule(
                self.l3_identity_in["ridicat"] & self.l3_data_in["ridicat"],
                (self.global_cyber_risk["critical"], self.response_urgency["domain_lockdown"]),
            ),
            # Combinații Critice
            ctrl.Rule(
                self.l3_identity_in["critic"] | self.l3_data_in["critic"],
                (self.global_cyber_risk["critical"], self.response_urgency["domain_lockdown"]),
            ),
        ]

        self.l3_ctrl = ctrl.ControlSystem(rules_l3)

    # =========================================================================
    # METODE DE CALCUL ȘI EXPLICABILITATE (XAI)
    # =========================================================================
    @staticmethod
    def _compute_var_memberships(antecedent: ctrl.Antecedent, val: float) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for term_name, term_obj in antecedent.terms.items():
            mu = float(fuzz.interp_membership(antecedent.universe, term_obj.mf, val))
            result[term_name] = round(mu, 4)
        return result

    @staticmethod
    def _classify_risk_and_response(global_risk: float, urgency: float) -> Tuple[str, str, int]:
        if global_risk >= 78.0 or urgency >= 80.0:
            return "CRITICAL", "EMERGENCY_DOMAIN_LOCKDOWN", 15
        if global_risk >= 55.0 or urgency >= 58.0:
            return "HIGH", "CONTAIN_ACCOUNT_AND_HOST", 12
        if global_risk >= 30.0 or urgency >= 32.0:
            return "MEDIUM", "ALERT_AND_AUDIT", 8
        return "LOW", "MONITOR_LOG", 3

    def _compare_defuzzification_methods(
        self, id_risk: float, data_risk: float, asset_crit: float
    ) -> Dict[str, float]:
        methods = ["centroid", "bisector", "mom", "som", "lom"]
        results: Dict[str, float] = {}

        # Construim funcția agregată de apartenență pe universul global_cyber_risk
        # folosind gradele de activare ale celor 4 termeni de ieșire
        id_m = self._compute_var_memberships(self.l3_identity_in, id_risk)
        da_m = self._compute_var_memberships(self.l3_data_in, data_risk)
        as_m = self._compute_var_memberships(self.asset_criticality, asset_crit)

        w_low = min(id_m["scazut"], da_m["scazut"])
        w_med = max(
            min(id_m["mediu"], da_m["scazut"]),
            min(id_m["scazut"], da_m["mediu"]),
            min(id_m["mediu"], da_m["mediu"], max(as_m["workstation"], as_m["member_server"])),
        )
        w_high = max(
            min(max(id_m["ridicat"], da_m["ridicat"]), max(as_m["workstation"], as_m["member_server"])),
            min(id_m["mediu"], da_m["mediu"], as_m["domain_controller"]),
        )
        w_crit = max(
            id_m["critic"],
            da_m["critic"],
            min(id_m["ridicat"], da_m["ridicat"]),
            min(max(id_m["ridicat"], da_m["ridicat"]), as_m["domain_controller"]),
        )

        aggregated = np.fmax.reduce([
            np.fmin(w_low, self.global_cyber_risk["low"].mf),
            np.fmin(w_med, self.global_cyber_risk["medium"].mf),
            np.fmin(w_high, self.global_cyber_risk["high"].mf),
            np.fmin(w_crit, self.global_cyber_risk["critical"].mf),
        ])

        if np.sum(aggregated) == 0:
            return {m: 0.0 for m in methods}

        for m in methods:
            try:
                val = float(fuzz.defuzz(self.u_pct, aggregated, m))
                results[m] = round(val, 2)
            except Exception:
                results[m] = 0.0
        return results

    def evaluate(
        self,
        failed_logons: float,
        kerberos_anomaly: float,
        privilege_level: float,
        sensitive_data_access: float,
        lateral_process_anomaly: float,
        context_anomaly: float,
        asset_criticality: float,
    ) -> FuzzyEvaluationResult:
        # Clamparea valorilor în universurile de discurs
        fl = float(np.clip(failed_logons, 0.0, 100.0))
        ka = float(np.clip(kerberos_anomaly, 0.0, 100.0))
        pl = float(np.clip(privilege_level, 0.0, 10.0))
        sda = float(np.clip(sensitive_data_access, 0.0, 100.0))
        lpa = float(np.clip(lateral_process_anomaly, 0.0, 100.0))
        ca = float(np.clip(context_anomaly, 0.0, 10.0))
        ac = float(np.clip(asset_criticality, 0.0, 10.0))

        # 1. Inferență Strat 1 (Identitate & Autentificare)
        sim_l1 = ctrl.ControlSystemSimulation(self.l1_ctrl)
        sim_l1.input["failed_logons"] = fl
        sim_l1.input["kerberos_anomaly"] = ka
        sim_l1.input["privilege_level"] = pl
        sim_l1.compute()
        id_risk = round(float(sim_l1.output["identity_risk"]), 2)

        # 2. Inferență Strat 2 (Securitatea Datelor & Mișcare Laterală)
        sim_l2 = ctrl.ControlSystemSimulation(self.l2_ctrl)
        sim_l2.input["sensitive_data_access"] = sda
        sim_l2.input["lateral_process_anomaly"] = lpa
        sim_l2.input["context_anomaly"] = ca
        sim_l2.compute()
        data_risk = round(float(sim_l2.output["data_security_risk"]), 2)

        # 3. Inferență Strat 3 (Master Cyber Risk & SOAR Response Urgency)
        sim_l3 = ctrl.ControlSystemSimulation(self.l3_ctrl)
        sim_l3.input["identity_risk_in"] = id_risk
        sim_l3.input["data_security_risk_in"] = data_risk
        sim_l3.input["asset_criticality"] = ac
        sim_l3.compute()
        global_risk = round(float(sim_l3.output["global_cyber_risk"]), 2)
        urgency = round(float(sim_l3.output["response_urgency"]), 2)

        # Calculul gradelor de apartenență (XAI)
        memberships = {
            "failed_logons": self._compute_var_memberships(self.failed_logons, fl),
            "kerberos_anomaly": self._compute_var_memberships(self.kerberos_anomaly, ka),
            "privilege_level": self._compute_var_memberships(self.privilege_level, pl),
            "sensitive_data_access": self._compute_var_memberships(self.sensitive_data_access, sda),
            "lateral_process_anomaly": self._compute_var_memberships(self.lateral_process_anomaly, lpa),
            "context_anomaly": self._compute_var_memberships(self.context_anomaly, ca),
            "asset_criticality": self._compute_var_memberships(self.asset_criticality, ac),
            "identity_risk": self._compute_var_memberships(self.l3_identity_in, id_risk),
            "data_security_risk": self._compute_var_memberships(self.l3_data_in, data_risk),
        }

        risk_level, response_tier, wazuh_level = self._classify_risk_and_response(global_risk, urgency)
        defuzz_comp = self._compare_defuzzification_methods(id_risk, data_risk, ac)

        # Generarea explicațiilor lingvistice pentru regulile dominante activate
        active_explanations: List[str] = []
        for var_name, terms in memberships.items():
            dominant_term, dom_mu = max(terms.items(), key=lambda kv: kv[1])
            if dom_mu > 0.25:
                active_explanations.append(f"{var_name} -> {dominant_term} (μ={dom_mu:.2f})")

        return FuzzyEvaluationResult(
            inputs={
                "failed_logons": fl,
                "kerberos_anomaly": ka,
                "privilege_level": pl,
                "sensitive_data_access": sda,
                "lateral_process_anomaly": lpa,
                "context_anomaly": ca,
                "asset_criticality": ac,
            },
            identity_risk_score=id_risk,
            data_security_risk_score=data_risk,
            global_cyber_risk_score=global_risk,
            response_urgency_score=urgency,
            risk_level=risk_level,
            response_tier=response_tier,
            wazuh_rule_level=wazuh_level,
            memberships=memberships,
            defuzz_comparison=defuzz_comp,
            active_rules_summary=active_explanations,
        )
