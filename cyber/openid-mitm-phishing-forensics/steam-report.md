# Valve Security Incident Disclosure: BitM Steam OpenID Credential Phishing

**Case File Reference:** `SEC-2025-AITM-004` **Classification:** `TLP:CLEAR` **Target Authority:** Valve Corporation Security & Abuse Team (`security@valvesoftware.com` / HackerOne) **Submission Date:** 22 November 2025 **Primary Analyst:** `@stefanutc1` **Category:** Account Takeover, Browser-in-the-Middle (BitM), Unauthorized Family View Persistence & Web API Key Abuse

## Executive Disclosure Overview

To the Valve Corporation Security Team,

This report details an active, sophisticated Adversary-in-the-Middle (AiTM) campaign weaponizing simulated Browser-in-the-Middle (BitM) authentication windows to harvest Steam credentials, bypass Steam Guard two-factor authentication, and establish persistent backdoors via the Steam Web API and Family View PIN locks.

Testing was strictly confined to an isolated, air-gapped laboratory environment utilizing synthetic, throwaway accounts registered exclusively for forensic telemetry collection.

## Technical Evidence & Infrastructure Indicators

### Phishing & Reverse-Proxy Indicators

- **Primary Phishing FQDN:** `cs2-tournament-bracket[.]top`
- **Hosting Provider & ASN:** AS202425 (IP Volume Inc.)
- **Origin IP Address:** `194.38.20.182`
- **SSL Certificate Fingerprint:** `SHA256: 4e82b7d81a9...` (Issued by Let's Encrypt Authority X3)
- **Ingress Relay URI:** `POST https://cs2-tournament-bracket.top/api/v2/auth/steam_callback`

### Threat Actor Modus Operandi

1. **In-Page DOM Emulation:** The phishing page injects an in-DOM draggable window styled to replicate Google Chrome running on Windows 11, complete with a faux address bar displaying `https://steamcommunity.com/openid/login`.
2. **Synchronous Session Extraction:** Attacker infrastructure acts as an automated proxy, capturing `steamLoginSecure` and `sessionid` cookies.
3. **Immediate Account Lockdown:** Within 15 seconds of token acquisition, automated scripts call Steam's internal parental control endpoints (`/parental/ajaxsetparental`) to bind an unauthorized 4-digit PIN, effectively locking the genu...
4. **Trade Offer Hijacking via Web API:** The script provisions a rogue API key at `steamcommunity.com/dev/registerkey` to monitor and intercept high-value CS2 weapon skins and items.

## Recommended Platform Countermeasures

To mitigate the systemic abuse of Steam OpenID and post-exploitation mechanisms, we submit the following platform-level security enhancements for Valve's engineering review:

### Out-of-Band Notification for New Family View Locks

- **Current Behavior:** Family View can be established silently using an existing authenticated web session without triggering a re-authentication challenge or email confirmation.
- **Proposed Enhancement:** Require an email confirmation link or a 12-hour cooling-off grace period before newly configured Family View PINs become active, preventing attackers from immediately locking out victims.

### Mandatory Steam Mobile Push for API Key Registration

- Whenever a Steam Web API Key is registered at `/dev/registerkey`, trigger a high-priority push notification and biometric confirmation prompt via the Steam Mobile App.

### OpenID Single Sign-On Context Binding

- Legitimate OpenID authentication flows should never require manual username/password entry if the user already has an active, authenticated session in the client or browser. The Steam community login should clearly alert users if an ex...

## Submission & Resolution Tracking

- **Date Submitted:** 22 November 2025
- **Status:** Acknowledged by Security Triage; domain suspended by upstream registrar; threat indicators incorporated into global gaming blocklists.
