
from pathlib import Path
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from skfuzzy import control as ctrl

from .experimental_engine import ExperimentalFuzzyEngine


class ExperimentalVisualizer:

    def __init__(self, engine: ExperimentalFuzzyEngine, output_dir: Path) -> None:
        self.engine = engine
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_membership_functions(self) -> Path:
        fig, axes = plt.subplots(3, 2, figsize=(14, 11), dpi=200)
        fig.suptitle(
            "Funcțiile de Apartenență Fuzzy Mamdani (Modelul Experimental F, A, S, L → R)",
            fontsize=14,
            fontweight="bold"
        )

        vars_info = [
            (self.engine.f_auth, "Intrare F: Frecvența autentificărilor [0 - 100]"),
            (self.engine.a_dev, "Intrare A: Abaterea comportamentală [0 - 100]"),
            (self.engine.s_sev, "Intrare S: Severitatea evenimentelor [0 - 100]"),
            (self.engine.l_scope, "Intrare L: Amploarea accesului la sisteme [0 - 100]"),
            (self.engine.r_risk, "Ieșire R: Scorul final de risc [0 - 100]"),
        ]

        color_map = {
            "scazuta": "#27ae60", "medie": "#f39c12", "ridicata": "#c0392b",
            "scazut": "#27ae60", "ridicat": "#d35400", "critic": "#8e44ad"
        }

        for idx, (var, title) in enumerate(vars_info):
            ax = axes.flat[idx]
            for term_name, term_obj in var.terms.items():
                c = color_map.get(term_name, "#2980b9")
                ax.plot(var.universe, term_obj.mf, linewidth=2.0, label=term_name, color=c)
                ax.fill_between(var.universe, 0, term_obj.mf, alpha=0.12, color=c)
            ax.set_title(title, fontsize=10, fontweight="bold")
            ax.set_ylabel("Grad μ(x)", fontsize=9)
            ax.set_xlabel("Univers de discurs", fontsize=9)
            ax.set_ylim(-0.02, 1.08)
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.legend(loc="upper right", fontsize=8)

        # Ascundem ultimul subplot rămas gol
        axes.flat[5].axis("off")
        # Adăugăm o legendă explicativă pentru praguri în ultimul spațiu
        txt = (
            "Praguri de decizie experimentală:\n"
            "• [0 – 34]  : Scăzut   (Înregistrare & Monitorizare)\n"
            "• [35 – 69] : Mediu    (Alertă & Analiză suplimentară)\n"
            "• [70 – 84] : Ridicat  (Alertă prioritară & Contenție propusă)\n"
            "• [85 – 100]: Critic   (Escaladare imediată & Izolare)"
        )
        axes.flat[5].text(0.1, 0.4, txt, fontsize=10, bbox=dict(boxstyle="round,pad=0.8", facecolor="#ecf0f1", alpha=0.8))

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out_path = self.output_dir / "fuzzy_fasl_membership_functions.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_3d_surfaces(self) -> Path:
        grid_pts = 24
        vals = np.linspace(0, 100, grid_pts)
        X, Y = np.meshgrid(vals, vals)

        # Suprafața 1: F x A -> R (cu S=15, L=15 fixate)
        Z1 = np.zeros_like(X)
        for i in range(grid_pts):
            for j in range(grid_pts):
                sim = ctrl.ControlSystemSimulation(self.engine.control_system)
                sim.input["auth_frequency"] = float(X[i, j])
                sim.input["behavior_deviation"] = float(Y[i, j])
                sim.input["event_severity"] = 20.0
                sim.input["access_scope"] = 20.0
                sim.compute()
                Z1[i, j] = float(sim.output["risk_score"])

        # Suprafața 2: S x L -> R (cu F=40, A=40 fixate)
        Z2 = np.zeros_like(X)
        for i in range(grid_pts):
            for j in range(grid_pts):
                sim = ctrl.ControlSystemSimulation(self.engine.control_system)
                sim.input["auth_frequency"] = 40.0
                sim.input["behavior_deviation"] = 40.0
                sim.input["event_severity"] = float(X[i, j])
                sim.input["access_scope"] = float(Y[i, j])
                sim.compute()
                Z2[i, j] = float(sim.output["risk_score"])

        fig = plt.figure(figsize=(15, 6), dpi=200)

        # Plot 1
        ax1 = fig.add_subplot(121, projection="3d")
        surf1 = ax1.plot_surface(X, Y, Z1, cmap="viridis", edgecolor="k", linewidth=0.2, alpha=0.88)
        ax1.set_title("Suprafața 3D: Frecvență (F) × Abatere (A) → Risc (R)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Frecvență autentificări (F)")
        ax1.set_ylabel("Abatere comportament (A)")
        ax1.set_zlabel("Scor Risc (R)")
        fig.colorbar(surf1, ax=ax1, shrink=0.5, aspect=10)

        # Plot 2
        ax2 = fig.add_subplot(122, projection="3d")
        surf2 = ax2.plot_surface(X, Y, Z2, cmap="plasma", edgecolor="k", linewidth=0.2, alpha=0.88)
        ax2.set_title("Suprafața 3D: Severitate (S) × Amploare Acces (L) → Risc (R)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Severitate eveniment (S)")
        ax2.set_ylabel("Amploare acces (L)")
        ax2.set_zlabel("Scor Risc (R)")
        fig.colorbar(surf2, ax=ax2, shrink=0.5, aspect=10)

        plt.tight_layout()
        out_path = self.output_dir / "fuzzy_fasl_3d_surfaces.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_confusion_matrices(self, fuzzy_metrics: Dict[str, Any], baseline_metrics: Dict[str, Any]) -> Path:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=200)

        def draw_cm(ax, tp, fp, tn, fn, title, subtitle):
            cm = np.array([[tn, fp], [fn, tp]])
            im = ax.imshow(cm, cmap="Blues", interpolation="nearest")
            ax.set_title(f"{title}\n({subtitle})", fontsize=11, fontweight="bold")
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["Normal (Negativ)", "Suspect (Pozitiv)"], fontsize=9)
            ax.set_yticklabels(["Normal (Negativ)", "Suspect (Pozitiv)"], fontsize=9)
            ax.set_xlabel("Clasă Prezisă", fontsize=10)
            ax.set_ylabel("Adevăr de Referință (Ground Truth)", fontsize=10)

            for i in range(2):
                for j in range(2):
                    val = cm[i, j]
                    color = "white" if val > cm.max() / 2 else "black"
                    cell_label = f"{val}\n" + (
                        "(TN)" if (i == 0 and j == 0) else
                        "(FP)" if (i == 0 and j == 1) else
                        "(FN)" if (i == 1 and j == 0) else "(TP)"
                    )
                    ax.text(j, i, cell_label, ha="center", va="center", color=color, fontsize=10, fontweight="bold")

        draw_cm(
            ax1,
            fuzzy_metrics["tp"], fuzzy_metrics["fp"], fuzzy_metrics["tn"], fuzzy_metrics["fn"],
            "Motor Fuzzy Mamdani",
            f"Precision: {fuzzy_metrics['precision']:.2f} | Recall: {fuzzy_metrics['recall']:.2f} | FPR: {fuzzy_metrics['fpr']:.2f}"
        )

        draw_cm(
            ax2,
            baseline_metrics["tp"], baseline_metrics["fp"], baseline_metrics["tn"], baseline_metrics["fn"],
            "Model de Referință (Reguli Determ.)",
            f"Precision: {baseline_metrics['precision']:.2f} | Recall: {baseline_metrics['recall']:.2f} | FPR: {baseline_metrics['fpr']:.2f}"
        )

        plt.tight_layout()
        out_path = self.output_dir / "experiment_confusion_matrices.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_metric_comparison(self, fuzzy_metrics: Dict[str, Any], baseline_metrics: Dict[str, Any]) -> Path:
        metric_names = ["Precision", "Recall", "Specificity (1-FPR)", "F1-Score", "Accuracy"]
        fuzzy_vals = [
            fuzzy_metrics["precision"], fuzzy_metrics["recall"], fuzzy_metrics["specificity"],
            fuzzy_metrics["f1_score"], fuzzy_metrics["accuracy"]
        ]
        base_vals = [
            baseline_metrics["precision"], baseline_metrics["recall"], baseline_metrics["specificity"],
            baseline_metrics["f1_score"], baseline_metrics["accuracy"]
        ]

        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)
        x = np.arange(len(metric_names))
        width = 0.35

        rects1 = ax.bar(x - width/2, fuzzy_vals, width, label="Motor Fuzzy Mamdani", color="#2980b9")
        rects2 = ax.bar(x + width/2, base_vals, width, label="Model Referință (Reguli Fixe)", color="#7f8c8d")

        ax.set_ylabel("Scor Metric [0.0 - 1.0]", fontsize=10)
        ax.set_title("Comparație Experimentală: Fuzzy Mamdani vs. Model de Referință (Set Test N=200)", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(metric_names, fontsize=9)
        ax.set_ylim(0, 1.15)
        ax.axhline(0.90, color="#e74c3c", linestyle="--", linewidth=1.2, label="Criteriu de Succes (>= 90%)")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(loc="lower right", fontsize=9)

        # Etichete numerice pe bare
        for r in rects1:
            h = r.get_height()
            ax.annotate(f"{h:.2f}", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                        textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")
        for r in rects2:
            h = r.get_height()
            ax.annotate(f"{h:.2f}", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                        textcoords="offset points", ha="center", va="bottom", fontsize=8)

        plt.tight_layout()
        out_path = self.output_dir / "experiment_metric_comparison.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_risk_score_distribution(self, test_df: pd.DataFrame) -> Path:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=200)

        classes = ["normal", "ambiguous", "suspicious"]
        data_to_plot = [test_df[test_df["ground_truth"] == c]["fuzzy_risk_score"].values for c in classes]

        bp = ax.boxplot(data_to_plot, patch_artist=True, labels=["Normal (N01, N02)", "Ambiguu (C01)", "Suspect (S01-S04)"])
        colors = ["#2ecc71", "#f39c12", "#e74c3c"]
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.65)

        ax.axhline(35, color="#f39c12", linestyle=":", label="Prag Mediu / Alertă (35)")
        ax.axhline(70, color="#e67e22", linestyle="--", label="Prag Ridicat / Contenție (70)")
        ax.axhline(85, color="#c0392b", linestyle="-.", label="Prag Critic / Lockdown (85)")

        ax.set_title("Distribuția Scorurilor de Risc Fuzzy Mamdani pe Clase de Referință", fontsize=11, fontweight="bold")
        ax.set_ylabel("Scor de Risc Defuzzificat [0 - 100]", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.legend(loc="upper left", fontsize=8)

        plt.tight_layout()
        out_path = self.output_dir / "risk_score_distribution.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def generate_all_experimental_plots(
        self,
        fuzzy_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        test_df: pd.DataFrame
    ) -> List[Path]:
        return [
            self.plot_membership_functions(),
            self.plot_3d_surfaces(),
            self.plot_confusion_matrices(fuzzy_metrics, baseline_metrics),
            self.plot_metric_comparison(fuzzy_metrics, baseline_metrics),
            self.plot_risk_score_distribution(test_df)
        ]
