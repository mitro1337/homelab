
import unittest
from ad_fuzzy_soar.config import SystemConfig
from ad_fuzzy_soar.fuzzy_engine import ActiveDirectoryFuzzyEngine
from ad_fuzzy_soar.ad_simulator import ActiveDirectoryAttackSimulator
from ad_fuzzy_soar.incident_response import IncidentResponseOrchestrator


class TestActiveDirectoryFuzzyEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ActiveDirectoryFuzzyEngine()
        self.cfg = SystemConfig()
        self.orchestrator = IncidentResponseOrchestrator(self.cfg)

    def test_benign_workstation_activity_is_low_risk(self) -> None:
        res = self.engine.evaluate(
            failed_logons=2.0,
            kerberos_anomaly=5.0,
            privilege_level=1.5,
            sensitive_data_access=8.0,
            lateral_process_anomaly=3.0,
            context_anomaly=1.0,
            asset_criticality=2.0,
        )
        self.assertEqual(res.risk_level, "LOW")
        self.assertEqual(res.response_tier, "MONITOR_LOG")
        self.assertLess(res.global_cyber_risk_score, 25.0)

    def test_dcsync_domain_controller_is_critical_lockdown(self) -> None:
        res = self.engine.evaluate(
            failed_logons=35.0,
            kerberos_anomaly=96.0,
            privilege_level=9.8,
            sensitive_data_access=97.0,
            lateral_process_anomaly=95.0,
            context_anomaly=9.5,
            asset_criticality=10.0,
        )
        self.assertEqual(res.risk_level, "CRITICAL")
        self.assertEqual(res.response_tier, "EMERGENCY_DOMAIN_LOCKDOWN")
        self.assertEqual(res.wazuh_rule_level, 15)
        self.assertGreater(res.global_cyber_risk_score, 85.0)

    def test_kerberoasting_service_account_is_high_or_critical(self) -> None:
        res = self.engine.evaluate(
            failed_logons=14.0,
            kerberos_anomaly=82.0,
            privilege_level=6.5,
            sensitive_data_access=48.0,
            lateral_process_anomaly=64.0,
            context_anomaly=6.8,
            asset_criticality=7.0,
        )
        self.assertIn(res.risk_level, ("HIGH", "CRITICAL"))
        self.assertIn(res.response_tier, ("CONTAIN_ACCOUNT_AND_HOST", "EMERGENCY_DOMAIN_LOCKDOWN"))
        self.assertGreater(res.identity_risk_score, 70.0)

    def test_reference_scenarios_dataframe_completeness(self) -> None:
        sim = ActiveDirectoryAttackSimulator()
        df = sim.get_reference_scenarios_df()
        self.assertEqual(len(df), 8)
        for _, row in df.iterrows():
            res = self.engine.evaluate(
                failed_logons=float(row["failed_logons"]),
                kerberos_anomaly=float(row["kerberos_anomaly"]),
                privilege_level=float(row["privilege_level"]),
                sensitive_data_access=float(row["sensitive_data_access"]),
                lateral_process_anomaly=float(row["lateral_process_anomaly"]),
                context_anomaly=float(row["context_anomaly"]),
                asset_criticality=float(row["asset_criticality"]),
            )
            plan = self.orchestrator.build_remediation_plan(row.to_dict(), res)
            self.assertIn("ansible-playbook", plan["ansible_command"])
            self.assertTrue(plan["script_command"].startswith(("pwsh", "bash")))

    def test_experimental_engine_fasl(self) -> None:
        from ad_fuzzy_soar.experimental_engine import ExperimentalFuzzyEngine
        exp_eng = ExperimentalFuzzyEngine()

        # N01: Normal
        r_norm = exp_eng.evaluate(15.0, 10.0, 5.0, 12.0, scenario_id="N01", ground_truth="normal")
        self.assertEqual(r_norm.risk_level, "Scazut")
        self.assertLess(r_norm.risk_score, 35.0)

        # N02: Administrator legitim (L mare, dar A si S mici)
        r_admin = exp_eng.evaluate(40.0, 12.0, 8.0, 75.0, scenario_id="N02", ground_truth="normal")
        self.assertEqual(r_admin.risk_level, "Scazut")
        self.assertLess(r_admin.risk_score, 35.0)

        # S04: Atac corelat masiv
        r_atk = exp_eng.evaluate(85.0, 88.0, 90.0, 88.0, scenario_id="S04", ground_truth="suspicious")
        self.assertEqual(r_atk.risk_level, "Critic")
        self.assertGreaterEqual(r_atk.risk_score, 85.0)

    def test_synthetic_dataset_generator(self) -> None:
        from ad_fuzzy_soar.synthetic_generator import SyntheticDatasetGenerator
        gen = SyntheticDatasetGenerator(seed=123)
        ds = gen.generate_full_dataset(calib_count=20, valid_count=10, test_count=20)
        self.assertEqual(len(ds["calibration"]), 20)
        self.assertEqual(len(ds["validation"]), 10)
        self.assertEqual(len(ds["test"]), 20)
        self.assertEqual(len(ds["all"]), 50)
        rec = ds["test"][0]
        self.assertIn("ground_truth", rec)
        self.assertIn("auth_frequency", rec)

    def test_response_policy_engine_safety_allowlists(self) -> None:
        from ad_fuzzy_soar.response_policy_engine import ResponsePolicyEngine
        pol_eng = ResponsePolicyEngine(simulation_mode=True)

        # Verificare blocare actiune distructiva pe Domain Controller (Tier-0 allowlist)
        p1 = pol_eng.evaluate_action_policy(95.0, "Critic", target_user="adm_temp", target_host="DC01.CORP.CYBERLAB.LOCAL")
        self.assertTrue(p1.blocked_by_safety_rule)
        self.assertEqual(p1.safety_rule_name, "SAFETY_CRITICAL_SYSTEM_ALLOWLIST")

        # Verificare blocare actiune distructiva pe contul krbtgt
        p2 = pol_eng.evaluate_action_policy(95.0, "Critic", target_user="krbtgt", target_host="WS-IT01.CORP.CYBERLAB.LOCAL")
        self.assertTrue(p2.blocked_by_safety_rule)
        self.assertEqual(p2.safety_rule_name, "SAFETY_CRITICAL_ACCOUNT_ALLOWLIST")

        # Verificare protectie fail-safe la date lipsa
        p3 = pol_eng.evaluate_action_policy(85.0, "Critic", target_user="u_victima", target_host="WS-FIN01", has_missing_data=True)
        self.assertTrue(p3.blocked_by_safety_rule)
        self.assertEqual(p3.safety_rule_name, "SAFETY_FAIL_SAFE_MISSING_DATA")


if __name__ == "__main__":
    unittest.main()
