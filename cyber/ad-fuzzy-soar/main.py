#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import time
from typing import Dict, Any, List
import pandas as pd

from ad_fuzzy_soar.config import SystemConfig, BASE_DIR
from ad_fuzzy_soar.fuzzy_engine import ActiveDirectoryFuzzyEngine, FuzzyEvaluationResult
from ad_fuzzy_soar.ad_simulator import ActiveDirectoryAttackSimulator
from ad_fuzzy_soar.incident_response import IncidentResponseOrchestrator
from ad_fuzzy_soar.visualizer import FuzzySystemVisualizer


def evaluate_dataframe_batch(
    df: pd.DataFrame,
    engine: ActiveDirectoryFuzzyEngine,
    orchestrator: IncidentResponseOrchestrator,
) -> pd.DataFrame:
    enriched_rows: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        incident_meta = row.to_dict()
        res: FuzzyEvaluationResult = engine.evaluate(
            failed_logons=float(row["failed_logons"]),
            kerberos_anomaly=float(row["kerberos_anomaly"]),
            privilege_level=float(row["privilege_level"]),
            sensitive_data_access=float(row["sensitive_data_access"]),
            lateral_process_anomaly=float(row["lateral_process_anomaly"]),
            context_anomaly=float(row["context_anomaly"]),
            asset_criticality=float(row["asset_criticality"]),
        )
        soar_outcome = orchestrator.handle_incident(incident_meta, res)

        row_out = dict(incident_meta)
        row_out.update({
            "identity_risk_score": res.identity_risk_score,
            "data_security_risk_score": res.data_security_risk_score,
            "global_cyber_risk_score": res.global_cyber_risk_score,
            "response_urgency_score": res.response_urgency_score,
            "risk_level": res.risk_level,
            "response_tier": res.response_tier,
            "wazuh_rule_level": res.wazuh_rule_level,
            "defuzz_centroid": res.defuzz_comparison.get("centroid", 0.0),
            "defuzz_bisector": res.defuzz_comparison.get("bisector", 0.0),
            "defuzz_mom": res.defuzz_comparison.get("mom", 0.0),
            "active_rules_summary": " | ".join(res.active_rules_summary),
            "wazuh_report_status": soar_outcome["wazuh_report"]["status"],
            "discord_alert_status": soar_outcome["discord_report"]["status"],
            "ansible_command": soar_outcome["remediation_plan"]["ansible_command"],
            "native_script_command": soar_outcome["remediation_plan"]["script_command"],
        })
        enriched_rows.append(row_out)

    return pd.DataFrame(enriched_rows)


def print_evaluation_summary(evaluated_df: pd.DataFrame) -> None:
    print("\n" + "=" * 118)
    print("  RAPORT DE EVALUARE FUZZY MAMDANI MULTI-STRAT — SECURITATE ACTIVE DIRECTORY & RĂSPUNS LA INCIDENTE (SOAR)")
    print("=" * 118)

    display_cols = [
        "event_id",
        "os_type",
        "target_host",
        "target_user",
        "identity_risk_score",
        "data_security_risk_score",
        "global_cyber_risk_score",
        "risk_level",
        "response_tier",
        "wazuh_rule_level",
    ]
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print(evaluated_df[display_cols].to_string(index=False))
    print("-" * 118)

    for _, row in evaluated_df.iterrows():
        print(
            f"\n[{row['event_id']}] {row['scenario_name']} ({row['os_type'].upper()} -> {row['target_host']})"
        )
        print(
            f"  ├─ MITRE ATT&CK   : {row['mitre_tactic']} | {row['mitre_technique']} (EventIDs: {row['windows_event_ids']})"
        )
        print(
            f"  ├─ Scoruri Fuzzy  : L1 Identitate={row['identity_risk_score']:.2f} | "
            f"L2 Date/Lateral={row['data_security_risk_score']:.2f} | "
            f"L3 Global={row['global_cyber_risk_score']:.2f} (Bisector={row['defuzz_bisector']:.2f}, MOM={row['defuzz_mom']:.2f})"
        )
        print(f"  ├─ Reguli Active  : {row['active_rules_summary']}")
        print(
            f"  ├─ Decizie SOAR   : [{row['risk_level']}] -> {row['response_tier']} "
            f"(Wazuh Rule Level {row['wazuh_rule_level']} | Status: {row['wazuh_report_status']})"
        )
        print(f"  ├─ Alertă Discord : {row['discord_alert_status']}")
        print(f"  ├─ Playbook       : {row['ansible_command']}")
        print(f"  └─ Script Nativ   : {row['native_script_command']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AD-Fuzzy-SOAR: Sistem Inteligent de Inferență Fuzzy Mamdani pentru Active Directory & Wazuh SOAR"
    )
    parser.add_argument(
        "--mode",
        choices=["simulate-reference", "simulate-stream", "wazuh-poll", "daemon", "single", "experiment", "generate-data"],
        default="simulate-reference",
        help="Modul de execuție al sistemului (implicit: simulate-reference)",
    )
    parser.add_argument("--config", type=str, default=str(BASE_DIR / "config.yaml"), help="Calea către config.yaml")
    parser.add_argument("--count", type=int, default=20, help="Numărul de evenimente pentru simulate-stream")
    parser.add_argument("--interval", type=int, default=30, help="Intervalul de polling în secunde pentru modul daemon")
    parser.add_argument("--no-plots", action="store_true", help="Dezactivează generarea graficelor matplotlib")
    parser.add_argument("--discord-webhook", type=str, default="", help="URL opțional Discord Webhook")
    parser.add_argument("--execute-response", action="store_true", help="Dezactivează Dry-Run și execută activ răspunsul")

    # Parametri pentru --mode single
    parser.add_argument("--host", type=str, default="DC01.CORP.CYBERLAB.LOCAL")
    parser.add_argument("--user", type=str, default="svc_sql_prod")
    parser.add_argument("--os-type", choices=["windows", "linux"], default="windows")
    parser.add_argument("--src-ip", type=str, default="192.168.64.155")
    parser.add_argument("--failed-logons", type=float, default=55.0)
    parser.add_argument("--kerberos-anomaly", type=float, default=80.0)
    parser.add_argument("--privilege-level", type=float, default=7.5)
    parser.add_argument("--sensitive-data-access", type=float, default=70.0)
    parser.add_argument("--lateral-process-anomaly", type=float, default=65.0)
    parser.add_argument("--context-anomaly", type=float, default=7.0)
    parser.add_argument("--asset-criticality", type=float, default=8.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = SystemConfig.from_yaml(Path(args.config))
    if args.discord_webhook:
        cfg.discord.webhook_url = args.discord_webhook
    if args.execute_response:
        cfg.response.dry_run = False

    cfg.ensure_directories()
    chmod_scripts = [cfg.response.linux_sh_script_path]
    for sp in chmod_scripts:
        if sp.exists():
            sp.chmod(0o755)

    engine = ActiveDirectoryFuzzyEngine(defuzzify_method="centroid")
    orchestrator = IncidentResponseOrchestrator(cfg)
    simulator = ActiveDirectoryAttackSimulator()

    if args.mode == "experiment":
        from run_experiments import run_full_experiment_pipeline
        run_full_experiment_pipeline()
        return

    if args.mode == "generate-data":
        from ad_fuzzy_soar.synthetic_generator import SyntheticDatasetGenerator
        gen = SyntheticDatasetGenerator(seed=42)
        saved = gen.save_dataset_files(BASE_DIR / "data")
        print("\n[OK] Setul sintetic de date (500 înregistrări) a fost generat:")
        for k, p in saved.items():
            print(f"  ├─ {k}: {p}")
        return

    if args.mode == "simulate-reference":
        df_in = simulator.get_reference_scenarios_df()
    elif args.mode == "simulate-stream":
        df_in = simulator.generate_synthetic_stream_df(count=args.count)
    elif args.mode == "single":
        df_in = pd.DataFrame([{
            "event_id": "AD-CUSTOM-001",
            "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
            "scenario_name": "Evaluare Manuală CLI Incident Active Directory",
            "os_type": args.os_type,
            "target_host": args.host,
            "target_user": args.user,
            "source_ip": args.src_ip,
            "windows_event_ids": "4625, 4769, 4662, 5145",
            "mitre_tactic": "Credential Access / Lateral Movement",
            "mitre_technique": "Custom Evaluation Vector",
            "failed_logons": args.failed_logons,
            "kerberos_anomaly": args.kerberos_anomaly,
            "privilege_level": args.privilege_level,
            "sensitive_data_access": args.sensitive_data_access,
            "lateral_process_anomaly": args.lateral_process_anomaly,
            "context_anomaly": args.context_anomaly,
            "asset_criticality": args.asset_criticality,
        }])
    elif args.mode == "wazuh-poll":
        df_in = orchestrator.wazuh.fetch_active_directory_alerts_df()
        if df_in.empty:
            print("[INFO] Nu s-au găsit alerte noi în Wazuh Indexer sau serverul Wazuh este offline.")
            print("[INFO] Se utilizează scenariile de referință Active Directory pentru demonstrație.")
            df_in = simulator.get_reference_scenarios_df()
    elif args.mode == "daemon":
        print(f"[DAEMON] Pornire monitorizare continuă Wazuh SIEM (interval={args.interval}s)...")
        try:
            while True:
                df_poll = orchestrator.wazuh.fetch_active_directory_alerts_df()
                if not df_poll.empty:
                    evaluated = evaluate_dataframe_batch(df_poll, engine, orchestrator)
                    print_evaluation_summary(evaluated)
                else:
                    print(f"[{pd.Timestamp.now(tz='UTC').isoformat()}] [DAEMON] Nicio alertă nouă în Wazuh.")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[DAEMON] Oprit de utilizator.")
            return
    else:
        df_in = simulator.get_reference_scenarios_df()

    evaluated_df = evaluate_dataframe_batch(df_in, engine, orchestrator)
    print_evaluation_summary(evaluated_df)

    # Salvare rapoarte CSV și JSON cu pandas
    csv_path = cfg.response.reports_dir / "ad_fuzzy_evaluation_report.csv"
    json_path = cfg.response.reports_dir / "ad_fuzzy_evaluation_report.json"
    evaluated_df.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(evaluated_df.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Raport CSV salvat în   : {csv_path}")
    print(f"[OK] Raport JSON salvat în  : {json_path}")
    print(f"[OK] Evenimente Wazuh JSONL : {cfg.wazuh.fallback_events_log}")
    print(f"[OK] Payloads Discord JSONL : {cfg.discord.fallback_alerts_log}")

    if not args.no_plots:
        visualizer = FuzzySystemVisualizer(engine, cfg.response.plots_dir)
        saved_plots = visualizer.generate_all_plots(evaluated_df)
        for p in saved_plots:
            print(f"[OK] Grafic Fuzzy generat   : {p}")


if __name__ == "__main__":
    main()
