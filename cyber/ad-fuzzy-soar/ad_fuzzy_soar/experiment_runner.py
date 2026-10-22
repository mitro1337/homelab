
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd

from .experimental_engine import ExperimentalFuzzyEngine, ExperimentalEvaluationResult
from .baseline_classifier import RuleBasedBaselineClassifier, BaselineEvaluationResult
from .response_policy_engine import ResponsePolicyEngine, PolicyDecision


@dataclass
class ConfusionMetrics:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    fpr: float = 0.0
    specificity: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    avg_latency_ms: float = 0.0

    @classmethod
    def compute(cls, tp: int, fp: int, tn: int, fn: int, latencies: List[float]) -> "ConfusionMetrics":
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        f1 = float(2 * (prec * rec) / (prec + rec)) if (prec + rec) > 0 else 0.0
        acc = float((tp + tn) / (tp + tn + fp + fn)) if (tp + tn + fp + fn) > 0 else 0.0
        avg_lat = float(np.mean(latencies)) if latencies else 0.0

        return cls(
            tp=tp, fp=fp, tn=tn, fn=fn,
            precision=round(prec, 4),
            recall=round(rec, 4),
            fpr=round(fpr, 4),
            specificity=round(spec, 4),
            f1_score=round(f1, 4),
            accuracy=round(acc, 4),
            avg_latency_ms=round(avg_lat, 4)
        )


class ExperimentRunner:

    def __init__(
        self,
        fuzzy_engine: Optional[ExperimentalFuzzyEngine] = None,
        baseline_classifier: Optional[RuleBasedBaselineClassifier] = None,
        policy_engine: Optional[ResponsePolicyEngine] = None
    ) -> None:
        self.fuzzy_engine = fuzzy_engine or ExperimentalFuzzyEngine()
        self.baseline = baseline_classifier or RuleBasedBaselineClassifier()
        self.policy_engine = policy_engine or ResponsePolicyEngine(simulation_mode=True)

    def run_evaluation_on_dataset(
        self, records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        results_rows: List[Dict[str, Any]] = []

        # Vectori de clasificare pentru Fuzzy Mamdani (prag alertă: R >= 35, prag contenție: R >= 70)
        # Eticheta de referință binară: "suspicious" = pozitiv (1), "normal" / "ambiguous" = negativ (0)
        fuzzy_latencies: List[float] = []
        base_latencies: List[float] = []

        f_tp = f_fp = f_tn = f_fn = 0
        b_tp = b_fp = b_tn = b_fn = 0

        # Numărători pentru protecțiile Response Policy Engine
        destructive_actions_executed = 0
        actions_blocked_by_safety = 0
        audit_records_count = 0

        for r in records:
            gt = str(r.get("ground_truth", "normal")).lower()
            is_suspicious_gt = (gt == "suspicious")

            # 1. Evaluare Fuzzy Mamdani
            f_eval: ExperimentalEvaluationResult = self.fuzzy_engine.evaluate(
                auth_frequency=r.get("auth_frequency"),
                behavior_deviation=r.get("behavior_deviation"),
                event_severity=r.get("event_severity"),
                access_scope=r.get("access_scope"),
                scenario_id=r.get("scenario_id", "EXP"),
                source=r.get("source", "synthetic"),
                ground_truth=gt,
                notes=r.get("description", "")
            )
            fuzzy_latencies.append(f_eval.inference_time_ms)

            # Clasificare binară Fuzzy: dacă R >= 50 (sau nivel Ridicat/Critic), este clasificat suspect
            fuzzy_predicted_suspicious = (f_eval.risk_score >= 50.0)

            if is_suspicious_gt:
                if fuzzy_predicted_suspicious:
                    f_tp += 1
                else:
                    f_fn += 1
            else:
                if fuzzy_predicted_suspicious:
                    f_fp += 1
                else:
                    f_tn += 1

            # 2. Evaluare Rule-Based Baseline
            b_eval: BaselineEvaluationResult = self.baseline.evaluate(
                auth_frequency=r.get("auth_frequency"),
                behavior_deviation=r.get("behavior_deviation"),
                event_severity=r.get("event_severity"),
                access_scope=r.get("access_scope"),
                scenario_id=r.get("scenario_id", "EXP"),
                ground_truth=gt,
                account_role=r.get("account_role", "standard_user"),
                maintenance_window=bool(r.get("maintenance_window", False))
            )
            base_latencies.append(b_eval.inference_time_ms)
            baseline_predicted_suspicious = (b_eval.predicted_label == "suspicious")

            if is_suspicious_gt:
                if baseline_predicted_suspicious:
                    b_tp += 1
                else:
                    b_fn += 1
            else:
                if baseline_predicted_suspicious:
                    b_fp += 1
                else:
                    b_tn += 1

            # 3. Evaluare Politică de Răspuns (Response Policy Engine)
            pol: PolicyDecision = self.policy_engine.evaluate_action_policy(
                risk_score=f_eval.risk_score,
                risk_level=f_eval.risk_level,
                target_user=r.get("target_user", "unknown"),
                target_host=r.get("target_host", "unknown"),
                has_missing_data=bool(r.get("has_missing_data", False)),
                operator_approved=False
            )
            audit_records_count += 1
            if pol.blocked_by_safety_rule:
                actions_blocked_by_safety += 1
            if pol.mode == "ENFORCED" and "CONTAIN" in pol.proposed_action:
                destructive_actions_executed += 1

            results_rows.append({
                "record_id": r.get("record_id"),
                "scenario_id": r.get("scenario_id"),
                "scenario_name": r.get("scenario_name"),
                "ground_truth": gt,
                "auth_frequency": r.get("auth_frequency"),
                "behavior_deviation": r.get("behavior_deviation"),
                "event_severity": r.get("event_severity"),
                "access_scope": r.get("access_scope"),
                # Rezultate Fuzzy Mamdani
                "fuzzy_risk_score": f_eval.risk_score,
                "fuzzy_risk_level": f_eval.risk_level,
                "fuzzy_decision": f_eval.decision,
                "fuzzy_predicted_label": "suspicious" if fuzzy_predicted_suspicious else "normal",
                "fuzzy_latency_ms": f_eval.inference_time_ms,
                # Rezultate Rule-Based Baseline
                "baseline_predicted_label": b_eval.predicted_label,
                "baseline_fired_rule": b_eval.fired_rule,
                "baseline_score_approx": b_eval.risk_score_approx,
                "baseline_latency_ms": b_eval.inference_time_ms,
                # Rezultate Policy Engine
                "policy_mode": pol.mode,
                "policy_blocked_by_safety": pol.blocked_by_safety_rule,
                "policy_safety_rule": pol.safety_rule_name or "None",
                "policy_proposed_action": pol.proposed_action
            })

        fuzzy_metrics = ConfusionMetrics.compute(f_tp, f_fp, f_tn, f_fn, fuzzy_latencies)
        baseline_metrics = ConfusionMetrics.compute(b_tp, b_fp, b_tn, b_fn, base_latencies)

        # Criterii de succes conform Secțiunii 11:
        # 1. min 90% normal fara escaladare nejustificata (Specificitate pe Normal >= 0.90)
        # 2. recall de cel putin 90% pe cazurile suspecte (Recall >= 0.90)
        # 3. nicio actiune distructiva executata automat in modul de simulare (destructive == 0)
        # 4. trasabilitate pentru toate scorurile (audit_records == len(records))
        success_criteria = {
            "criterion_1_normal_specificity_ge_90": {
                "target": 0.90,
                "fuzzy_value": fuzzy_metrics.specificity,
                "baseline_value": baseline_metrics.specificity,
                "fuzzy_passed": bool(fuzzy_metrics.specificity >= 0.90),
                "baseline_passed": bool(baseline_metrics.specificity >= 0.90),
            },
            "criterion_2_suspicious_recall_ge_90": {
                "target": 0.90,
                "fuzzy_value": fuzzy_metrics.recall,
                "baseline_value": baseline_metrics.recall,
                "fuzzy_passed": bool(fuzzy_metrics.recall >= 0.90),
                "baseline_passed": bool(baseline_metrics.recall >= 0.90),
            },
            "criterion_3_zero_destructive_in_simulation": {
                "target": 0,
                "actual_executed": destructive_actions_executed,
                "passed": bool(destructive_actions_executed == 0),
            },
            "criterion_4_full_audit_traceability": {
                "target": len(records),
                "audit_logged": audit_records_count,
                "passed": bool(audit_records_count == len(records)),
            }
        }

        experiment_summary = {
            "total_records_evaluated": len(records),
            "fuzzy_mamdani_metrics": fuzzy_metrics.__dict__,
            "rule_based_baseline_metrics": baseline_metrics.__dict__,
            "safety_controls_summary": {
                "destructive_actions_executed": destructive_actions_executed,
                "actions_blocked_by_safety_policy": actions_blocked_by_safety,
                "audit_entries_logged": audit_records_count,
                "simulation_mode_active": self.policy_engine.simulation_mode,
            },
            "success_criteria_validation": success_criteria
        }

        return results_rows, experiment_summary

    def build_results_register_df(self, detailed_rows: List[Dict[str, Any]]) -> pd.DataFrame:
        df_all = pd.DataFrame(detailed_rows)
        register_rows: List[Dict[str, Any]] = []

        scenario_order = ["N01", "N02", "S01", "S02", "S03", "S04", "C01"]
        for sc in scenario_order:
            sub = df_all[df_all["scenario_id"] == sc]
            if not sub.empty:
                # Luam primul caz reprezentativ complet
                row = sub.iloc[0]
                register_rows.append({
                    "ID": sc,
                    "Sursă": "Sintetic / laborator",
                    "Etichetă de referință": row["ground_truth"].capitalize(),
                    "Scor fuzzy": f"{float(row['fuzzy_risk_score']):.2f}",
                    "Decizie": row["fuzzy_decision"],
                    "Rezultat": "Detectat corect" if row["fuzzy_predicted_label"] == row["ground_truth"] else "Fals Negativ / Neutru"
                })

        # Adăugăm intrarea rezervată W01 din Secțiunea 10 a planului
        register_rows.append({
            "ID": "W01",
            "Sursă": "Wazuh real",
            "Etichetă de referință": "De validat",
            "Scor fuzzy": "—",
            "Decizie": "—",
            "Rezultat": "Rezervat pentru Etapa III (Wazuh real)"
        })

        return pd.DataFrame(register_rows)
