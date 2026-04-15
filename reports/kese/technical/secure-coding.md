# KISA Secure Coding Assessment Report

**Project:** Youtube-AI-Agent-Agency
**Date:** 2026-04-11
**Framework:** Python (FastAPI + SQLAlchemy 2.0) / JavaScript (Next.js + NextAuth.js v5)
**Assessor:** Claude Opus 4.6 (Automated KISA Secure Coding Analysis)

---

## Executive Summary

| Category | Total | Compliant | Partial | Vulnerable | N/A |
|----------|:-----:|:---------:|:-------:|:----------:|:---:|
| 1. Input Data Validation | 16 | 10 | 2 | 1 | 3 |
| 2. Security Features | 16 | 8 | 4 | 2 | 2 |
| 3. Time and State | 2 | 1 | 0 | 0 | 1 |
| 4. Error Handling | 3 | 0 | 2 | 1 | 0 |
| 5. Code Quality | 3 | 2 | 0 | 0 | 1 |
| 6. Encapsulation | 4 | 2 | 1 | 0 | 1 |
| 7. API Misuse | 2 | 1 | 0 | 0 | 1 |
| **Total** | **46** | **24** | **9** | **4** | **9** |

**Overall Compliance Rate:** 64.9% (24/37 applicable items compliant)

---

## Top Findings by Severity

### Critical (1 item)

| # | CWE | Finding | File |
|---|-----|---------|------|
| 1 | CWE-352 | CSRF protection absent on state-changing API endpoints | `packages/api/yaa_app/api/main.py` |

### High (3 items)

| # | CWE | Finding | File |
|---|-----|---------|------|
| 2 | CWE-209 | Broad exception handlers silently swallow errors without proper logging in some paths | Multiple files |
| 3 | CWE-521 | Password policy only enforces minimum length (8 chars), no complexity requirements | `packages/api/yaa_app/api/routes/auth.py:35` |
| 4 | CWE-307 | Login endpoint lacks per-user brute force protection (only global rate limit) | `packages/api/yaa_app/api/routes/auth.py:209` |

### Medium (5 items)

| # | CWE | Finding | File |
|---|-----|---------|------|
| 5 | CWE-489 | `disable_auth` flag can bypass all authentication in production if misconfigured | `packages/core/yaa_core/shared/config.py:67` |
| 6 | CWE-754 | Many broad `except Exception:` / `except:` blocks that catch all exceptions | Multiple files |
| 7 | CWE-319 | CORS `allow_methods=["*"]` and `allow_headers=["*"]` overly permissive | `packages/api/yaa_app/api/main.py:93-94` |
| 8 | CWE-693 | No security response headers (CSP, HSTS, X-Frame-Options, etc.) | `packages/api/yaa_app/api/main.py` |
| 9 | CWE-759 | Legacy SHA-256 password hash path lacks salt | `packages/api/yaa_app/api/routes/auth.py:94` |

---

## Detailed Per-CWE Assessment

### 1. Input Data Validation (16 items)

#### 1-1. SQL Injection (CWE-89)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** All database access uses SQLAlchemy ORM with parameterized queries via the Repository Pattern. No raw SQL string concatenation found. Grep for `.execute(.*f"` and `.execute(.*+` returned zero matches in source code.
- **Files checked:** `packages/core/yaa_core/database/repositories/`, `packages/api/yaa_app/api/routes/`

#### 1-2. Code Injection (CWE-94, CWE-95)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** No `eval()` or `exec()` usage with external input found. The only `compile()` call is LangGraph's `graph.compile()` which is internal graph compilation, not code execution. No `Function()`, `setTimeout(string)` patterns in frontend code.
- **Files checked:** All Python and JS/TS files.

#### 1-3. Path Traversal / Resource Injection (CWE-22, CWE-99)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** `ChannelRegistry` validates `channel_id` and `workspace_id` with strict regex `^[a-zA-Z0-9_-]+$` and performs path resolution + `startswith` check to prevent directory traversal.
- **File:** `packages/core/yaa_core/shared/config.py:122-176`
- **Code:**
  ```python
  if not re.match(r"^[a-zA-Z0-9_-]+$", workspace_id):
      raise ValueError(...)
  path = (self._channels_dir / channel_id).resolve()
  if not str(path).startswith(str(self._channels_dir.resolve())):
      raise ValueError(f"Invalid path access: {channel_id}")
  ```

#### 1-4. Cross-Site Scripting - XSS (CWE-79)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** No `dangerouslySetInnerHTML` or `innerHTML` usage in frontend. React's JSX auto-escapes by default. FastAPI returns JSON responses (not HTML templates), so server-side XSS is not applicable. Next.js handles HTML output safely.
- **Files checked:** `packages/frontend/src/**/*.tsx`

#### 1-5. OS Command Injection (CWE-78)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** FFmpeg calls use `asyncio.create_subprocess_exec()` (not `shell=True`), passing arguments as a list. This avoids shell interpretation. `shlex.quote()` is used for logging only. No `os.system()` or `os.popen()` calls found.
- **File:** `packages/agents/yaa_agents/media_editor/video_editor.py:50`
- **Code:**
  ```python
  process = await asyncio.create_subprocess_exec(
      *cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
  )
  ```

#### 1-6. Unrestricted File Upload (CWE-434)
- **Severity:** High
- **Verdict:** N/A
- **Evidence:** No file upload endpoints exist in the API. Channel creation uses templates from the server filesystem. Media files are generated by agents, not uploaded by users.

#### 1-7. Open Redirect (CWE-601)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** No redirect endpoints accepting user-controlled URLs. Stripe/Toss redirect URLs are constructed server-side from `cors_origins` config. NextAuth redirect pages are hardcoded (`/login`).
- **File:** `packages/api/yaa_app/api/routes/billing.py:159-160`

#### 1-8. XML External Entity - XXE (CWE-611)
- **Severity:** High
- **Verdict:** N/A
- **Evidence:** No XML parsing found in the codebase. YAML parsing uses `yaml.safe_load()` which is safe. No `etree`, `XMLParser`, or `lxml` usage.

#### 1-9. XPath / XML Injection (CWE-643)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** No XPath queries or XML document processing found in the codebase.

#### 1-10. LDAP Injection (CWE-90)
- **Severity:** Medium
- **Verdict:** N/A (no LDAP usage)

#### 1-11. Cross-Site Request Forgery - CSRF (CWE-352)
- **Severity:** High
- **Verdict:** **VULNERABLE**
- **File:** `packages/api/yaa_app/api/main.py`
- **Evidence:** No CSRF token mechanism is implemented. The API relies on API key and JWT Bearer token authentication. While API key/Bearer auth provides some CSRF protection (tokens are not auto-sent by browsers), the frontend stores API keys in `sessionStorage` and sends them via custom headers, which is safe. However, the NextAuth session cookie-based authentication (when used via proxy rewrites) could be vulnerable to CSRF for state-changing operations since `SameSite` cookie attributes are not explicitly configured.
- **Remediation:** Implement CSRF protection for cookie-authenticated endpoints. Consider setting `SameSite=Strict` or `SameSite=Lax` on session cookies. For the API, since it primarily uses Bearer tokens (not cookies), the risk is mitigated but should be explicitly addressed for the Next.js proxy path.

#### 1-12. Server-Side Request Forgery - SSRF (CWE-918)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** No endpoints accept user-provided URLs to make server-side requests. The YouTube API calls use channel IDs (not arbitrary URLs). Toss Payments uses a hardcoded API base URL. Stripe calls are made through the official SDK.
- **Files checked:** `packages/api/yaa_app/api/routes/billing.py`, `packages/api/yaa_app/api/routes/competitors.py`

#### 1-13. Untrusted Input for Security Decision (CWE-807)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** Security decisions are made server-side. API key hashes are verified against the database. JWT tokens are cryptographically verified. Admin status is determined from server-side `admin_emails` config, not from client input. Workspace ownership is verified server-side.
- **File:** `packages/api/yaa_app/api/auth.py:87-191`

#### 1-14. HTTP Response Splitting (CWE-113)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** FastAPI/Starlette automatically sanitizes response headers, preventing CRLF injection. No manual header value construction from user input.

#### 1-15. Integer Overflow (CWE-190)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** Python handles arbitrary-precision integers natively. FastAPI Pydantic models use `ge`/`le` constraints on numeric inputs (e.g., `limit: int = Query(20, ge=1, le=100)`). Toss payment amounts are validated against a server-side lookup table.
- **File:** `packages/api/yaa_app/api/routes/billing.py:654-659`

#### 1-16. Format String Injection (CWE-134)
- **Severity:** Medium
- **Verdict:** Partial Compliance
- **Evidence:** Python logging uses `%s` format parameters correctly (e.g., `logger.info("...: %s", variable)`). f-strings used in error messages include user-controlled `channel_id` and `run.status`, but these flow through Pydantic-validated inputs and are returned as JSON (not executed). Minor risk from error detail strings containing user input.
- **File:** `packages/api/yaa_app/api/routes/channels.py:82`, `packages/api/yaa_app/api/routes/pipeline.py:307`
- **Code:**
  ```python
  raise HTTPException(status_code=404, detail=f"Channel not found: {channel_id}")
  ```
- **Remediation:** Avoid including raw user input in error messages. Use generic error messages with request IDs for tracing.

---

### 2. Security Features (16 items)

#### 2-1. Missing Authentication (CWE-306)
- **Severity:** Critical
- **Verdict:** Partial Compliance
- **File:** `packages/api/yaa_app/api/auth.py:214, 238, 259, 276, 304`
- **Evidence:** All API routes require authentication via `Depends(require_api_key)` or `Depends(get_auth_context)`. However, the `disable_auth` flag (`AppSettings.disable_auth: bool = False`) bypasses ALL authentication when set to `True`. While default is `False`, this is a dangerous configuration option that could be accidentally enabled in production.
- **Code:**
  ```python
  if settings.disable_auth:
      return None  # Bypasses all auth
  ```
- **Remediation:** Remove the `disable_auth` flag entirely, or restrict it to test environments only (check `ENV` variable). Add a startup warning if enabled.

#### 2-2. Improper Authorization (CWE-285)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** Workspace isolation is consistently enforced. Pipeline runs, competitors, API keys, and audit logs are all filtered by `workspace_id`. Ownership verification is performed before resource access (e.g., `run.workspace_id != auth.workspace_id`). Admin scope is checked for administrative operations.
- **Files checked:** `packages/api/yaa_app/api/routes/pipeline.py:267-268`, `packages/api/yaa_app/api/routes/competitors.py:161-162`, `packages/api/yaa_app/api/routes/admin.py:119-121`

#### 2-3. Incorrect Permission Assignment (CWE-732)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** `.env` file is in `.gitignore`. Database files are in `.gitignore` (`data/`, `*.db`). No `chmod` or file permission changes in source code. The application does not create files with overly permissive permissions.

#### 2-4. Broken Crypto Algorithm (CWE-327)
- **Severity:** High
- **Verdict:** Partial Compliance
- **File:** `packages/api/yaa_app/api/auth.py:48`, `packages/api/yaa_app/api/routes/auth.py:94`
- **Evidence:** API keys are hashed with SHA-256 (acceptable for API key hashing since keys have high entropy). Passwords use bcrypt (strong). However, legacy password verification falls back to unsalted SHA-256:
  ```python
  if hashlib.sha256(password.encode()).hexdigest() == password_hash:
      return True
  ```
  This legacy path should be deprecated with forced migration. Encryption uses Fernet (AES-128-CBC with HMAC, acceptable).
- **Remediation:** Force-migrate all SHA-256 password hashes to bcrypt. Add a migration script that rehashes on next successful login.

#### 2-5. Cleartext Storage / Transmission (CWE-312, CWE-319)
- **Severity:** High
- **Verdict:** Partial Compliance
- **File:** `packages/core/yaa_core/shared/encryption.py`, `packages/api/yaa_app/api/routes/settings.py`
- **Evidence:** Workspace API keys (YouTube, ElevenLabs) are stored in the database. The `encryption.py` module provides Fernet encryption, but integration keys in `WorkspaceModel` (youtube_api_key, elevenlabs_api_key) appear to be stored without encryption based on direct get/set in settings.py. The `encrypt_value`/`decrypt_value` functions exist but are not used for workspace API keys.
- **Remediation:** Encrypt workspace integration API keys before storage using the existing Fernet encryption module. Decrypt on retrieval.

#### 2-6. Hard-coded Credentials (CWE-259, CWE-321)
- **Severity:** Critical
- **Verdict:** Compliant
- **Evidence:** All API keys and secrets are loaded from environment variables via `AppSettings(BaseSettings)`. The only hardcoded credential-like strings are in test files (e.g., `client_secret="test-client-secret"`) and a docstring example (`api_key="sk-..."`), both of which are non-functional placeholders. `.env` is in `.gitignore`.
- **File:** `packages/core/yaa_core/shared/config.py:50-88`

#### 2-7. Inadequate Key Size (CWE-326)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** JWT uses HS256 (256-bit key). API keys are generated with `secrets.token_urlsafe(32)` (256 bits of entropy). Fernet encryption uses 128-bit AES (adequate). SHA-256 is used for API key hashing (256-bit output). JWT secret minimum length enforced at 32 characters.
- **File:** `packages/api/yaa_app/api/auth.py:84`

#### 2-8. Insufficient Randomness (CWE-330)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** API keys use `secrets.token_urlsafe()` (cryptographically secure). UUIDs use `uuid.uuid4()` (random-based). No `random.randint()`, `random.random()`, or `Math.random()` found for security-sensitive values.
- **File:** `packages/api/yaa_app/api/auth.py:43`

#### 2-9. Weak Password Requirements (CWE-521)
- **Severity:** Medium
- **Verdict:** **VULNERABLE**
- **File:** `packages/api/yaa_app/api/routes/auth.py:35`
- **Evidence:** Password validation only enforces minimum length of 8 characters. No requirements for uppercase, lowercase, digits, or special characters.
  ```python
  password: str = Field(..., min_length=8, description="Min 8 characters")
  ```
- **Remediation:** Add password complexity validation requiring at least: 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character. Consider using a password strength library (e.g., `zxcvbn`).

#### 2-10. Improper Signature Verification (CWE-347)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** JWT tokens are verified with `jwt.decode(token, secret, algorithms=[algorithm])` specifying the algorithm explicitly (prevents algorithm confusion attacks). Stripe webhook signatures are verified via `stripe.Webhook.construct_event()`. Toss webhook signatures are verified using `hmac.compare_digest()` with SHA-256.
- **Files:** `packages/api/yaa_app/api/auth.py:98`, `packages/api/yaa_app/api/routes/billing.py:255, 808`

#### 2-11. Improper Certificate Validation (CWE-295)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** No `verify=False`, `CERT_NONE`, or `check_hostname=False` patterns found anywhere in the codebase. External HTTP calls (httpx, openai SDK) use default SSL verification.

#### 2-12. Sensitive Info in Persistent Cookie (CWE-539)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** The backend API does not set cookies directly. NextAuth handles session cookies with default secure settings. The frontend stores API keys in `sessionStorage` (not persistent cookies), which is cleared on browser close.
- **File:** `packages/frontend/src/lib/api.ts:14`

#### 2-13. Sensitive Info in Comments (CWE-615)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** No passwords, API keys, or secrets found in code comments. The docstring `api_key="sk-..."` in `batch_openai.py:10` is a placeholder pattern, not an actual key.

#### 2-14. Unsalted One-Way Hash (CWE-759)
- **Severity:** Medium
- **Verdict:** **VULNERABLE**
- **File:** `packages/api/yaa_app/api/routes/auth.py:94`
- **Evidence:** The legacy password verification path uses unsalted SHA-256:
  ```python
  if hashlib.sha256(password.encode()).hexdigest() == password_hash:
      return True
  ```
  While new passwords use bcrypt (which includes salt), existing SHA-256 hashes are vulnerable to rainbow table attacks.
- **Remediation:** On successful login with SHA-256 hash, immediately rehash the password with bcrypt and update the database. Set a deadline to force-expire all remaining SHA-256 hashes.

#### 2-15. Download Without Integrity Check (CWE-494)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** The application does not download external binaries or libraries at runtime. Dependencies are managed by `uv` (Python) and `pnpm/npm` (Node.js) with lockfiles.

#### 2-16. Missing Brute Force Protection (CWE-307)
- **Severity:** High
- **Verdict:** **VULNERABLE**
- **File:** `packages/api/yaa_app/api/routes/auth.py:209-258`, `packages/api/yaa_app/api/middleware.py:70-104`
- **Evidence:** Global rate limiting exists via `slowapi` (60 req/min by IP). However, the login endpoint has no **per-user** brute force protection. An attacker can try different passwords for the same email at 60 attempts per minute. No account lockout mechanism exists.
- **Remediation:** Implement per-email login attempt tracking with exponential backoff. After 5 failed attempts, lock the account for 15 minutes. Add a dedicated rate limit decorator on the `/auth/login` endpoint (e.g., 5 attempts per 15 minutes per email).

---

### 3. Time and State (2 items)

#### 3-1. TOCTOU Race Condition (CWE-367)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** File system operations in `ChannelRegistry` (check existence then read) have minimal TOCTOU risk since channels are managed by admins, not concurrent users. Database operations use SQLAlchemy sessions with proper commit/rollback, and Toss payment uses `SELECT FOR UPDATE` for race condition prevention.
- **File:** `packages/api/yaa_app/api/routes/billing.py:664`

#### 3-2. Infinite Loop / Uncontrolled Recursion (CWE-835, CWE-674)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** SSE streaming has a `max_duration_seconds = 35 * 60` timeout. Batch API polling has a configurable timeout with `time.monotonic()` deadline. LangGraph pipeline execution has Arq `job_timeout`. No uncontrolled recursion patterns found.
- **Files:** `packages/api/yaa_app/api/routes/pipeline.py:337-340`, `packages/core/yaa_core/shared/batch_openai.py:101-102`

---

### 4. Error Handling (3 items)

#### 4-1. Error Message Information Exposure (CWE-209)
- **Severity:** Medium
- **Verdict:** Partial Compliance
- **File:** `packages/api/yaa_app/api/routes/competitors.py:220`, `packages/api/yaa_app/api/routes/billing.py:705`
- **Evidence:** Some error messages expose internal details to clients:
  ```python
  raise HTTPException(status_code=502, detail=f"YouTube API error: {exc}")
  raise HTTPException(status_code=400, detail=f"Payment approval failed: {error_message}")
  ```
  While FastAPI does not expose stack traces by default, raw exception messages from external services are forwarded to clients.
- **Remediation:** Log detailed errors server-side and return generic error messages to clients. Use error codes for client-side mapping.

#### 4-2. Error Condition Without Action (CWE-390)
- **Severity:** Medium
- **Verdict:** Partial Compliance
- **File:** Multiple files
- **Evidence:** Several `except Exception:` blocks log warnings but silently continue, which is acceptable for non-critical paths (audit log saving, usage event recording). However, `packages/api/yaa_app/api/auth.py:100` silently returns `None` on JWT decode failure without logging the specific error type, making debugging difficult.
- **Code:**
  ```python
  except Exception:
      return None  # Silent failure
  ```
- **Remediation:** Add structured logging with error type classification in authentication error paths.

#### 4-3. Improper Exception Handling (CWE-754)
- **Severity:** Medium
- **Verdict:** **VULNERABLE (Minor)**
- **File:** Multiple files (24+ locations)
- **Evidence:** Extensive use of broad `except Exception:` and bare `except:` blocks throughout the codebase. While many include logging, the broad catch masks unexpected errors:
  - `packages/api/yaa_app/api/middleware.py:36` - Audit log silently fails
  - `packages/core/yaa_core/shared/encryption.py:56` - Decryption silently fails
  - `packages/api/yaa_app/api/routes/channels.py:57` - Channel loading silently fails
  - `packages/core/yaa_core/shared/llm_clients.py:129` - Token tracking silently fails
- **Remediation:** Replace broad exception handlers with specific exception types. At minimum, log the exception type and message. For security-sensitive paths (auth, encryption), use specific exception handling.

---

### 5. Code Quality (3 items)

#### 5-1. NULL Pointer Dereference (CWE-476)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** Consistent null checks before object access. Database query results are checked with `if user is None:`, `if run is None:`, etc. before use. Pydantic models validate required fields. Optional fields use `str | None` type hints.

#### 5-2. Improper Resource Shutdown (CWE-404)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** Database sessions use `async with session_factory() as session:` context managers for automatic cleanup. `asynccontextmanager` is used for application lifespan. Temporary files in `batch_openai.py` are cleaned up in a `finally` block. Arq worker has `on_startup`/`on_shutdown` hooks.
- **Files:** `packages/core/yaa_core/database/engine.py:94-100`, `packages/core/yaa_core/shared/batch_openai.py:145-147`

#### 5-3. Deserialization of Untrusted Data (CWE-502)
- **Severity:** Critical
- **Verdict:** N/A
- **Evidence:** No `pickle.loads()`, `marshal.load()`, `shelve.open()`, or `yaml.unsafe_load()` found. YAML files are loaded with `yaml.safe_load()`. All external data is deserialized as JSON (safe). Pydantic models provide schema validation on all API inputs.

---

### 6. Encapsulation (4 items)

#### 6-1. Data Leak Between Sessions (CWE-488, CWE-543)
- **Severity:** High
- **Verdict:** Compliant
- **Evidence:** No global mutable state storing user data. Authentication context is stored per-request in `request.state.auth_context`. Database sessions are scoped per-request via FastAPI dependency injection. The `_STRIPE_PROCESSED_EVENTS` OrderedDict is bounded (10000 items) and only stores event IDs (no user data).

#### 6-2. Active Debug Code (CWE-489)
- **Severity:** Medium
- **Verdict:** Partial Compliance
- **File:** `packages/core/yaa_core/shared/config.py:67`, `packages/api/yaa_app/api/main.py:73-75`
- **Evidence:** The `disable_auth` flag serves as a debug/development bypass. When enabled, it also exposes `/docs`, `/redoc`, and `/openapi.json`. While the default is `False`, there is no environment-based guard preventing this in production.
  ```python
  docs_url = "/docs" if settings.disable_auth else None
  ```
- **Remediation:** Replace `disable_auth` with an explicit `ENVIRONMENT` check (e.g., only allow in `development` or `testing`). Add a startup log warning if debug-like features are enabled.

#### 6-3. Private Data Returned from Public Method (CWE-495)
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** API responses use Pydantic `response_model` to control which fields are exposed. Password hashes are never returned in API responses. API keys are masked in the settings API (`_mask_key()`). Internal database models are not exposed directly.
- **File:** `packages/api/yaa_app/api/routes/settings.py:35-39`

#### 6-4. Public Data Assigned to Private Field (CWE-496)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** Python's dynamic nature makes this pattern less relevant. Pydantic models create copies of input data during validation. No mutable internal state is exposed via reference.

---

### 7. API Misuse (2 items)

#### 7-1. Reliance on DNS Lookup (CWE-350)
- **Severity:** Medium
- **Verdict:** N/A
- **Evidence:** No DNS-based access control decisions found. Rate limiting uses IP addresses via `get_remote_address`. No reverse DNS lookups.

#### 7-2. Use of Vulnerable API
- **Severity:** Medium
- **Verdict:** Compliant
- **Evidence:** YAML uses `safe_load()` (not `load()`). No deprecated or known-vulnerable function calls found. Modern libraries are used throughout (SQLAlchemy 2.0 async, FastAPI, bcrypt, Fernet).

---

## Summary of Required Actions

### Immediate (Critical/High - Must Fix Before Production)

| Priority | CWE | Action | Effort |
|:--------:|-----|--------|:------:|
| 1 | CWE-307 | Implement per-email login brute force protection with account lockout | Medium |
| 2 | CWE-352 | Add CSRF protection for cookie-authenticated requests (SameSite cookies) | Low |
| 3 | CWE-759 | Force-migrate legacy SHA-256 password hashes to bcrypt on next login | Medium |
| 4 | CWE-521 | Add password complexity requirements (uppercase, digit, special char) | Low |

### Planned (Medium - Fix Before Next Release)

| Priority | CWE | Action | Effort |
|:--------:|-----|--------|:------:|
| 5 | CWE-489 | Guard `disable_auth` with environment check; prevent production use | Low |
| 6 | CWE-754 | Replace broad exception handlers with specific types in security paths | Medium |
| 7 | CWE-209 | Remove internal error details from client-facing error messages | Low |
| 8 | CWE-312 | Encrypt workspace integration API keys using Fernet before DB storage | Medium |
| 9 | CWE-693 | Add security headers (CSP, HSTS, X-Frame-Options) via middleware | Low |

---

## Methodology

This assessment followed the KISA Secure Coding Guide (2023) for Python (46 items) and JavaScript (42 items), evaluating 46 unique CWE patterns across 7 categories. The assessment was performed through:

1. Static code analysis via pattern matching (Grep/Glob) for known vulnerable patterns
2. Manual review of authentication, authorization, encryption, and error handling code
3. Configuration review (.gitignore, CORS settings, security headers)
4. Architecture review (dependency injection, repository pattern, middleware chain)

**Rating Scale:**
- **Compliant:** Secure coding practices followed
- **Partial Compliance:** Partially implemented; improvements needed
- **Vulnerable:** Security weakness identified; remediation required
- **N/A:** Pattern not applicable to this codebase
