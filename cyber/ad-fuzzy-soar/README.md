# AD-Fuzzy-SOAR — Active Directory Fuzzy Risk Assessment & SOAR Incident Response System

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Fuzzy Logic](https://img.shields.io/badge/fuzzy--engine-scikit--fuzzy-orange.svg)](https://scikit-fuzzy.github.io/scikit-fuzzy/)
[![SIEM Integration](https://img.shields.io/badge/SIEM-Wazuh%204.10-purple.svg)](https://wazuh.com/)

**AD-Fuzzy-SOAR** is an intelligent cyber risk evaluation and automated incident response (SOAR) platform designed specifically for **Active Directory** environments (Windows Domain Controllers, Member Servers, Workstations, and Linux SSSD/Kerberos nodes).

Traditional SIEM detection models rely heavily on rigid boolean thresholds (e.g., *"trigger alert if failed logons > 5 in 60s"*), which are either evaded by stealthy low-cadence adversaries or cause debilitating alert fatigue and false positives during planned maintenance. AD-Fuzzy-SOAR addresses this structural limitation by employing **Hierarchical Mamdani Fuzzy Inference Systems (FIS)** with Gaussian membership partitions and Centroid defuzzification to model behavioral uncertainty smoothly and contextually.

---

## Key Features

- **Multi-Layer Mamdani Fuzzy Inference**:
  - **Subsystem 1 (Identity Risk)**: Evaluates failed logons, Kerberos/NTLM ticket anomalies (Kerberoasting, Pass-the-Hash, Golden Ticket), and account privilege tiers.
  - **Subsystem 2 (Data Security & Lateral Movement Risk)**: Evaluates sensitive SMB file share access, remote execution anomalies (PsExec, WMI, PowerShell), and contextual temporal/geographic shifts.
  - **Subsystem 3 (Master Risk & SOAR Decision)**: Aggregates identity risk, data risk, and asset criticality into a global risk score $R \in [0, 100]$ and response urgency.
- **Experimental 4-Dimensional Engine ($F, A, S, L \rightarrow R$)**:
  - Evaluates Authentication Frequency ($F$), Behavioral Deviation ($A$), Event Severity ($S$), and Access Scope ($L$).
- **SOAR Policy Engine & Safety Controls**:
  - **Simulation Mode (`Dry-Run`)**: Evaluates actions without applying disruptive changes.
  - **Tier-0 Asset Protection**: Automatic allowlisting for Domain Controllers (`DC01`), `krbtgt`, and administrative accounts to prevent self-inflicted Denial of Service.
  - **Human-in-the-Loop**: Demands SOC analyst authorization for critical containment actions ($R \ge 85$).
  - **Audited Rollback**: Maintains a JSONL audit ledger and automated reversal plans for every applied containment action.
- **Bidirectional SIEM & Orchestration Integration**:
  - **Wazuh SIEM/XDR**: Native REST API (port 55000) and Indexer query connectors.
  - **Sysmon & Windows Event Log**: Granular telemetry decoders.
  - **Ansible & PowerShell/Bash**: Automated containment playbooks and host isolation scripts.
  - **Discord Webhooks**: Real-time rich embed alerting with color-coded severity tiers.

---

## Architecture Overview

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Active Directory & Endpoint Layer                 │
 │   Windows Server 2022 DC (AD DS, DNS, Kerberos) + Windows 10 + Linux   │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ (TCP 1514 / TLS)
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Wazuh SIEM / XDR Manager & Indexer                │
 │    Real-time log ingestion, XML decoders, and MITRE ATT&CK correlation │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Normalized Telemetry
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Mamdani Fuzzy Inference Engine                    │
 │       • Input Fuzzification (Gaussian Membership Functions)            │
 │       • Knowledge Base (15 Mamdani Min-Max Inference Rules)            │
 │       • Centroid Defuzzification: R = (∫ z · μ(z) dz) / (∫ μ(z) dz)    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Risk Score R ∈ [0, 100]
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                   Response Policy Engine & SOAR Controls               │
 │  [Dry-Run Simulation]  |  [Tier-0 Allowlist]  |  [Analyst Approval]    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ Executed Containment
                                     ▼
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
  Discord Webhook            Ansible Playbooks         PowerShell / Bash Script
  (Real-time Alerts)       (Host / Network Contain)      (Account Suspension)
```

---

## Experimental Benchmark Results

Evaluated against an independent, uncalibrated test dataset of 200 records (115 attacks, 85 normal/ambiguous events) comparing the **Mamdani Fuzzy Engine** against a standard **Rule-Based SIEM Baseline**:

| Metric | Mamdani Fuzzy Engine | Rule-Based SIEM Baseline | Operational Delta |
| :--- | :---: | :---: | :--- |
| **Accuracy** | **99.00%** | 97.50% | **+1.50%** |
| **Precision** | **100.00%** | 100.00% | Zero false positives on both |
| **Recall (Detection Rate)** | **98.26%** | 95.65% | **+2.61%** (5 missed by baseline vs 2) |
| **F1-Score** | **0.9912** | 0.9778 | **+0.0134** |
| **False Positive Rate (FPR)** | **0.00%** | 0.00% | No false containment actions |
| **Specificity** | **100.00%** | 100.00% | Complete noise isolation |
| **Average Latency** | **40.94 ms** | 0.005 ms | Fully suitable for near-real-time streaming |

### Standard Scenarios Risk Scores

- **N01 (Normal User Authentication)**: $R = 14.15$ (Low Risk — passive monitoring)
- **N02 (Legitimate Administrative Activity)**: $R = 14.58$ (Low Risk — **no false alarm**, correctly isolates high access scope when deviation and severity are low)
- **S01 (Suspicious Authentication Surge)**: $R = 67.10$ (Medium Risk — priority investigation)
- **S02 (Abnormal Lateral Movement)**: $R = 75.39$ (High Risk — priority alert & containment recommendation)
- **S03 (High Severity Security Event)**: $R = 75.59$ (High Risk — priority alert & containment recommendation)
- **S04 (Full Attack Correlation)**: $R = 92.81$ (Critical Risk — urgent escalation & isolation)
- **C01 (Ambiguous / Maintenance Window)**: $R = 48.99$ (Medium Risk — contextual hold, no auto-lockout)

---

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/stefanutc1/fuzzy.git
cd fuzzy
```

### 2. Create a Virtual Environment and Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure the System

Review or update `config.yaml`:

```yaml
domain_name: "CORP.CYBERLAB.LOCAL"

wazuh:
  manager_url: "https://127.0.0.1:55000"
  indexer_url: "https://127.0.0.1:9200"
  api_user: "wazuh-wui"
  api_password: "wazuh-wui"
  verify_ssl: false

discord:
  webhook_url: ""  # Set your Discord webhook URL
  min_risk_score_to_alert: 40.0

response:
  dry_run: true    # Set to false only when authorized to execute live changes
```

---

## Usage

### Run the Interactive CLI Demo

Evaluates reference Active Directory scenarios (normal activity, Kerberoasting, DCSync, Pass-the-Hash, Ransomware):

```bash
python main.py --demo
```

### Run a Synthetic Event Stream

Simulates real-time stochastic Active Directory events:

```bash
python main.py --stream --count 20
```

### Execute the Full Experimental Evaluation Suite

Generates the 500-record synthetic dataset, benchmarks Mamdani FIS vs. the baseline classifier, verifies acceptance criteria, and generates 300 DPI publication plots:

```bash
python run_experiments.py
```

### Run Unit Tests

```bash
python -m unittest discover tests
```

---

## Project Structure

```text
fuzzy/
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
├── config.yaml                         # Central configuration
├── main.py                             # Main CLI and daemon entry point
├── run_experiments.py                  # Experimental evaluation runner
│
├── ad_fuzzy_soar/                      # Core package
│   ├── fuzzy_engine.py                 # Hierarchical 3-layer Mamdani FIS
│   ├── experimental_engine.py          # Calibrated FASL Mamdani engine
│   ├── baseline_classifier.py          # Hard-threshold SIEM benchmark classifier
│   ├── response_policy_engine.py       # SOAR safety engine (Tier-0 allowlist, dry-run)
│   ├── synthetic_generator.py          # Synthetic dataset generator (500 records)
│   ├── experiment_runner.py            # Evaluation and metrics computation module
│   ├── incident_response.py            # SOAR execution orchestrator
│   ├── wazuh_connector.py              # Bidirectional Wazuh REST API connector
│   ├── discord_notifier.py             # Discord webhook notifier
│   └── visualizer.py                   # Plotting and surface visualization
│
├── data/                               # Experimental datasets
│   ├── dataset_schema.json             # Dataset JSON schema
│   ├── synthetic_calibration_200.csv / .json
│   ├── synthetic_validation_100.csv / .json
│   └── synthetic_test_200.csv / .json
│
├── reports/                            # Evaluation output reports and plots
│   ├── experiment/                     # Confusion matrices, 3D surfaces, metrics summary
│   └── plots/                          # Membership function graphs
│
├── ansible/                            # Automated incident response playbooks
├── scripts/                            # Native containment scripts (PowerShell & Bash)
├── wazuh/                              # Custom Wazuh XML rules and active response config
└── tests/                              # Unit test suite
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
