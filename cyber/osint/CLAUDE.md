<div align="center">

# Claude Guidelines: OSINT Module

</div>

<div align="center">

## Rules, Guardrails, and Verification Steps

</div>

---

<div align="center">

### Directives

</div>

When working inside `cyber/osint`, follow these rules:

1. **No Emojis**: Keep all markdown files, commit messages, and comments completely free of emojis or pictographs.
2. **Centered Markdown Headings**: Wrap every heading (`#`, `##`, `###`) in `<div align="center">\n\n... \n\n</div>`.
3. **Passive Reconnaissance Only**: Never suggest or execute active network scans, port probes (e.g. Nmap SYN scans), or intrusive brute-force attacks against third-party systems. Keep lookups passive (DNS records, Certificate Transparency, RDAP, public registries).
4. **Admiralty Grading**: When evaluating external intelligence or IOC claims, assign a NATO STANAG 2022 Admiralty rating (e.g. B2, C3).
5. **Git Author Identity**: Every commit must be authored by `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.

---

<div align="center">

### Codebase Organization

</div>

This module runs on Python 3.10+ using the standard library:

- `lib/entity_extractor.py`: Regex extraction of IPs, domains, hashes, CVEs, emails, and wallet addresses.
- `lib/admiralty.py`: Scoring matrices and confidence calculations for source reliability (A-F) and credibility (1-6).
- `lib/passive_intel.py`: URL and domain parsing, crt.sh query generation, and passive DNS profile helpers.
- `lib/synthesis.py`: Formats parsed data and confidence scores into structured markdown reports.
- `scripts/osint_cli.py`: Terminal interface for `extract`, `score`, `recon`, and `synthesize`.

---

<div align="center">

### Verification Commands

</div>

Run these commands before pushing any changes:

```bash
# Run unit tests
python3 -m unittest tests/test_osint.py

# Run module compliance check
python3 scripts/audit_osint.py

# Quick extraction test
python3 scripts/osint_cli.py extract --text "Sample C2 at 198.51.100.12 with domain threat-sample.org"
```
