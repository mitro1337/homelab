# Technical Write-Up: Portal InvataCyber.ro (Blind SQL Injection & Admin Takeover)

## Challenge Specification

- **Target Application**: Maintenance / lockdown portal with authentication modules hidden from the public interface.
- **Tracking Mechanism**: The application sets and reads a tracking cookie (`TrackingId`) to identify returning visitors. When the cookie value matches an active database record, a unique banner is displayed; when it does not match, a di...
- **Objective**: Discover the hidden administrative console and recover credentials to extract the flag.
- **Flag Format**: `InvataCyber{...}`

## Attack Surface Analysis & Root Cause

Upon inspecting HTTP traffic, the web server reads the `TrackingId` cookie:

The application queries the database backend:

When this query returns a valid record, the application includes a welcome message in the response body, producing an exact response length of **5,652 bytes**.

Because data is not directly reflected in page content and no database error traces are displayed, this behavior creates an ideal **Blind Boolean-Based SQL Injection Oracle**.

## Vulnerability Verification (PoC Oracle)

Testing boolean conditional logic using [`sql_solve.py`](scripts/sql_solve.py):

* **Condition True**:
```http Cookie: TrackingId=base-tracking-id-123' OR '1'='1 ``` Result: Response size is `5652 bytes` (banner present).

* **Condition False**:
```http Cookie: TrackingId=base-tracking-id-123' OR '1'='2 ``` Result: Response size is not `5652 bytes` (banner absent).

This confirms the presence of an injectable SQLite database backend.

## Automated Database Schema & Credential Exfiltration

Using automated Python scripts ([`dump_sqlite.py`](scripts/dump_sqlite.py), [`dump_schema.py`](scripts/dump_schema.py), and [`dump_users.py`](scripts/dump_users.py)), binary-search character extraction was executed against `sqlite_master` and internal tables.

### Schema Extraction Query

Recovered Table DDL:

### Credential Dumping Query

Recovered Credentials:
- **Username**: `admin`
- **Password**: `<extracted_cleartext_password>`

## Administrative Console Discovery & Flag Capture

Executing the endpoint scanner [`solver_portal.py`](scripts/solver_portal.py) revealed the hidden administrative route:
- Route: `/console`
- Authenticating with recovered credentials yielded full administrative access and revealed the flag:
`InvataCyber{b1ind_sq1i_d4t4b4s3_3xfi1tr4t10n_succ3ss}`

## Remediation & Hardening Recommendations

1. **Parameterized Prepared Statements**: Replace dynamic string concatenation with parameterized SQL queries:
```python cursor.execute("SELECT tracking_id FROM tracking WHERE tracking_id = ?", (cookie_val,)) ```
2. **Web Application Firewall (WAF)**: Deploy Suricata / ModSecurity rules detecting SQL injection metacharacters (`'`, `OR`, `SELECT`, `sqlite_master`) in HTTP headers.
3. **Cookie Validation**: Enforce strict cryptographic HMAC signing on tracking cookies to prevent client-side manipulation.
