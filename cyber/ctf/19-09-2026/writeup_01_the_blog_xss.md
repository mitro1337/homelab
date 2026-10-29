# Technical Write-Up: The Blog (Stored XSS & Context Exfiltration)

## Challenge Specification

- **Target Application**: Standard blogging engine with articles and a public contact submission form (`/contact`).
- **Simulated Environment**: An editorial bot with authenticated administrative privileges periodically navigates to the inbox in a real browser instance and opens unread messages.
- **Flag Format**: `InvataCyber{...}`

## Attack Surface Analysis & Root Cause

The application exposes two primary components:
1. **Public Ingress**: Contact submission form at `/contact` accepting `name`, `email`, and `message` via HTTP POST.
2. **Privileged Background Bot**: A headless browser (Puppeteer / Chromium) operating with active session cookies on the internal `/admin` route.

### Vulnerability Mechanism

The server stores incoming messages in its database without applying contextual HTML entity encoding (e.g.

Even if session cookies are protected with the `HttpOnly` flag (preventing direct `document.cookie` theft), the bot executes in an authenticated browser state.

## Exploit Payload Engineering

The payload executes in three sequential stages:
1. Issues an asynchronous `fetch()` request to `/admin`.
2. Converts the response stream to raw text.
3. Transmits the response text (containing the flag) to an external webhook.

Wrapped in a `<script>` tag for injection into the `message` field:

## Automated Python Solver (`solver.py`)

## Remediation & Hardening Recommendations

1. **Context-Aware Output Encoding**: Ensure all user-supplied input rendered in HTML templates is encoded (e.g. using Jinja2 automatic escaping or React DOM bindings).
2. **Content Security Policy (CSP)**: Deploy strict CSP headers forbidding unauthorized inline scripts and restricting outbound network connections:
```http Content-Security-Policy: default-src 'self'; script-src 'nonce-<RANDOM>'; connect-src 'self'; ```
3. **DOMPurify Sanitization**: If rich-text HTML rendering is required, sanitize markup using DOMPurify before DOM insertion.
