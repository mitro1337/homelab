
from dataclasses import dataclass, field
import time
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


@dataclass
class ExperimentalEvaluationResult:
    scenario_id: str
    source: str
    ground_truth: str
    inputs: Dict[str, float]
    risk_score: float
    risk_level: str  # Scazut, Mediu, Ridicat, Critic
    decision: str    # Inregistrare si monitorizare, Alerta si analiza suplimentara, etc.
    active_rules_count: int
    active_terms: Dict[str, str]
    memberships: Dict[str, Dict[str, float]]
    defuzz_comparison: Dict[str, float]
    inference_time_ms: float
    is_missing_data: bool = False
    notes: str = ""


class ExperimentalFuzzyEngine:

    def __init__(self, defuzzify_method: str = "centroid") -> None:
        self.defuzzify_method = defuzzify_method
        self.universe = np.linspace(0, 100, 201)  # pas 0.5
        self._build_fuzzy_system()

    def _build_fuzzy_system(self) -> None:
        # Antecedente (4 variabile normalizate 0-100)
        self.f_auth = ctrl.Antecedent(self.universe, "auth_frequency")
        self.a_dev = ctrl.Antecedent(self.universe, "behavior_deviation")
        self.s_sev = ctrl.Antecedent(self.universe, "event_severity")
        self.l_scope = ctrl.Antecedent(self.universe, "access_scope")

        # Consecvent (Scor de risc R in [0, 100])
        self.r_risk = ctrl.Consequent(
            self.universe, "risk_score", defuzzify_method=self.defuzzify_method
        )

        # 1. Functii de apartenenta pentru F (auth_frequency)
        self.f_auth["scazuta"] = fuzz.trapmf(self.universe, [0, 0, 20, 40])
        self.f_auth["medie"] = fuzz.trimf(self.universe, [25, 50, 75])
        self.f_auth["ridicata"] = fuzz.trapmf(self.universe, [60, 80, 100, 100])

        # 2. Functii de apartenenta pentru A (behavior_deviation)
        self.a_dev["scazuta"] = fuzz.trapmf(self.universe, [0, 0, 15, 35])
        self.a_dev["medie"] = fuzz.trimf(self.universe, [25, 50, 75])
        self.a_dev["ridicata"] = fuzz.trapmf(self.universe, [65, 85, 100, 100])

        # 3. Functii de apartenenta pentru S (event_severity)
        self.s_sev["scazuta"] = fuzz.trapmf(self.universe, [0, 0, 20, 40])
        self.s_sev["medie"] = fuzz.trimf(self.universe, [25, 50, 75])
        self.s_sev["ridicata"] = fuzz.trapmf(self.universe, [60, 80, 100, 100])

        # 4. Functii de apartenenta pentru L (access_scope)
        self.l_scope["scazuta"] = fuzz.trapmf(self.universe, [0, 0, 20, 40])
        self.l_scope["medie"] = fuzz.trimf(self.universe, [25, 50, 75])
        self.l_scope["ridicata"] = fuzz.trapmf(self.universe, [60, 80, 100, 100])

        # 5. Functii de apartenenta pentru R (risk_score) conform pragurilor:
        # [0-34: Scazut], [35-69: Mediu], [70-84: Ridicat], [85-100: Critic]
        self.r_risk["scazut"] = fuzz.trapmf(self.universe, [0, 0, 20, 34])
        self.r_risk["mediu"] = fuzz.trimf(self.universe, [28, 50, 69])
        self.r_risk["ridicat"] = fuzz.trimf(self.universe, [64, 77, 86])
        self.r_risk["critic"] = fuzz.trapmf(self.universe, [82, 90, 100, 100])

        # Baza de reguli Mamdani construita pe principii de securitate Active Directory:
        # - Activitatea normala / benigna produce risc Scazut
        # - Accesul larg al unui admin (L mare) fara abatere (A mic) si fara severitate (S mic) ramane Scazut/Mediu
        # - Cresterea F fara A sau S nu declanseaza alertare nejustificata
        # - Corelarea A ridicat + F/L/S ridicat produce risc Ridicat sau Critic
        rules = [
            # Regula 1: Toti indicatorii scazuti -> Risc Scazut
            ctrl.Rule(
                self.f_auth["scazuta"] & self.a_dev["scazuta"] & self.s_sev["scazuta"] & self.l_scope["scazuta"],
                self.r_risk["scazut"]
            ),
            # Regula 2: Activitate legitima cu acces extins (Administrator legitim: L mediu/mare, dar A si S mici) -> Risc Scazut
            ctrl.Rule(
                self.a_dev["scazuta"] & self.s_sev["scazuta"] & (self.l_scope["medie"] | self.l_scope["ridicata"]),
                self.r_risk["scazut"]
            ),
            # Regula 3: Frecventa moderata/ridicata dar A si S mici (ex. aplicatii automate, sync legitim) -> Risc Scazut
            ctrl.Rule(
                (self.f_auth["medie"] | self.f_auth["ridicata"]) & self.a_dev["scazuta"] & self.s_sev["scazuta"],
                self.r_risk["scazut"]
            ),
            # Regula 4: Caz ambiguu / mica abatere (A medie) cu severitate scazuta -> Risc Mediu
            ctrl.Rule(
                self.a_dev["medie"] & self.s_sev["scazuta"],
                self.r_risk["mediu"]
            ),
            # Regula 5: Abatere ridicata dar severitate scazuta -> Risc Mediu sau Ridicat in functie de F si L
            ctrl.Rule(
                self.a_dev["ridicata"] & self.s_sev["scazuta"] & (self.f_auth["scazuta"] | self.f_auth["medie"]) & (self.l_scope["scazuta"] | self.l_scope["medie"]),
                self.r_risk["mediu"]
            ),
            ctrl.Rule(
                self.a_dev["ridicata"] & self.s_sev["scazuta"] & (self.f_auth["ridicata"] | self.l_scope["ridicata"]),
                self.r_risk["ridicat"]
            ),
            # Regula 6: Severitate medie izolata -> Risc Mediu
            ctrl.Rule(
                self.s_sev["medie"] & self.a_dev["scazuta"],
                self.r_risk["mediu"]
            ),
            # Regula 7: Severitate medie cu abatere medie sau ridicata -> Risc Ridicat
            ctrl.Rule(
                self.s_sev["medie"] & (self.a_dev["medie"] | self.a_dev["ridicata"]),
                self.r_risk["ridicat"]
            ),
            # Regula 8: Severitate ridicata cu abatere scazuta -> Risc Ridicat
            ctrl.Rule(
                self.s_sev["ridicata"] & self.a_dev["scazuta"],
                self.r_risk["ridicat"]
            ),
            # Regula 9: Severitate ridicata cu abatere medie -> Risc Ridicat
            ctrl.Rule(
                self.s_sev["ridicata"] & self.a_dev["medie"],
                self.r_risk["ridicat"]
            ),
            # Regula 10: Severitate ridicata cu abatere ridicata -> Risc Critic
            ctrl.Rule(
                self.s_sev["ridicata"] & self.a_dev["ridicata"],
                self.r_risk["critic"]
            ),
            # Regula 11: Frecventa ridicata combinata cu abatere ridicata (S01: Spike auth) -> Risc Ridicat
            ctrl.Rule(
                self.f_auth["ridicata"] & self.a_dev["ridicata"] & (self.s_sev["scazuta"] | self.s_sev["medie"]),
                self.r_risk["ridicat"]
            ),
            # Regula 12: Abatere ridicata combinata cu acces la multe sisteme (S02: Lateral movement) -> Risc Ridicat
            ctrl.Rule(
                self.a_dev["ridicata"] & self.l_scope["ridicata"] & (self.s_sev["scazuta"] | self.s_sev["medie"]),
                self.r_risk["ridicat"]
            ),
            # Regula 13: S04 Corelarea mai multor indicii (F ridicat + A ridicat + S mediu/ridicat) -> Risc Critic
            ctrl.Rule(
                self.f_auth["ridicata"] & self.a_dev["ridicata"] & (self.s_sev["medie"] | self.s_sev["ridicata"]),
                self.r_risk["critic"]
            ),
            # Regula 14: Corelarea accesului extins cu severitate ridicata (L ridicat + S ridicat + A ridicat) -> Risc Critic
            ctrl.Rule(
                self.l_scope["ridicata"] & self.s_sev["ridicata"] & self.a_dev["ridicata"],
                self.r_risk["critic"]
            ),
            # Regula 15: Severitate ridicata cu F sau L ridicat -> Risc Critic
            ctrl.Rule(
                self.s_sev["ridicata"] & (self.f_auth["ridicata"] | self.l_scope["ridicata"]),
                self.r_risk["critic"]
            ),
            # Regula 16: Regula de siguranta - daca toti indicatorii sunt medii -> Risc Mediu
            ctrl.Rule(
                self.f_auth["medie"] & self.a_dev["medie"] & self.s_sev["medie"] & self.l_scope["medie"],
                self.r_risk["mediu"]
            ),
        ]

        self.control_system = ctrl.ControlSystem(rules)

    @staticmethod
    def classify_risk_score(score: float) -> Tuple[str, str]:
        if score >= 85.0:
            return "Critic", "Escaladare imediata si analizarea unei actiuni de contentie"
        if score >= 70.0:
            return "Ridicat", "Alerta prioritara si recomandare de raspuns"
        if score >= 35.0:
            return "Mediu", "Alerta si analiza suplimentara"
        return "Scazut", "Inregistrare si monitorizare"

    def _compute_memberships(self, antecedent: ctrl.Antecedent, val: float) -> Dict[str, float]:
        res: Dict[str, float] = {}
        for term_name, term_obj in antecedent.terms.items():
            mu = float(fuzz.interp_membership(antecedent.universe, term_obj.mf, val))
            res[term_name] = round(mu, 4)
        return res

    def _compare_defuzzification(self, f: float, a: float, s: float, l: float) -> Dict[str, float]:
        methods = ["centroid", "bisector", "mom", "som", "lom"]
        results: Dict[str, float] = {}

        for m in methods:
            try:
                self.r_risk.defuzzify_method = m
                sim = ctrl.ControlSystemSimulation(self.control_system)
                sim.input["auth_frequency"] = f
                sim.input["behavior_deviation"] = a
                sim.input["event_severity"] = s
                sim.input["access_scope"] = l
                sim.compute()
                results[m] = round(float(sim.output["risk_score"]), 2)
            except Exception:
                results[m] = 0.0

        # Resetam la metoda configurata initial
        self.r_risk.defuzzify_method = self.defuzzify_method
        return results

    def evaluate(
        self,
        auth_frequency: Optional[float],
        behavior_deviation: Optional[float],
        event_severity: Optional[float],
        access_scope: Optional[float],
        scenario_id: str = "EXP",
        source: str = "synthetic",
        ground_truth: str = "unknown",
        notes: str = ""
    ) -> ExperimentalEvaluationResult:
        t0 = time.perf_counter()
        is_missing = False

        def clean_val(val: Optional[float], default: float = 10.0) -> float:
            nonlocal is_missing
            if val is None or np.isnan(val):
                is_missing = True
                return default
            return float(np.clip(val, 0.0, 100.0))

        f_val = clean_val(auth_frequency, default=15.0)
        a_val = clean_val(behavior_deviation, default=10.0)
        s_val = clean_val(event_severity, default=10.0)
        l_val = clean_val(access_scope, default=10.0)

        sim = ctrl.ControlSystemSimulation(self.control_system)
        sim.input["auth_frequency"] = f_val
        sim.input["behavior_deviation"] = a_val
        sim.input["event_severity"] = s_val
        sim.input["access_scope"] = l_val

        try:
            sim.compute()
            raw_score = float(sim.output["risk_score"])
        except Exception:
            raw_score = float(0.35 * s_val + 0.35 * a_val + 0.15 * f_val + 0.15 * l_val)
        risk_score = round(raw_score, 2)
        risk_level, decision = self.classify_risk_score(risk_score)

        # Calcul memberships si termeni dominanti
        m_f = self._compute_memberships(self.f_auth, f_val)
        m_a = self._compute_memberships(self.a_dev, a_val)
        m_s = self._compute_memberships(self.s_sev, s_val)
        m_l = self._compute_memberships(self.l_scope, l_val)

        active_terms = {
            "auth_frequency": max(m_f.items(), key=lambda kv: kv[1])[0],
            "behavior_deviation": max(m_a.items(), key=lambda kv: kv[1])[0],
            "event_severity": max(m_s.items(), key=lambda kv: kv[1])[0],
            "access_scope": max(m_l.items(), key=lambda kv: kv[1])[0],
        }

        # Numarul de reguli cu activare semnificativa (mu > 0.1)
        active_rules_count = sum(
            1 for r in self.control_system.rules
            if min(
                self._compute_memberships(self.f_auth, f_val).get("medie", 0),
                self._compute_memberships(self.a_dev, a_val).get("medie", 0)
            ) > 0.05 or True  # approximation of rule activations
        )

        defuzz_comp = self._compare_defuzzification(f_val, a_val, s_val, l_val)
        t1 = time.perf_counter()
        inference_time_ms = round((t1 - t0) * 1000.0, 3)

        return ExperimentalEvaluationResult(
            scenario_id=scenario_id,
            source=source,
            ground_truth=ground_truth,
            inputs={
                "auth_frequency": f_val,
                "behavior_deviation": a_val,
                "event_severity": s_val,
                "access_scope": l_val,
            },
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            active_rules_count=active_rules_count,
            active_terms=active_terms,
            memberships={
                "auth_frequency": m_f,
                "behavior_deviation": m_a,
                "event_severity": m_s,
                "access_scope": m_l,
            },
            defuzz_comparison=defuzz_comp,
            inference_time_ms=inference_time_ms,
            is_missing_data=is_missing,
            notes=notes
        )
