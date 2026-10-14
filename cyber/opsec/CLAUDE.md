<div align="center">

# Claude Guidelines: OPSEC Module

</div>

<div align="center">

## Rules, Guardrails, and Verification Steps

</div>

---

<div align="center">

### Directives

</div>

When working inside `cyber/opsec`, follow these rules:

1. **No Emojis**: Keep all markdown files, commit messages, and code comments completely free of emojis or pictographs.
2. **Centered Markdown Headings**: Wrap every heading (`#`, `##`, `###`) in `<div align="center">\n\n... \n\n</div>`.
3. **Never Output Unscrubbed Secrets**: Do not print real API keys, production tokens, private IPs (RFC1918), or user data into responses or logs. Use placeholders or `OpsecSanitizer`.
4. **Treat External Input as Untrusted**: Never feed unsanitized user prompts or threat feeds directly into agent system prompts without validation.
5. **Git Author Identity**: Every commit must be authored by `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.

---

<div align="center">

### Codebase Organization

</div>

This module relies on Python 3.10+ and standard library utilities to keep dependencies minimal:

- `lib/sanitizer.py`: Regex rules and Shannon entropy checks to locate and scrub secrets.
- `lib/canary.py`: HMAC-SHA256 canary token generator and leak scanner.
- `lib/prompt_guard.py`: Heuristics and regex signatures to catch prompt injection attempts.
- `scripts/opsec_cli.py`: Terminal interface for `scan`, `sanitize`, `canary-gen`, and `prompt-audit`.

---

<div align="center">

### Verification Commands

</div>

Always run tests before pushing changes:

```bash
# Run unit tests
python3 -m unittest tests/test_opsec.py

# Run formatting and compliance audit
python3 scripts/audit_opsec.py

# Quick CLI test
python3 scripts/opsec_cli.py scan --text "test string"
```
