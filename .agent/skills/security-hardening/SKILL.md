---
name: security-hardening
description: System security, vulnerability prevention, and infrastructure protection.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Security Hardening

> **Defense in Depth.**

---

## The OWASP Mentality

1. **Injection:** Sanitize ALL inputs. Use parameterized queries.
2. **Broken Auth:** Use MFA, strong hashing (Argon2, bcrypt).
3. **Sensitive Data Exposure:** Encrypt at rest and in transit (TLS).
4. **XSS / CSRF:** Content Security Policy (CSP), CSRF tokens.

---

## Infrastructure Hardening

- **Firewalls:** Principle of Least Privilege.
- **SSH:** Disable password auth, use keys.
- **Updates:** Automated security patching.
- **Secrets:** Use Secret Managers (Vault, AWS Secrets Manager).

---

## Application Security

- **CORS:** Restrict origins.
- **Headers:** `Helmet`, `Strict-Transport-Security`, `X-Frame-Options`.
- **Rate-limiting:** Protect against DoS/Brute-force.
- **Auditing:** Regular dependency scans and security logs.

---

## Related Skills

| Task | Skill |
|------|-------|
| Vulnerability Scanning | `@[skills/vulnerability-scanner]` |
| Red Team Tactics | `@[skills/red-team-tactics]` |
| API Security | `@[skills/api-patterns]` |

---

> **Remember:** Security is a process, not a product.
