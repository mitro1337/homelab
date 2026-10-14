<div align="center">

# Multi-Agent OSINT Guidelines

</div>

<div align="center">

## Operational Boundaries and Subagent Rules

</div>

---

<div align="center">

### Scope

</div>

Rules for automated subagents gathering and processing threat intelligence in this repository. These safeguards ensure all reconnaissance remains strictly passive and well-documented.

---

<div align="center">

### Subagent Rules

</div>

1. **Zero Emojis**: Keep all markdown outputs, generated logs, and comments clean of Unicode emojis.
2. **Centered Headings**: Wrap headings in `<div align="center">\n\n... \n\n</div>`.
3. **Passive Reconnaissance Only**:
   - Never run active port scanners (like Nmap), brute-force tools, or web application fuzzers against targets.
   - Limit data collection to public records, Certificate Transparency logs, and passive DNS caches.
4. **Admiralty Grading**:
   - Tag every threat indicator or external claim with a NATO STANAG 2022 Admiralty rating.
   - Treat single-source claims as unverified (E5 or F6) until corroborated by another source.
5. **Report Generation**:
   - Format final dossiers through `IntelligenceSynthesizer` and mark appropriate TLP headers (e.g. TLP:CLEAR or TLP:AMBER).

---

<div align="center">

### Inspection Flow

</div>

```mermaid
sequenceDiagram
    autonumber
    participant A as Investigating Agent
    participant E as EntityExtractor
    participant P as PassiveIntelEngine
    participant M as AdmiraltyEvaluator
    participant S as IntelligenceSynthesizer
    participant C as Incident Queue

    A->>E: Ingest Raw Threat Text
    E-->>A: Parsed Indicators (IPs, Domains, Hashes)
    A->>P: Request Passive Lookups (crt.sh, DNS)
    P-->>A: Domain Mappings and Subdomains
    A->>M: Grade Source & Credibility (STANAG 2022)
    M-->>A: Confidence Score
    A->>S: Compile Dossier
    S-->>A: Markdown Report
    A->>C: Deliver to Queue
```

---

<div align="center">

### Pre-Push Checklist

</div>

- [ ] All markdown headings are centered using `<div align="center">...</div>`.
- [ ] No emojis in any markdown, code comments, or commit messages.
- [ ] Unit tests pass: `python3 -m unittest tests/test_osint.py`.
- [ ] Audit passes: `python3 scripts/audit_osint.py`.
- [ ] Commit author is `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.
