# Executive Intelligence Briefing: Revolut Vishing & Credential Relay

**Case File Reference:** `SEC-2026-VISH-002` **Classification:** `TLP:CLEAR` **Incident Type:** Social Engineering, Voice Phishing (Vishing) & Real-Time Credential Relay **Investigation Date:** 10 August 2026 **Primary Analyst:** `@stefanutc1` **Target Entity:** FinTech Consumers (Revolut Bank UAB) · Romanian Market

## Incident Overview & Impact Assessment

On **10 August 2026**, a coordinated Voice Phishing (Vishing) campaign targeted mobile banking consumers across Romania.

Impersonating official Revolut Anti-Fraud personnel, the attackers manufactured synthetic panic by claiming the user's account had been compromised by a pending high-value international transaction or negative balance liquidation.

### Key Executive Metrics

| Dimension | Value | Operational Context |
| :--- | :--- | :--- |
| **Ingress Channel** | Voice Call (VoIP SIP Trunk) | Spoofed Romanian mobile CLI (`0749-XXX-XXX`) |
| **Secondary Channel** | SMS / URL Shorteners | Shortened redirection chains masking disposable domains (`.tk`, `.xyz`) |
| **Harvested Assets** | Card PAN, CVV, Exp, SMS OTP | Real-time relay into attacker-automated banking API sessions |
| **Potential Loss** | Uncapped Account Balance | Prevented via rapid call termination and app security triage |
| **National Escalation** | DNSC & Revolut Fraud Operations | Telephony and infrastructure IoCs submitted for regional blacklisting |

## High-Level Attack Timeline

## Threat Actor Profile & Capabilities

- **Telephony Ingress:** Access to commercial SIP trunking providers with permissive Caller ID header injection (`P-Asserted-Identity`), enabling spoofed domestic mobile prefixes.
- **Dynamic Web Engineering:** Utilization of automated web scraping frameworks to deploy pixel-perfect clones of Revolut's web authentication and card management interfaces.
- **Real-Time Token Harvesting:** Deployment of reverse-proxy C2 architectures capable of maintaining active user sessions and requesting two-factor verification codes synchronously while the victim is engaged on the voice call.

## Remediation & Strategic Defense

1. **Zero-Trust Communication Policy:** Financial institutions never contact customers via voice to request payment card CVVs, SMS one-time passwords, or in-app biometric approvals.
2. **Homelab Perimeter Defense:** All identified domains and IP addresses were immediately appended to `cyber/forbidden_domains.txt` and sinkholed on the OPNsense perimeter router (`192.168.1.134`).
3. **Cross-Reference Documentation:**
   - Full technical breakdown: [`technical-analysis.md`](technical-analysis.md)
   - Formal banking incident disclosure: [`revolut-report.md`](revolut-report.md)
- Additional items omitted.
