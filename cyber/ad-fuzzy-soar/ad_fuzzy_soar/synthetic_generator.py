
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


SCENARIO_PROFILES: Dict[str, Dict[str, Any]] = {
    "N01": {
        "name": "Autentificare normală",
        "ground_truth": "normal",
        "description": "Utilizator standard pe stația obișnuită, acces la resurse autorizate.",
        "f_mean": 16.0, "f_std": 5.0,
        "a_mean": 9.0,  "a_std": 4.0,
        "s_mean": 6.0,  "s_std": 3.0,
        "l_mean": 14.0, "l_std": 5.0,
        "roles": ["standard_user"],
        "maintenance_prob": 0.0,
    },
    "N02": {
        "name": "Activitate administrativă legitimă",
        "ground_truth": "normal",
        "description": "Administrator domeniu care accesează multiple sisteme în cadrul atribuțiilor.",
        "f_mean": 42.0, "f_std": 8.0,
        "a_mean": 14.0, "a_std": 4.0,
        "s_mean": 10.0, "s_std": 4.0,
        "l_mean": 74.0, "l_std": 8.0,
        "roles": ["domain_admin", "workstation_support"],
        "maintenance_prob": 0.15,
    },
    "S01": {
        "name": "Creștere neobișnuită a autentificărilor",
        "ground_truth": "suspicious",
        "description": "Spike brusc de autentificări pe un cont (posibil password spray sau brute-force).",
        "f_mean": 82.0, "f_std": 6.0,
        "a_mean": 78.0, "a_std": 6.0,
        "s_mean": 32.0, "s_std": 8.0,
        "l_mean": 34.0, "l_std": 8.0,
        "roles": ["standard_user", "service_account"],
        "maintenance_prob": 0.0,
    },
    "S02": {
        "name": "Acces neobișnuit la mai multe endpoint-uri",
        "ground_truth": "suspicious",
        "description": "Cont care accesează sisteme dinafara profilului său normal (mișcare laterală).",
        "f_mean": 42.0, "f_std": 8.0,
        "a_mean": 80.0, "a_std": 6.0,
        "s_mean": 38.0, "s_std": 8.0,
        "l_mean": 84.0, "l_std": 6.0,
        "roles": ["standard_user", "service_account"],
        "maintenance_prob": 0.0,
    },
    "S03": {
        "name": "Evenimente de securitate cu severitate ridicată",
        "ground_truth": "suspicious",
        "description": "Alerte de severitate mare din Wazuh/Sysmon (Kerberoasting, DCSync, Mimikatz).",
        "f_mean": 36.0, "f_std": 10.0,
        "a_mean": 58.0, "a_std": 8.0,
        "s_mean": 88.0, "s_std": 5.0,
        "l_mean": 52.0, "l_std": 10.0,
        "roles": ["service_account", "domain_admin", "standard_user"],
        "maintenance_prob": 0.0,
    },
    "S04": {
        "name": "Corelarea mai multor indicii",
        "ground_truth": "suspicious",
        "description": "Atac activ combinat: frecvență mare, abatere severă, alerte critice și acces larg.",
        "f_mean": 86.0, "f_std": 5.0,
        "a_mean": 88.0, "a_std": 5.0,
        "s_mean": 90.0, "s_std": 5.0,
        "l_mean": 86.0, "l_std": 5.0,
        "roles": ["domain_admin", "compromised_user"],
        "maintenance_prob": 0.0,
    },
    "C01": {
        "name": "Caz ambiguu / posibil fals pozitiv",
        "ground_truth": "ambiguous",
        "description": "Activitate legitimă diferită de profilul istoric (mentenanță nocturnă planificată).",
        "f_mean": 52.0, "f_std": 9.0,
        "a_mean": 46.0, "a_std": 7.0,
        "s_mean": 18.0, "s_std": 5.0,
        "l_mean": 48.0, "l_std": 8.0,
        "roles": ["domain_admin", "backup_operator"],
        "maintenance_prob": 0.85,
    },
}


class SyntheticDatasetGenerator:

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)
        self.base_time = datetime(2026, 10, 1, 8, 0, 0, tzinfo=timezone.utc)

    def _sample_scenario_record(
        self,
        scenario_id: str,
        partition: str,
        index: int,
        introduce_missing_data: bool = False
    ) -> Dict[str, Any]:
        cfg = SCENARIO_PROFILES[scenario_id]

        def sample_val(mean: float, std: float) -> float:
            return round(float(np.clip(self.rng.normal(mean, std), 0.0, 100.0)), 1)

        f_val = sample_val(cfg["f_mean"], cfg["f_std"])
        a_val = sample_val(cfg["a_mean"], cfg["a_std"])
        s_val = sample_val(cfg["s_mean"], cfg["s_std"])
        l_val = sample_val(cfg["l_mean"], cfg["l_std"])

        # Caz de date incomplete / senzori cu erori (pentru verificarea robusteții fail-safe)
        missing_fields: List[str] = []
        if introduce_missing_data:
            target_field = self.rng.choice(["access_scope", "event_severity", "auth_frequency"])
            if target_field == "access_scope":
                l_val = None
            elif target_field == "event_severity":
                s_val = None
            else:
                f_val = None
            missing_fields.append(str(target_field))

        role = str(self.rng.choice(cfg["roles"]))
        is_maint = bool(self.rng.random() < cfg["maintenance_prob"])

        # Timestamp stocastic incrementat
        time_offset = timedelta(minutes=int(self.rng.integers(1, 1440 * 7)))
        rec_time = (self.base_time + time_offset).isoformat()

        user_prefix = {
            "standard_user": "u_ion.", "domain_admin": "adm_vlad.",
            "workstation_support": "sup_ana.", "service_account": "svc_sql_",
            "compromised_user": "u_victima.", "backup_operator": "svc_backup_"
        }.get(role, "user_")
        target_user = f"{user_prefix}{self.rng.integers(10, 99)}"

        hosts_pool = ["WS-CONTAB01", "WS-HR02", "WS-IT05", "SQL-PROD01", "SRV-FILE01", "DC01"]
        target_host = f"{self.rng.choice(hosts_pool)}.CORP.CYBERLAB.LOCAL"

        record_id = f"SYN-{partition.upper()[:3]}-{index + 1:04d}"

        return {
            "record_id": record_id,
            "scenario_id": scenario_id,
            "scenario_name": cfg["name"],
            "source": "synthetic",
            "partition": partition,
            "timestamp": rec_time,
            "target_user": target_user,
            "target_host": target_host,
            "account_role": role,
            "maintenance_window": is_maint,
            "auth_frequency": f_val,
            "behavior_deviation": a_val,
            "event_severity": s_val,
            "access_scope": l_val,
            "ground_truth": cfg["ground_truth"],
            "has_missing_data": len(missing_fields) > 0,
            "missing_fields": missing_fields,
            "description": cfg["description"]
        }

    def generate_partition(
        self,
        partition_name: str,
        count: int,
        missing_rate: float = 0.05
    ) -> List[Dict[str, Any]]:
        scenario_keys = ["N01", "N02", "S01", "S02", "S03", "S04", "C01"]
        probabilities = [0.25, 0.15, 0.15, 0.15, 0.15, 0.10, 0.05]

        records: List[Dict[str, Any]] = []
        for i in range(count):
            sc_id = str(self.rng.choice(scenario_keys, p=probabilities))
            introduce_missing = bool(self.rng.random() < missing_rate)
            rec = self._sample_scenario_record(sc_id, partition_name, i, introduce_missing)
            records.append(rec)
        return records

    def generate_full_dataset(
        self,
        calib_count: int = 200,
        valid_count: int = 100,
        test_count: int = 200
    ) -> Dict[str, List[Dict[str, Any]]]:
        calib = self.generate_partition("calibration", calib_count, missing_rate=0.03)
        valid = self.generate_partition("validation", valid_count, missing_rate=0.04)
        test = self.generate_partition("test", test_count, missing_rate=0.05)
        return {
            "calibration": calib,
            "validation": valid,
            "test": test,
            "all": calib + valid + test
        }

    def save_dataset_files(self, output_dir: Path) -> Dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        ds = self.generate_full_dataset(calib_count=200, valid_count=100, test_count=200)

        saved_files: Dict[str, Path] = {}

        # 1. Schema JSON
        schema_path = output_dir / "dataset_schema.json"
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "AD-Fuzzy-SOAR Synthetic Dataset Schema",
            "type": "object",
            "properties": {
                "record_id": {"type": "string"},
                "scenario_id": {"type": "string", "enum": ["N01", "N02", "S01", "S02", "S03", "S04", "C01"]},
                "scenario_name": {"type": "string"},
                "source": {"type": "string", "enum": ["synthetic", "homelab", "wazuh"]},
                "partition": {"type": "string", "enum": ["calibration", "validation", "test"]},
                "timestamp": {"type": "string", "format": "date-time"},
                "target_user": {"type": "string"},
                "target_host": {"type": "string"},
                "account_role": {"type": "string"},
                "maintenance_window": {"type": "boolean"},
                "auth_frequency": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
                "behavior_deviation": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
                "event_severity": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
                "access_scope": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
                "ground_truth": {"type": "string", "enum": ["normal", "suspicious", "ambiguous"]},
                "has_missing_data": {"type": "boolean"},
                "missing_fields": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"}
            },
            "required": ["scenario_id", "source", "ground_truth"]
        }
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        saved_files["schema"] = schema_path

        # 2. Partiții JSON și CSV
        for part_name, records in ds.items():
            json_file = output_dir / f"synthetic_{part_name}_{len(records)}.json"
            csv_file = output_dir / f"synthetic_{part_name}_{len(records)}.csv"

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

            df = pd.DataFrame(records)
            df.to_csv(csv_file, index=False)

            saved_files[f"{part_name}_json"] = json_file
            saved_files[f"{part_name}_csv"] = csv_file

        return saved_files
