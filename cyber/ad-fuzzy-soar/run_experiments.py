#!/usr/bin/env python3

import json
from pathlib import Path
import pandas as pd

from ad_fuzzy_soar.config import BASE_DIR
from ad_fuzzy_soar.experimental_engine import ExperimentalFuzzyEngine
from ad_fuzzy_soar.synthetic_generator import SyntheticDatasetGenerator
from ad_fuzzy_soar.baseline_classifier import RuleBasedBaselineClassifier
from ad_fuzzy_soar.response_policy_engine import ResponsePolicyEngine
from ad_fuzzy_soar.experiment_runner import ExperimentRunner
from ad_fuzzy_soar.experimental_visualizer import ExperimentalVisualizer


def run_full_experiment_pipeline() -> None:
    data_dir = BASE_DIR / "data"
    reports_exp_dir = BASE_DIR / "reports" / "experiment"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_exp_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 105)
    print("  AD-FUZZY-SOAR — PIPELINE EXPERIMENTAL (ZILELE TEHNICII STUDENȚEȘTI / LICENȚĂ)")
    print("=" * 105)

    # -------------------------------------------------------------------------
    # Etapa 1: Generare Set Sintetic (Secțiunea 5)
    # -------------------------------------------------------------------------
    print("\n[ETAPA 1/4] Generare set de date sintetic structurat (500 înregistrări)...")
    generator = SyntheticDatasetGenerator(seed=42)
    saved_dataset_paths = generator.save_dataset_files(data_dir)
    print(f"  ├─ Schema JSON documentată salvată în : {saved_dataset_paths['schema']}")
    print(f"  ├─ Calibrare (200 înregistrări)       : {saved_dataset_paths['calibration_csv']}")
    print(f"  ├─ Validare (100 înregistrări)        : {saved_dataset_paths['validation_csv']}")
    print(f"  ├─ Testare Finală (200 înregistrări)  : {saved_dataset_paths['test_csv']}")
    print(f"  └─ Dataset integral (500 înregistrări): {saved_dataset_paths['all_csv']}")

    # -------------------------------------------------------------------------
    # Etapa 2: Execuție Evaluare Comparativă pe Setul de Test (Secțiunea 9)
    # -------------------------------------------------------------------------
    print("\n[ETAPA 2/4] Evaluare comparativă: Motor Fuzzy Mamdani vs. Model de Referință pe Setul de Test...")
    with open(saved_dataset_paths["test_json"], "r", encoding="utf-8") as f:
        test_records = json.load(f)

    fuzzy_engine = ExperimentalFuzzyEngine(defuzzify_method="centroid")
    baseline = RuleBasedBaselineClassifier()
    policy_engine = ResponsePolicyEngine(
        simulation_mode=True,
        require_human_approval=True,
        audit_log_path=reports_exp_dir / "policy_audit.jsonl"
    )

    runner = ExperimentRunner(fuzzy_engine, baseline, policy_engine)
    detailed_rows, summary = runner.run_evaluation_on_dataset(test_records)

    # Salvăm rezultatele detaliate
    test_eval_df = pd.DataFrame(detailed_rows)
    test_eval_csv = reports_exp_dir / "test_evaluations_comparison.csv"
    test_eval_df.to_csv(test_eval_csv, index=False)

    summary_json_path = reports_exp_dir / "experiment_metrics_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # Etapa 3: Registrul de Rezultate & Verificare Criterii de Succes (Secțiunile 10 & 11)
    # -------------------------------------------------------------------------
    print("\n[ETAPA 3/4] Populare Registru de Rezultate și Verificare Criterii de Acceptare...")
    register_df = runner.build_results_register_df(detailed_rows)
    register_csv = reports_exp_dir / "results_register.csv"
    register_df.to_csv(register_csv, index=False)

    print("\n" + "-" * 105)
    print("  REGISTRUL DE REZULTATE EXPERIMENTALE (Tabelul din Secțiunea 10):")
    print("-" * 105)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)
    print(register_df.to_string(index=False))
    print("-" * 105)

    f_m = summary["fuzzy_mamdani_metrics"]
    b_m = summary["rule_based_baseline_metrics"]

    print("\n  REZULTATE COMPARATIVE PE SETUL DE TEST (N = 200 înregistrări):")
    print(f"  ┌──────────────────────┬────────────────────────┬────────────────────────┐")
    print(f"  │ Indicator Metric     │  Motor Fuzzy Mamdani   │  Model Referință (SIEM)│")
    print(f"  ├──────────────────────┼────────────────────────┼────────────────────────┤")
    print(f"  │ Precizie (Precision) │         {f_m['precision']:.4f}         │         {b_m['precision']:.4f}         │")
    print(f"  │ Rată Detecție (Recall│         {f_m['recall']:.4f}         │         {b_m['recall']:.4f}         │")
    print(f"  │ Alarme False (FPR)   │         {f_m['fpr']:.4f}         │         {b_m['fpr']:.4f}         │")
    print(f"  │ Specificitate        │         {f_m['specificity']:.4f}         │         {b_m['specificity']:.4f}         │")
    print(f"  │ F1-Score             │         {f_m['f1_score']:.4f}         │         {b_m['f1_score']:.4f}         │")
    print(f"  │ Acuratețe Globală    │         {f_m['accuracy']:.4f}         │         {b_m['accuracy']:.4f}         │")
    print(f"  │ Latență medie / ev.  │         {f_m['avg_latency_ms']:.3f} ms       │         {b_m['avg_latency_ms']:.3f} ms       │")
    print(f"  └──────────────────────┴────────────────────────┴────────────────────────┘")

    crit = summary["success_criteria_validation"]
    print("\n  VERIFICARE CRITERII DE SUCCES (Secțiunea 11):")
    c1 = crit["criterion_1_normal_specificity_ge_90"]
    print(f"  • Criteriul 1 (Specificitate Normal >= 90%): Fuzzy={c1['fuzzy_value']:.2%} [{ 'SUCCES' if c1['fuzzy_passed'] else 'FAIL' }] vs. Baseline={c1['baseline_value']:.2%}")
    c2 = crit["criterion_2_suspicious_recall_ge_90"]
    print(f"  • Criteriul 2 (Recall Suspect >= 90%)     : Fuzzy={c2['fuzzy_value']:.2%} [{ 'SUCCES' if c2['fuzzy_passed'] else 'FAIL' }] vs. Baseline={c2['baseline_value']:.2%}")
    c3 = crit["criterion_3_zero_destructive_in_simulation"]
    print(f"  • Criteriul 3 (0 acțiuni distructive în sim): Executate={c3['actual_executed']} [{ 'SUCCES' if c3['passed'] else 'FAIL' }]")
    c4 = crit["criterion_4_full_audit_traceability"]
    print(f"  • Criteriul 4 (Trasabilitate completă audit) : Logate={c4['audit_logged']}/{c4['target']} [{ 'SUCCES' if c4['passed'] else 'FAIL' }]")

    # -------------------------------------------------------------------------
    # Etapa 4: Generare Grafice Științifice (300 DPI)
    # -------------------------------------------------------------------------
    print("\n[ETAPA 4/4] Generare diagrame științifice de înaltă rezoluție pentru lucrare...")
    visualizer = ExperimentalVisualizer(fuzzy_engine, reports_exp_dir)
    plots = visualizer.generate_all_experimental_plots(f_m, b_m, test_eval_df)
    for p in plots:
        print(f"  ├─ Grafic generat: {p.name} -> {p}")

    print("\n" + "=" * 105)
    print("  [OK] PIPELINE EXPERIMENTAL FINALIZAT CU SUCCES!")
    print(f"  Toate datele, rapoartele și graficele se află în: {reports_exp_dir}")
    print("=" * 105)


if __name__ == "__main__":
    run_full_experiment_pipeline()
