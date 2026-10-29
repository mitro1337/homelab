# Technical Forensics & Evidence Analysis

**Case File:** `SEC-2026-ECOM-005` **Target Brand:** Media Galaxy (Altex Romania S.A.) **Threat Category:** Social Engineering / Brand Impersonation / Chinese SaaS Phishing Cluster **Victim Asset Impact:** BCR Debit Card (~21 EUR), Personal Identification Information (PII) **Investigation Date:** 16 September 2026 **Classification:** `TLP:CLEAR` **Analyst:** `@stefanutc1`

## Executive Summary & Attack Chain

On 16 September 2026, an active e-commerce phishing and financial fraud campaign was uncovered targeting Romanian consumers through sponsored promotional ads on TikTok.

The campaign operated on a multi-tier infrastructure:
1. **Lure & Ingestion:** High-volume sponsored advertisements on TikTok presenting deep discounts on consumer electronics, directing users into the in-app browser to a spoofed subdomain: `https://mediagalaxy.voetbalshop-nlco.com`.
2. **Landing Page & Credential Harvesting:** A localized clone of the Media Galaxy checkout and login portal. Victims were prompted for contact information, delivery address, and bank payment card credentials.
3. **Financial Exfiltration:** Payment processing was executed through a merchant descriptor recorded on bank statements as `morvethemi london` (amounting to ~21 EUR / ~105 RON), debited directly from a **BCR (Banca Comercială Română)** ...
4. **Follow-Up Social Engineering & Phishing Lures:** The threat actors deployed automated notifications via SMTP relays using spoofed addresses (`noreply@email.worvixglobal.com`, `noreply@info.mailapp-fly.com`), providing fake purchase ...
5. **Technical Attribution:** Deep packet inspection, SSL certificate fingerprinting, and DOM inspection revealed that the phishing infrastructure was built upon a compromised foreign domain (`voetbalshop-nlco.com`) fronted by Cloudflare...

## Granular Evidence Breakdown

### Evidence Item 01: WorvixGlobal Shell Portal

- **File:** `evidence/01_worvixglobal_fake_portal.png`
- **Source:** Desktop Capture (20:17:47)
- **Observations:** The root domain `worvixglobal.com` hosts an unencrypted (`Not secure | worvixglobal.com`) shell trading template displaying "Your Trusted Partner for Global Trade". This facade was erected to satisfy cursory automated...

### Evidence Item 02: WHOIS Registration of WorvixGlobal

- **File:** `evidence/02_whois_worvixglobal.png`
- **Source:** Desktop Capture (20:19:10)
- **Registrar:** NameSilo, LLC (`whois.namesilo.com`)
- **Creation Date:** 8 February 2025
- **Expiration Date:** 8 February 2027
- Additional items omitted.

### Evidence Item 03 & 04: Email Header Analysis & DKIM Signatures

- **Files:** `evidence/03_phishing_email_headers_mailappfly.png`, `evidence/04_dkim_spf_mailappfly.png`
- **Sender (From):** `mediagalaxy-ro <noreply@info.mailapp-fly.com>`
- **Reply-To:** `mediagalaxy-ro <MaryxBeckb96@gmail.com>`
- **MTA Delivery:** Sent and cryptographically signed (DKIM) by `info.mailapp-fly.com`.
- **Forensic Assessment:** The threat actor abused a bulk mailing SaaS platform (`mailapp-fly.com`) with valid SPF and DKIM signatures to bypass Google Gmail security scoring. Crucially, the `Reply-To` header points directly to an attack...

### Evidence Item 05 & 06: Fraudulent Order Confirmation & Spoofed Media Galaxy Footer

- **Files:** `evidence/05_order_confirmation_worvixglobal.png`, `evidence/06_email_footer_spoofed_mediagalaxy.png`
- **Subject:** `Order Confirmation: Thank You for Your Purchase [229942-177457]`
- **Sender:** `Customer Service <noreply@email.worvixglobal.com>`
- **Recipient:** Target victim inbox (`08:17 AM`)
- **Footer Text:** `"Dacă aveți întrebări, răspundeți la acest e-mail sau contactați-ne la MaryxBeckb96@gmail.com . (c) 2026 mediagalaxy-ro"`
- Additional items omitted.

### Evidence Item 07: WHOIS Intelligence on Compromised Landing Domain

- **File:** `evidence/07_whois_voetbalshop_nlco.png`
- **Target:** `voetbalshop-nlco.com`
- **Created:** 12 March 2026
- **Nameservers:** `amos.ns.cloudflare.com`, `daphne.ns.cloudflare.com`
- **Status:** `clientTransferProhibited`
- Additional items omitted.

### Evidence Item 08, 09 & 10: Phishing Landing Decompilation & Chinese Codebase Attribution

- **Files:** `evidence/08_phishing_subdomain_landing_chinese_notice.png`, `evidence/09_browser_devtools_storage_inspection.png`, `evidence/10_dom_source_zh_cn_login_module.png`
- **URL Visited:** `https://mediagalaxy.voetbalshop-nlco.com` / `https://voetbalshop-nlco.com/en`
- **Visual State:** The portal displayed `"The website is under maintenance"` with an icon labeled `"Warning - m***o"` and `"v***L"`.
- **Browser Heuristics:** Google Chrome automatically displayed the popup: `"Translate page from Chinese (Simplified)?"`
- **DOM Source Code Audit:**
```html <!DOCTYPE html> <html lang="zh-CN"> <head>...</head> <body> <div class="module_login_default" id="module_login"> <div class="module_login_wrapper">...</div> </div> <script type="text/javascript"> window._CEDDE_ET = 0.0468571186; </script> </body> </html> ```
- Additional items omitted.

### Evidence Item 11 & 12: Historical Web Archival Analysis

- **Files:** `evidence/11_wayback_machine_worvixglobal_history.png`, `evidence/12_wayback_machine_snapshot_calendar.png`
- **Wayback Machine Query:** `https://web.archive.org/web/*/worvixglobal.com`
- **Captures:** Only 4 snapshots captured between 9 April 2025 and 29 June 2026.
- **Forensic Assessment:** Extremely low archival presence and lack of organic traffic confirm the domain is an artificial front operated by cybercriminals.

### Evidence Item 13: Certificate Transparency Logs for Landing Domain

- **File:** `evidence/13_crt_sh_certificates_voetbalshop.png`
- **crt.sh Query:** Identity Match `voetbalshop-nlco.com`
- **Certificates Logged:** Rapid sequential issuance between 12 March 2026 and 26 July 2026 across Let's Encrypt, Cloudflare TLS Issuing ECC CA 4, Google Trust Services (WE1, WR1), and Sectigo Limited.
- **SANs:** `*.voetbalshop-nlco.com`, `voetbalshop-nlco.com`.

### Evidence Item 14: Merchant Transaction Audit

- **File:** `evidence/14_merchant_descriptor_investigation.png`
- **Search Query:** `"morvethemi london"`
- **Result:** No registered corporation, retail establishment, or authorized payment facilitator exists in the UK Companies House or global merchant registries under this name. The descriptor was algorithmically generated or mapped throu...

### Evidence Item 15, 16 & 17: Certificate Transparency History for WorvixGlobal

- **Files:** `evidence/15_crt_sh_certificates_worvixglobal_part1.png`, `evidence/16_crt_sh_certificates_worvixglobal_part2.png`, `evidence/17_crt_sh_certificates_worvixglobal_part3.png`
- **crt.sh IDs:** 20+ certificates spanning 8 February 2025 to 3 September 2026.
- **Issuers:** Let's Encrypt, Sectigo, Google Trust Services.
- **SAN Coverage:** Wildcard `*.worvixglobal.com` alongside `www.worvixglobal.com`.

### Evidence Item 18: Ephemeral Ephemerality Verification

- **File:** `evidence/18_wayback_voetbalshop_ephemeral_evidence.png`
- **Wayback Query:** `http://voetbalshop-nlco.com/`
- **Result:** `"No URL has been captured for this URL prefix"`.
- **Forensic Assessment:** The attack surface was ephemeral, weaponized specifically for the duration of the paid TikTok advertising burst and subsequently flipped to "Maintenance" to prevent forensic scanning and search engine indexing.

### Evidence Item 19 & 20: Network Infrastructure Pivot to Backend SaaS

- **Files:** `evidence/19_dns_infrastructure_worvixglobal_zoho.png`, `evidence/20_ssl_cert_yiyangsaas_pivot.png`
- **`worvixglobal.com` Network Mapping:**
  - IP: `104.21.14.99` (Cloudflare AS13335)
  - MX: `mx.zoho.com`, `mx2.zoho.com`, `mx3.zoho.com` (Zoho Mail for C2 communication)
- **`voetbalshop-nlco.com` Direct Pivot:**
- Additional items omitted.

### Evidence Item 21 & 22: WHOIS Profile of `yiyangsaas.com`

- **Files:** `evidence/21_whois_yiyangsaas_china_registrant.png`, `evidence/22_whois_yiyangsaas_ename_registrar.png`
- **Registrar:** `eName Technology Co., Ltd.` (`whois.ename.com` / `www.ename.net`)
- **Creation Date:** 12 September 2023
- **Expiration Date:** 12 September 2027
- **Updated Date:** 13 September 2026
- Additional items omitted.

### Evidence Item 23 & 24: Secondary Account Takeover (ATO) Phase

- **Files:** `evidence/23_fake_password_reset_lure.png`, `evidence/24_fake_verification_code_delivery.png`
- **Subject:** `Reset Your Password`
- **Timestamps:** 16 September 2026 at `13:10:45` & `13:12:09`
- **Target Victim:** `[REDACTED]`
- **Header:** Emblazoned with a spoofed red `MEDIACALAXY` logo.
- Additional items omitted.

### Evidence Item 25: Official DNSC PNRISC Blacklist Enforcement & Takedown

- **File:** `evidence/25_dnsc_blacklist_voetbalshop_block.png`
- **Source:** DNSC Official Blacklist Gateway (`https://blacklist.dnsc.ro/`)
- **Date Added:** 18 September 2026
- **Status:** `Blacklisted`
- **Threat Reason:** `Impersonation`
- Additional items omitted.

### Evidence Item 26: Facebook Lure & Cross-Platform Campaign Link (Dreamwardrobe.online)

- **File:** `evidence/26_facebook_victim_dreamwardrobe_coffee_machine_fraud.png`
- **Source:** Victim Bank Transaction Screenshot (George BCR Mobile Banking)
- **Billing Entity / Descriptor:** `dreamwardrobe.online`
- **Amount Debited:** `-49,72 RON` (`9,99 EUR`)
- **Category Tag:** `Moda` (Fashion hanger icon)
- Additional items omitted.

### Evidence Item 27: Facebook Sponsored Ad Lure (Philips LatteGO 4300 at 51 lei)

- **File:** `evidence/27_facebook_sponsored_ad_mediagalaxy_coffee_machine_51lei.png`
- **Source:** Facebook Mobile Application (Sponsored Feed Ad / Post Sponsorizat)
- **Spoofed Brand / Page:** `Media Galaxy` (official brand identity & logo avatar co-opted)
- **Ad Headline & Copy:**
> *"Espressor Philips LatteGO 4300 la doar 51 lei* > *Datorită închiderii depozitelor noastre din România, lansăm o vânzare online prin care toată lumea poate cumpăra Philips LatteGO 4300 la un preț incredibil* > *Faceți clic pe butonul „Aflați mai multe” de sub post pentru a participa la vânzarea noastră"*
- **Visual Staging & Asset:** Premium Philips LatteGO 4300 coffee machine showcased on a retail display shelf with a counterfeit yellow shelf price tag: `MEDIA GALAXY | PHILIPS LATTEGO 4300 | 51 lei`.
- Additional items omitted.

### Evidence Item 28: Order Delivery Notice Email Headers (StridewiseTrading Spoofing)

- **File:** `evidence/28_delivery_notice_email_header_stridewise.png`
- **Source:** Desktop Webmail Capture (Gmail Web Interface)
- **Subject:** `Order Delivery Notice 229942-177457 (Notificare de livrare a comenzii 229942-177457)`
- **Spam Labeling:** Filtered directly to `Spam` folder by Google Mail heuristics
- **Sender (From):** `Customer Service <noreply@email.stridewisetrading.com>`
- Additional items omitted.

### Evidence Item 29: Order Delivery Notice Body & Fake Logistics Tracking (TrackParcel.de)

- **File:** `evidence/29_delivery_notice_email_body_tracking_lure.png`
- **Source:** Gmail Web Interface (Upper Body Capture)
- **Order Identifier:** `numărul de comandă: 229942-177457`
- **Tracking Identifier:** `EURO20260918100004917`
- **Tracking Portal URL:** `https://www.trackparcel.de/`
- Additional items omitted.
> *"Vă mulțumim pentru achiziție!

### Evidence Item 30: Threat Actor Contact Drop Inbox (brekerfurught@outlook.com)

- **File:** `evidence/30_delivery_notice_email_body_outlook_drop_inbox.png`
- **Source:** Gmail Web Interface (Lower Body & Support Details)
- **Customer Support Mailbox:** `brekerfurught@outlook.com`
- **Call-to-Action Instructions:**
> *"Următoarea operațiune:* > *• Faceți clic pe linkul de mai sus pentru a urmări starea coletului.* > *• Asigurați-vă că adresa de destinație este corectă.* > *• Cineva primește coletul acasă sau îl aranjează în avans.* > *Dacă aveți întrebări despre această livrare, vă rugăm să contactați echipa noastră de asistență clienți.* > *Cutia poștală pentru serviciul clienți:...
- **Forensic Assessment & Direct Threat Actor Correlation:**
- Additional items omitted.

### Section 2.5: Live Airtight Browser Sandbox Probing & Discoveries

In addition to the historical screenshots provided on the Desktop, active forensic probing was conducted using an isolated Google Chrome headless sandbox (`--headless=new --incognito --user-data-dir=/tmp/isolated_chrome_sandbox`) with ephemeral profiles to prevent any client fingerprint leakage.

Key artifacts captured live into `evidence/live_scans/`:
1. **Live Proof of Shared Origin (`104.16.145.247`):** Active DNS resolution confirmed that both `mediagalaxy.voetbalshop-nlco.com` and the central C2 domain `yiyangsaas.com` point to the exact same Cloudflare IP address: `104.16.145.247`.
2. **TikTok Ad Preloading Detection:** Live DOM dumping captured the explicit meta directive:
`<meta name="tiktok-ads-preloading-nocache" content="1">` This proves the threat actor specifically tailored their application to exploit the caching and preloading behavior of TikTok's in-app webview.
3. **Deobfuscated OEMCart Chinese Engine:** Client-side JavaScript execution environment revealed the decoded token `atob("b2VtY2FydF8=") === "oemcart_"`, associated with asset path `/skins/default/guoqi.png` (*guoqi* being Chinese pinyi...
4. **Certificate Timestamping:** OpenSSL certificate extraction verified the active SSL certificate for `mediagalaxy.voetbalshop-nlco.com` (Serial `b4:66:51:7d...`) was issued by Google Trust Services on **September 15, 2026 at 00:43:20 ...
5. **Burned Secondary Dispatchers:** Mail dispatch subdomains `info.mailapp-fly.com` and `email.worvixglobal.com` now resolve to `NXDOMAIN`, confirming threat actors purged their secondary DNS records post-campaign.

Refer to [`evidence/LIVE_WEB_VERIFICATION.md`](evidence/LIVE_WEB_VERIFICATION.md) for full raw dumps and header logs.

## Threat Actor Infrastructure Graph

## MITRE ATT&CK Matrix Mapping

| Tactic | Technique ID | Technique Name | Implementation in Campaign |
| :--- | :--- | :--- | :--- |
| **Resource Development** | `T1583.001` | Acquire Domains | Registered `worvixglobal.com` (NameSilo) and acquired `voetbalshop-nlco.com`. |
| **Resource Development** | `T1583.003` | Virtual Private Server | Deployed C2 backend on `yiyangsaas.com` with Cloudflare proxying. |
| **Resource Development** | `T1584.001` | Compromise Domains | Hijacked/created `mediagalaxy` subdomain on `voetbalshop-nlco.com`. |
| **Initial Access** | `T1566.002` | Spearphishing Link | Sponsored ads on TikTok directing users to cloned e-commerce portal. |
| **Execution** | `T1204.001` | Malicious Link | Victim clicks link inside the TikTok mobile in-app browser. |
| ... | additional rows omitted |
