
from dataclasses import dataclass
import time
from typing import Dict, Any, Tuple, Optional
import numpy as np


@dataclass
class BaselineEvaluationResult:
    scenario_id: str
    ground_truth: str
    inputs: Dict[str, float]
    predicted_label: str  # "normal" sau "suspicious"
    fired_rule: str
    risk_score_approx: float
    decision: str
    inference_time_ms: float


class RuleBasedBaselineClassifier:

    def __init__(
        self,
        severity_threshold: float = 70.0,
        auth_spike_threshold: float = 70.0,
        deviation_threshold: float = 65.0,
        scope_threshold: float = 70.0,
    ) -> None:
        self.severity_th = severity_threshold
        self.auth_spike_th = auth_spike_threshold
        self.dev_th = deviation_threshold
        self.scope_th = scope_threshold

    def evaluate(
        self,
        auth_frequency: Optional[float],
        behavior_deviation: Optional[float],
        event_severity: Optional[float],
        access_scope: Optional[float],
        scenario_id: str = "EXP",
        ground_truth: str = "unknown",
        account_role: str = "standard_user",
        maintenance_window: bool = False
    ) -> BaselineEvaluationResult:
        t0 = time.perf_counter()

        f = float(auth_frequency if auth_frequency is not None and not np.isnan(auth_frequency) else 15.0)
        a = float(behavior_deviation if behavior_deviation is not None and not np.isnan(behavior_deviation) else 10.0)
        s = float(event_severity if event_severity is not None and not np.isnan(event_severity) else 10.0)
        l = float(access_scope if access_scope is not None and not np.isnan(access_scope) else 10.0)

        fired_rule = "None (Traffic within normal boundaries)"
        predicted = "normal"
        decision = "Inregistrare si monitorizare"
        score_approx = 20.0

        # Regula 1: Severitate ridicata din jurnal
        if s >= self.severity_th:
            predicted = "suspicious"
            fired_rule = f"RULE_HIGH_SEVERITY: event_severity ({s:.1f}) >= {self.severity_th}"
            score_approx = 85.0
            decision = "Alerta prioritara si recomandare de raspuns"

        # Regula 2: Spike frecventa + abatere
        elif f >= self.auth_spike_th and a >= self.dev_th:
            predicted = "suspicious"
            fired_rule = f"RULE_AUTH_SPIKE: auth_freq ({f:.1f}) >= {self.auth_spike_th} AND dev ({a:.1f}) >= {self.dev_th}"
            score_approx = 80.0
            decision = "Alerta prioritara si recomandare de raspuns"

        # Regula 3: Acces larg + abatere (daca nu este administrator legitim)
        elif l >= self.scope_th and a >= self.dev_th:
            predicted = "suspicious"
            fired_rule = f"RULE_UNUSUAL_SCOPE: scope ({l:.1f}) >= {self.scope_th} AND dev ({a:.1f}) >= {self.dev_th}"
            score_approx = 75.0
            decision = "Alerta prioritara si recomandare de raspuns"

        # Regula 4: Corelare medie
        elif f >= 60.0 and a >= 55.0 and s >= 50.0:
            predicted = "suspicious"
            fired_rule = f"RULE_MULTI_CORRELATION: f>=60, a>=55, s>=50"
            score_approx = 72.0
            decision = "Alerta prioritara si recomandare de raspuns"

        # Regula 5: Abatere moderata (posibil ambiguu)
        elif a >= 50.0 or s >= 45.0:
            predicted = "normal"  # In SIEM clasic, evenimentele sub pragul de alerta sunt considerate benigne/zgomot
            fired_rule = "RULE_SUB_THRESHOLD_ANOMALY (Not escalated)"
            score_approx = 45.0
            decision = "Alerta si analiza suplimentara"

        t1 = time.perf_counter()
        inference_time_ms = round((t1 - t0) * 1000.0, 3)

        return BaselineEvaluationResult(
            scenario_id=scenario_id,
            ground_truth=ground_truth,
            inputs={"auth_frequency": f, "behavior_deviation": a, "event_severity": s, "access_scope": l},
            predicted_label=predicted,
            fired_rule=fired_rule,
            risk_score_approx=score_approx,
            decision=decision,
            inference_time_ms=inference_time_ms
        )
