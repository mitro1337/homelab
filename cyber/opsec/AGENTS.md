<div align="center">

# Multi-Agent OPSEC Guidelines

</div>

<div align="center">

## Operational Boundaries and Subagent Rules

</div>

---

<div align="center">

### Scope

</div>

Rules for automated subagents executing tasks in this repository. These safeguards prevent prompt injection, data leaks, and credential exposure across multi-agent workflows.

---

<div align="center">

### Subagent Rules

</div>

1. **Zero Emojis**: Keep all markdown outputs, generated logs, and comments clean of Unicode emojis.
2. **Centered Headings**: Wrap headings in `<div align="center">\n\n... \n\n</div>`.
3. **Execution Isolation**:
   - Subagents must work strictly within their assigned project folder.
   - Do not make outbound network calls unless explicitly required by the task.
4. **Data Sanitization**:
   - Run `OpsecSanitizer` before writing logs or committing files containing raw telemetry.
   - Quarantine unexpected sensitive data immediately.
5. **Canary Trap Handling**:
   - Never print or leak canary tokens created by `CanaryManager`.
   - If a known canary token appears in an untrusted payload, stop the run and alert the user.

---

<div align="center">

### Inspection Flow

</div>

```mermaid
sequenceDiagram
    autonumber
    participant U as Operator
    participant O as OPSEC Orchestrator
    participant S as Sanitizer Worker
    participant C as Canary Guard
    participant T as Target System

    U->>O: Dispatch Task
    O->>O: Evaluate Prompt via PromptGuard
    O->>C: Register Canary Token
    O->>S: Scrub Input Arguments
    S-->>O: Clean Arguments
    O->>T: Execute Command
    T-->>O: Raw Telemetry Output
    O->>C: Check Canary Tripwires
    O->>S: Scrub Output Artifacts
    S-->>O: Clean Artifacts
    O-->>U: Deliver Results
```

---

<div align="center">

### Pre-Push Checklist

</div>

- [ ] All markdown headings are centered using `<div align="center">...</div>`.
- [ ] No emojis in any markdown, code comments, or commit messages.
- [ ] Unit tests pass: `python3 -m unittest tests/test_opsec.py`.
- [ ] Audit passes: `python3 scripts/audit_opsec.py`.
- [ ] Commit author is `stefanutc1 <321888485+stefanutc1@users.noreply.github.com>`.
