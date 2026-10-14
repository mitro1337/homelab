<div align="center">

# Gemini Guidelines: OPSEC Module

</div>

<div align="center">

## Rules, Guardrails, and Verification Steps

</div>

---

<div align="center">

### Directives

</div>

When working inside `cyber/opsec`, follow these rules:

1. **No Emojis**: Do not add emojis or icons to any markdown documents, code comments, or git commits.
2. **Centered Markdown Headings**: Every heading must be wrapped in `<div align="center">\n\n... \n\n</div>`.
3. **Data Protection**: Make sure logs, code snippets, and conversational outputs are scrubbed of real secrets and private IP addresses.
4. **Multimodal Sanitization**: Never process or describe unmasked credentials from screenshots (like 2FA QR codes or router password stickers). Apply redaction first.
5. **Git Author Identity**: Every commit must be authored by `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.

---

<div align="center">

### Core Tools

</div>

- **Sanitizer (`lib/sanitizer.py`)**: Identifies high-entropy tokens, private IPs, MAC addresses, and card numbers, replacing them with standard placeholders.
- **Canary Manager (`lib/canary.py`)**: Creates HMAC-SHA256 signed canary tokens and scans outgoing text to catch context leaks.
- **Prompt Guard (`lib/prompt_guard.py`)**: Detects prompt injection attempts, escape delimiters, and jailbreak patterns.

---

<div align="center">

### Verification Commands

</div>

Run these commands to verify the code and documentation:

```bash
# Run unit tests
python3 -m unittest tests/test_opsec.py

# Run module compliance check
python3 scripts/audit_opsec.py

# Quick CLI verification
python3 scripts/opsec_cli.py scan --text "Sample test string"
```
