# Case Study: E-Commerce Brand Impersonation & Chinese SaaS Fraud Funnel (Media Galaxy Spoof via TikTok)

**Case Reference:** `SEC-2026-ECOM-005` **Classification:** `TLP:CLEAR` **Incident Date:** 16 September 2026 **Primary Investigators:** `@stefanutc1` **Target Entity:** Media Galaxy (Altex România S.A.) **Financial Loss Impact:** ~21 EUR (~112 RON) via BCR (Banca Comercială Română) Debit Card **Status:** Incident Resolved & Remediated, Domain Inactive (DNSC Takedown...

## Context & Incident Overview

In September 2026, a targeted e-commerce fraud operation weaponized sponsored short-form video advertisements on TikTok to impersonate **Media Galaxy**, one of Romania's largest national consumer electronics retailers.

Upon submitting card details, the victim was debited ~21 EUR under the obscure foreign descriptor **`morvethemi london`**.

## Technical Findings & Forensics

1. **Subdomain Masking on Compromised Infrastructure:**  
The attackers leveraged a secondary domain (`voetbalshop-nlco.com`) ostensibly created to clone a Dutch football sportswear portal (`voetbalshop.nl`).
2. **Chinese Origin & Turnkey Phishing SaaS Codebase:**  
Inspection of the rendered DOM revealed that the underlying application was configured with `<html lang="zh-CN">`.
3. **Infrastructure Smoking Gun (`yiyangsaas.com`):**  
Direct service enumeration of the Cloudflare-fronted reverse proxy IP (`104.16.145.247`) revealed an SSL certificate common name pointing directly to `cn: yiyangsaas.com`.
4. **Email Delivery Architecture:**  
   - Dispatcher 1: `Customer Service <noreply@email.worvixglobal.com>` (registered at NameSilo in Feb 2025, using Zoho Mail MX servers).
- Additional items omitted.
Additional forensic intelligence captured the exact deceptive ad creative deployed on Facebook (Evidence Item 27) and the corresponding banking charge (Evidence Item 26).

## Indicators of Compromise (IoCs)

| Indicator | Type | Threat Role | Action |
| :--- | :--- | :--- | :--- |
| `mediagalaxy.voetbalshop-nlco.com` | FQDN | Phishing Landing Subdomain | DNS Sinkhole (0.0.0.0) |
| `dm.voetbalshop-nlco.com` | FQDN | Impersonation Infrastructure | DNSC PNRISC Blacklisted |
| `gonser.voetbalshop-nlco.com` | FQDN | Impersonation Infrastructure | DNSC PNRISC Blacklisted |
| `voetbalshop-nlco.com` | Domain | Base Infrastructure | OPNsense Blocklist |
| `dreamwardrobe.online` | Domain | Shell Merchant / Facebook Scam Descriptor | Payment Fraud Aggregator |
| ... | additional rows omitted |

| `worvixglobal.com` | Domain | Attacker Shell Front & Mail Domain | Mail Gateway Filter & Sinkhole |
| `email.worvixglobal.com` | FQDN | Phishing Order Dispatcher | Mail Reject |
| `info.mailapp-fly.com` | FQDN | Phishing Code Dispatcher | Mail Reject |
| `noreply@email.worvixglobal.com` | Email | Phishing Sender | Blacklist |
| `noreply@info.mailapp-fly.com` | Email | Phishing Sender | Blacklist |
| `MaryxBeckb96@gmail.com` | Email | Attacker Reply-To Drop | Abuse Escalation |
| `brekerfurught@outlook.com` | Email | Attacker Reply-To Drop | Abuse Escalation |
| ... | additional rows omitted |

## Remediation & Incident Response Execution

1. **Compromised Card Lockdown:** The victim immediately froze and blocked the compromised card via George BCR, requesting an emergency card cancellation and reissuance to eliminate recurring unauthorized charges.
2. **Chargeback Dispute:** A formal dispute was initiated with BCR support under Visa/Mastercard Rule 4853 / Condition 13.1 (Merchant Fraud / Misrepresentation), requesting a complete clawback of the ~21 EUR fee.
3. **Perimeter Hardening on OPNsense (`192.168.1.1`):**
   - Ingested `domains.txt` into Unbound DNS Blocklists.
   - Deployed custom Suricata IDS rules (`sid:1000951-1000956`) on WAN and LAN interfaces.
- Additional items omitted.
