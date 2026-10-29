# Incident Response Playbook: E-Commerce Fraud & Financial Chargebacks

**Standard Operating Procedure (SOP):** IR-SOP-ECOM-004 **Target Threat Category:** E-Commerce Brand Spoofing / Social Media Ad Phishing / Unauthorized Financial Transaction **Incident Reference:** `SEC-2026-ECOM-005` (Media Galaxy / TikTok Campaign) **Classification:** `TLP:CLEAR`

## Workflow Architecture & Lifecycle

## Phase 1: Identification & Immediate Triage

1. **Victim Interview & Timeline Reconstruction:**
   - **September 16, 08:17**: Phishing checkout completed via TikTok sponsored ad on `mediagalaxy.voetbalshop-nlco.com`.
   - **September 16, 20:00**: Compromise identified by analyst/family (~12h detection latency).
   - **September 16, 20:15 - 21:25**: Forensic reverse engineering & technical attribution conducted.
   - **September 16, 21:00 - 21:21**: Abuse takedowns filed to Cloudflare, Google Safe Browsing, and Media Galaxy / Altex legal.
- Additional items omitted.

## Phase 2: Containment & Financial Lockdown

1. **Freeze and Block the Compromised Card via George BCR:**
   - Open **George BCR App -> Cards**.
   - Select the affected debit card -> Tap **Freeze / Block (Blochează card)** immediately.
   - Request permanent card cancellation and reissuance of a new card with a fresh 16-digit PAN.
   - Check the George BCR transaction feed for any secondary pending debits or unexpected standing mandates.
- Additional items omitted.

## Phase 3: Financial Remediation & Chargeback Guide

### Visa & Mastercard Chargeback Rules

Under **Visa Dispute Condition 13.1 (Merchandise/Services Not Received)** and **Mastercard Reason Code 4853 (Recurring Transaction / No Delivery / Fraud)**:
- Cardholders are entitled to a full chargeback when merchandise was ordered from a merchant that fails to deliver or represents an impersonated business.
- Since the merchant descriptor displayed on the statement (`morvethemi london`) does not represent a legitimate retail business and the site disappeared into "maintenance" (`v***L The website is under maintenance`), the transaction qual...

### BCR Chargeback & Payment Dispute Filing Procedure

1. Call **BCR Support** (*2227 / +4021.407.42.00) or visit a local BCR branch.
2. Formally report an unauthorized commercial transaction resulting from an e-commerce phishing scam.
3. Cite the exact transaction: `~21 EUR` on 16 September 2026 under merchant descriptor `morvethemi london`.
4. Submit the formal dispute documentation (using [`disclosures/BCR_CHARGEBACK_FRAUD_DISCLOSURE.md`](../disclosures/BCR_CHARGEBACK_FRAUD_DISCLOSURE.md)).
5. When submitting proof, attach:
- Additional items omitted.

#### Dispute Narrative Template (English):

#### Dispute Narrative Template (Romanian):

## Phase 4: Eradication & Takedown Notifications

Send standardized abuse reports to the relevant infrastructure providers:

| Provider | Target IoC | Contact Email / Form | Action Requested |
| :--- | :--- | :--- | :--- |
| **Cloudflare** | `104.16.145.247`, `voetbalshop-nlco.com`, `yiyangsaas.com` | `abuse@cloudflare.com` / `https://abuse.cloudflare.com/` | Terminate reverse proxy & expose origin IP |
| **NameSilo** | `worvixglobal.com` | `abuse@namesilo.com` | Domain suspension (phishing) |
| **eName Technology** | `yiyangsaas.com` | `abuse@ename.com` | Domain suspension & abuse investigation |
| **Zoho Mail** | `mx.zoho.com` (for `worvixglobal.com`) | `abuse@zohocorp.com` | Disable fraudulent mail tenant |
| **Google Abuse** | `MaryxBeckb96@gmail.com` | `https://support.google.com/mail/contact/abuse` | Account suspension for fraud relay |
| ... | additional rows omitted |

## Phase 5: Post-Incident Hardening & Lessons Learned

1. Enforce strict virtual card discipline:
   - For all social media / ad-driven purchases, utilize single-use disposable virtual cards with custom spend limits.
2. Maintain OPNsense Unbound DNS sinkhole blocks (`domains.txt`).
3. Deploy Suricata custom detection rules on gateway interfaces.
4. Report ad sponsor identity directly to TikTok Ad Quality & Safety team.
