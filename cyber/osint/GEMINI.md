<div align="center">

# Gemini Guidelines: OSINT Module

</div>

<div align="center">

## Rules, Guardrails, and Verification Steps

</div>

---

<div align="center">

### Directives

</div>

When working inside `cyber/osint`, follow these rules:

1. **No Emojis**: Do not add emojis or icons to any markdown documents, code comments, or git commits.
2. **Centered Markdown Headings**: Every heading must be wrapped in `<div align="center">\n\n... \n\n</div>`.
3. **Passive Reconnaissance**: Do not run or generate commands for active port scanning or web vulnerability testing against external targets. Use passive DNS and public Certificate Transparency queries.
4. **Admiralty Grading**: When analyzing unstructured threat feeds, apply NATO STANAG 2022 ratings (A-F for source reliability, 1-6 for data credibility).
5. **Git Author Identity**: Every commit must be authored by `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.

---

<div align="center">

### Core Tools

</div>

- **Entity Extractor (`lib/entity_extractor.py`)**: Locates and validates IPs, domains, hashes, CVEs, emails, and crypto addresses in raw text.
- **Admiralty Evaluator (`lib/admiralty.py`)**: Computes confidence scores using the STANAG 2022 matrix.
- **Passive Intel (`lib/passive_intel.py`)**: Formats queries for crt.sh and parses apex domains from complex URLs.
- **Synthesizer (`lib/synthesis.py`)**: Compiles indicators and evaluation scores into clean reports.

---

<div align="center">

### Verification Commands

</div>

Run these commands to verify the code and documentation:

```bash
# Run unit tests
python3 -m unittest tests/test_osint.py

# Run module compliance check
python3 scripts/audit_osint.py
```
