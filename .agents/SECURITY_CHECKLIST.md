# Security Checklist for Code Reviews

Use this checklist during every code review to ensure security best practices are followed.

---

## 🔴 Critical Security Checks

*These issues must be fixed before any code can be approved*

### 1. No Hardcoded Secrets

- [ ] No API keys in source code
- [ ] No passwords in source code
- [ ] No database credentials in source code
- [ ] No secret tokens in source code
- [ ] Environment variables used for sensitive configuration

**If found:** Request immediate changes. Secrets should be in `.env` files (not committed) or secure vaults.

---

### 2. Input Validation

- [ ] All user inputs are validated before use
- [ ] Input length limits are enforced
- [ ] Special characters are escaped/sanitized
- [ ] File uploads are validated (type, size, content)
- [ ] No trust in client-side validation alone

**If found:** Request changes. Unvalidated input is the #1 cause of security vulnerabilities.

---

### 3. No SQL Injection

- [ ] Parameterized queries used (not string concatenation)
- [ ] ORM used where appropriate
- [ ] No raw SQL with user input

**If found:** Request immediate changes. SQL injection can lead to complete data compromise.

---

### 4. No Command Injection

- [ ] No `os.system()` with user input
- [ ] No `subprocess` calls with untrusted input
- [ ] No `eval()` or `exec()` with user data
- [ ] No shell=True with user input

**If found:** Request immediate changes. Command injection allows arbitrary code execution.

---

### 5. No Path Traversal

- [ ] File paths validated against expected directory
- [ ] No direct use of user input in file paths
- [ ] Path normalization used (`os.path.realpath()`)

**If found:** Request changes. Path traversal can expose sensitive files.

---

## 🟠 High Security Checks

*Significant security issues that should be fixed before merge*

### 6. Authentication & Authorization

- [ ] Sensitive operations require authentication
- [ ] Users can only access their own data
- [ ] Session tokens are secure and rotated
- [ ] Passwords are hashed (bcrypt, argon2, etc.)
- [ ] No plaintext password storage

**If found:** Request changes. Authorization bypass can lead to data breaches.

---

### 7. Data Protection

- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit (HTTPS)
- [ ] No sensitive data in logs
- [ ] Personal data minimized (collect only what's needed)

**If found:** Request changes. Data exposure violates privacy and may be illegal.

---

### 8. Error Handling

- [ ] Error messages don't reveal internal details
- [ ] Stack traces not shown to users
- [ ] Generic error messages for security-related failures
- [ ] Errors logged securely (no sensitive data in logs)

**If found:** Request changes. Information disclosure helps attackers.

---

### 9. Secure Random

- [ ] `secrets` module used for tokens/passwords (not `random`)
- [ ] Cryptographically secure random for security-sensitive operations
- [ ] Session IDs are sufficiently long and random

**If found:** Request changes. Predictable random can be exploited.

---

## 🟡 Medium Security Checks

*Security improvements that should be addressed*

### 10. Dependencies

- [ ] No dependencies with known vulnerabilities
- [ ] Dependencies are necessary and justified
- [ ] Licenses are compatible with project
- [ ] Dependencies are pinned to specific versions

**If found:** Request update to vulnerable dependencies.

---

### 11. Rate Limiting

- [ ] Authentication endpoints have rate limiting
- [ ] API endpoints have rate limiting (if public)
- [ ] Brute force protection in place

**If found:** Suggest adding rate limiting (may be out of scope for some stories).

---

### 12. CORS & Headers

- [ ] CORS properly configured (if web app)
- [ ] Security headers set (if web app)
- [ ] No unnecessary cross-origin requests

**If found:** Suggest improvements for web-facing code.

---

## 🟢 Low Security Checks

*Security hygiene items to consider*

### 13. Logging & Monitoring

- [ ] Security-relevant events are logged
- [ ] Failed authentication attempts logged
- [ ] Sensitive data not in log output
- [ ] Log files have appropriate permissions

**If found:** Suggest improvements.

---

### 14. Code Security

- [ ] No debug code left in production
- [ ] No commented-out security checks
- [ ] No backdoor accounts or code
- [ ] Assertions not used for security

**If found:** Request cleanup.

---

## Project-Specific: Word Quest

### 15. Student Data Protection

- [ ] Student data stored locally only (no external transmission)
- [ ] No third-party analytics SDKs
- [ ] No tracking cookies or beacons
- [ ] Parent authentication is password-protected
- [ ] Email functionality is opt-in only (if implemented)

**If found:** Request changes. This is critical for an educational product for children.

---

### 16. No External Data Transmission

- [ ] No data sent to external servers without parent consent
- [ ] No analytics tracking
- [ ] No telemetry
- [ ] No automatic updates that could be hijacked

**If found:** Request changes. Word Quest should be offline-first for privacy.

---

## Review Decision Guide

| Issues Found | Recommendation |
|--------------|----------------|
| Any 🔴 Critical | **Request Changes** - Must fix before merge |
| Any 🟠 High | **Request Changes** - Must fix before merge |
| 3+ 🟡 Medium | **Request Changes** - Address before merge |
| 1-2 🟡 Medium | **Approve with Comments** - Fix in follow-up |
| Only 🟢 Low | **Approve** - Nice to fix, not required |
| Only 💡 Suggestions | **Approve** - Optional improvements |

---

## Common Vulnerability Examples

### ❌ BAD: String concatenation in SQL
```python
query = "SELECT * FROM users WHERE name = '" + user_input + "'"
cursor.execute(query)
```

### ✅ GOOD: Parameterized query
```python
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (user_input,))
```

---

### ❌ BAD: Hardcoded API key
```python
API_KEY = "sk-1234567890abcdef"
```

### ✅ GOOD: Environment variable
```python
import os
API_KEY = os.environ.get("API_KEY")
```

---

### ❌ BAD: Using random for tokens
```python
import random
token = random.randint(100000, 999999)
```

### ✅ GOOD: Using secrets for tokens
```python
import secrets
token = secrets.token_hex(16)
```

---

### ❌ BAD: Unvalidated file path
```python
filepath = "/data/" + user_filename
with open(filepath) as f:
    content = f.read()
```

### ✅ GOOD: Validated file path
```python
import os
base_dir = "/data"
filepath = os.path.realpath(os.path.join(base_dir, user_filename))
if not filepath.startswith(base_dir):
    raise ValueError("Invalid path")
with open(filepath) as f:
    content = f.read()
```

---

### ❌ BAD: eval() with user input
```python
result = eval(user_input)
```

### ✅ GOOD: Safe alternative
```python
import ast
result = ast.literal_eval(user_input)  # Only evaluates literals
```

---

**Last Updated:** July 3, 2026  
**Version:** 1.0
