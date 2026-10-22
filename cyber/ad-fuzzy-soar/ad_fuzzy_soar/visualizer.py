
from pathlib import Path
from typing import List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skfuzzy import control as ctrl

from .fuzzy_engine import ActiveDirectoryFuzzyEngine


class FuzzySystemVisualizer:

    def __init__(self, engine: ActiveDirectoryFuzzyEngine, output_dir: Path) -> None:
        self.engine = engine
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_membership_functions(self) -> Path:
        fig, axes = plt.subplots(3, 2, figsize=(15, 12), dpi=200)
        fig.suptitle(
            "Funcțiile de Apartenență Fuzzy Mamdani — Sistemul AD-Fuzzy-SOAR (Active Directory)",
            fontsize=15,
            fontweight="bold",
        )

        variables = [
            (self.engine.failed_logons, "L1 Antecedent: Autentificări Eșuate (Event 4625/4771)"),
            (self.engine.kerberos_anomaly, "L1 Antecedent: Anomalie Tichete Kerberos (4768/4769/PtH)"),
            (self.engine.privilege_level, "L1 Antecedent: Nivel Privilegii Cont AD [0-10]"),
            (self.engine.sensitive_data_access, "L2 Antecedent: Acces Date Sensibile SMB / DCSync (5145/4662)"),
            (self.engine.lateral_process_anomaly, "L2 Antecedent: Procese & Mișcare Laterală (4688/7045/SSSD)"),
            (self.engine.global_cyber_risk, "L3 Consecvent: Scor Global de Risc Cibernetic [0-100]"),
        ]

        for ax, (var, title) in zip(axes.flat, variables):
            for term_name, term_obj in var.terms.items():
                ax.plot(var.universe, term_obj.mf, linewidth=2.2, label=term_name)
                ax.fill_between(var.universe, 0, term_obj.mf, alpha=0.12)
            ax.set_title(title, fontsize=11, fontweight="bold")
            ax.set_ylabel("Grad de apartenență μ(x)")
            ax.set_xlabel("Univers de discurs")
            ax.set_ylim(-0.02, 1.08)
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.legend(loc="upper right", fontsize=9)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out_path = self.output_dir / "fuzzy_membership_functions.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_3d_control_surface(self, asset_criticality_fixed: float = 8.5) -> Path:
        grid_pts = 25
        x_vals = np.linspace(0, 100, grid_pts)
        y_vals = np.linspace(0, 100, grid_pts)
        X, Y = np.meshgrid(x_vals, y_vals)
        Z = np.zeros_like(X)

        for i in range(grid_pts):
            for j in range(grid_pts):
                sim = ctrl.ControlSystemSimulation(self.engine.l3_ctrl)
                sim.input["identity_risk_in"] = float(X[i, j])
                sim.input["data_security_risk_in"] = float(Y[i, j])
                sim.input["asset_criticality"] = asset_criticality_fixed
                sim.compute()
                Z[i, j] = float(sim.output["global_cyber_risk"])

        fig = plt.figure(figsize=(11, 8), dpi=200)
        ax = fig.add_subplot(111, projection="3d")
        surf = ax.plot_surface(
            X, Y, Z, cmap="inferno", edgecolor="k", linewidth=0.25, alpha=0.9, antialiased=True
        )
        ax.set_title(
            f"Suprafața 3D de Control Fuzzy Mamdani (Criticitate Activ = {asset_criticality_fixed}/10)",
            fontsize=13,
            fontweight="bold",
            pad=16,
        )
        ax.set_xlabel("Risc Identitate AD (L1) [0-100]")
        ax.set_ylabel("Risc Date & Mișcare Laterală (L2) [0-100]")
        ax.set_zlabel("Risc Global Defuzzificat (L3) [0-100]")
        fig.colorbar(surf, shrink=0.55, aspect=12, label="Global Cyber Risk Score")

        plt.tight_layout()
        out_path = self.output_dir / "fuzzy_3d_control_surface.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_scenarios_evaluation(self, evaluated_df: pd.DataFrame) -> Path:
        fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
        labels = [
            f"{row['event_id']}\n({row['target_host'].split('.')[0]})"
            for _, row in evaluated_df.iterrows()
        ]
        x = np.arange(len(labels))
        width = 0.2

        ax.bar(x - 1.5 * width, evaluated_df["identity_risk_score"], width, label="L1: Risc Identitate AD", color="#3498db")
        ax.bar(x - 0.5 * width, evaluated_df["data_security_risk_score"], width, label="L2: Risc Securitate Date", color="#9b59b6")
        ax.bar(x + 0.5 * width, evaluated_df["global_cyber_risk_score"], width, label="L3: Risc Global (Centroid)", color="#e74c3c")
        ax.bar(x + 1.5 * width, evaluated_df["response_urgency_score"], width, label="SOAR: Urgență Răspuns", color="#f39c12")

        # Praguri de decizie SOAR / Wazuh
        ax.axhline(78, color="#c0392b", linestyle="--", linewidth=1.2, label="Prag CRITICAL / Lockdown (78)")
        ax.axhline(55, color="#e67e22", linestyle="--", linewidth=1.2, label="Prag HIGH / Contain (55)")
        ax.axhline(30, color="#f1c40f", linestyle="--", linewidth=1.2, label="Prag MEDIUM / Alert (30)")

        ax.set_title(
            "Evaluarea Scenariilor de Atac Active Directory (Windows & Linux) prin Inferență Fuzzy Mamdani",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_ylabel("Scor Defuzzificat [0 - 100]")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
        ax.set_ylim(0, 108)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(loc="upper left", ncol=2, fontsize=9)

        plt.tight_layout()
        out_path = self.output_dir / "ad_scenarios_risk_comparison.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def generate_all_plots(self, evaluated_df: pd.DataFrame) -> List[Path]:
        return [
            self.plot_membership_functions(),
            self.plot_3d_control_surface(),
            self.plot_scenarios_evaluation(evaluated_df),
        ]
