# OptiLearn QA, Security, and Performance Audit

**Audit date:** 2026-11-19  
**Workspace:** `C:\Users\Lenovo\Desktop\OptiLearn`  
**Branch:** `audit-fixes`  
**Scope:** Local source and local checks only. No remote repository, deployment, database, or third-party AI/OAuth service was accessed.

## 1. Executive summary

OptiLearn is a single local Git repository containing a FastAPI backend and a Next.js frontend. The audit found and fixed authorization weaknesses in chat session access, unsafe upload naming and ownership checks, oversized upload handling at the route layer, several client-facing raw exception messages, and missing untrusted-content guidance in AI prompts.

**Overall risk: Moderate.** The code-level fixes reduce meaningful exposure, but production database TLS verification is disabled, auth refresh tokens are not server-revocable, there is no shared application-wide rate limiter, and background work runs in-process. Live deployment and production database behavior were not validated.

**Code quality: Moderate.** The frontend passes lint, TypeScript, and production build checks. The prior audit run passed 13 backend tests; the final environment did not have pytest or Ruff installed, so those could not be rerun after the last backend edits. No coverage report was available.

**Reliability: Moderate.** User-facing chat and upload paths received safer validation and error handling. Startup against a real database, external integrations, full indexing, and app-level HTTP flows could not be exercised in this environment.

**Performance: Not measured.** No Lighthouse, browser automation, local load test, or production latency measurement was available. Static inspection found potentially expensive upload parsing and in-process background processing; no throughput or latency numbers are claimed.

## 2. Project architecture

- **Frontend:** Next.js 16.4.6, React 19, TypeScript, under `frontend/`; the production build reports 12 generated routes, including dashboard, classrooms, chat, login, and registration.
- **Backend:** FastAPI application at repository root under `app/`, with route modules for authentication, chat, classroom, files, and indexing.
- **Database:** SQLAlchemy async/sync PostgreSQL access, asyncpg and psycopg pooling, pgvector and PostgreSQL full-text retrieval. Startup initializes database metadata; no migration workflow was verified in this audit.
- **Authentication:** Google OAuth integration, application JWT access/refresh tokens in HttpOnly cookies, and encrypted Google refresh-token storage.
- **AI:** LangGraph tutor with Postgres checkpointing for tutoring and an in-memory checkpoint for indexing; Groq model integrations; hybrid vector and full-text search with reciprocal-rank fusion and reranking; model call limiting exists per process/run, not as a shared distributed quota.
- **Ingestion:** PDF, office document, text, and image processing paths are present. No working audio/video transcription pipeline or FFmpeg ingestion was found in the inspected implementation, despite the project description.
- **Deployment configuration:** `render.yaml`, frontend configuration, and README indicate intended Render backend/Vercel frontend setup. No concrete authorized live URLs or credentials were present in the workspace, and no hosting dashboard was accessed.

## 3. Findings

| Severity | Category | Location | Description | Status | Recommendation |
|---|---|---|---|---|---|
| Medium | Authorization | `app/api/routes/chat.py`; tests in `tests/test_chat_session_scope.py` | Chat history, deletion, and query paths previously accepted a caller-supplied session namespace without verifying its user ownership. | Fixed | Keep owner-scoped session IDs and add API-level regression tests when an isolated DB test fixture is available. |
| Medium | File upload | `app/api/routes/files.py`; `app/services/file_service.py` | Upload names could influence paths; user/course ownership and size/type boundaries needed stronger enforcement. | Fixed | Keep proxy/hosting request-body limits aligned with the 100 MiB application cap; test multipart edge cases against an isolated service. |
| Medium | Data exposure | `app/workflows/indexing_workflow.py`; `app/api/routes/classroom.py`; related service/API paths | Provider and internal exception text could be persisted or returned to the user. | Fixed in reviewed paths | Review any newly added error surfaces and retain server-side diagnostic logs only. |
| Medium | Transport security | `app/core/database.py:24-25` | PostgreSQL SSL context disables hostname and certificate verification (`CERT_NONE`), allowing interception if the connection traverses an untrusted network. | Not fixed; needs environment/provider validation | Use CA/hostname verification appropriate to the configured database provider; test before rollout because provider settings are unknown here. |
| Medium | Authentication | `app/api/routes/auth.py`; `app/core/security.py` | Refresh JWTs are stateless and logout clears browser cookies but cannot revoke a copied refresh token before its expiry. | Not fixed | Consider refresh-token rotation with server-side revocation/session records and expiry enforcement. |
| Medium | Rate limiting | `app/rag/agent.py:25-37` and API routes | Model limiter is in-memory/per process; general API/auth/upload rate limiting is not shared across workers. | Not fixed | Add a shared store or edge-level limits for authentication, upload, and inference endpoints. |
| Medium | Upload resource limits | `app/api/routes/files.py:18` | Handler enforces a 100 MiB streamed limit, but multipart parsing can spool request bytes before route code applies that limit. Archive/decompression-bomb limits were not verified. | Partially addressed | Set a request-body limit at the proxy/server boundary and add content/decompression quotas. |
| Medium | Secret storage | `frontend/lib/api.ts:311-318` | User-provided Groq key is stored in browser `localStorage`, where same-origin script execution could read it. | Not fixed; design decision | Prefer short-lived/session storage or a backend-mediated secret flow with explicit user consent and secure storage. |
| Medium | Reliability | `app/api/routes/classroom.py`; `app/api/routes/indexing.py` | Classroom sync/indexing use FastAPI in-process background tasks, which may be lost on restart and do not provide durable retries. | Not fixed | Move durable jobs to a queue/worker and add recovery for stale processing states. |
| Low | AI security | `app/rag/prompts.py`; `app/rag/tools.py`; `app/processing/image_processor.py` | Retrieved and uploaded content is untrusted and can contain prompt injection. Prompt guidance was added, but model behavior is not guaranteed and adversarial cases were not tested. | Mitigated, not verified | Keep retrieved content separated/quoted and add mocked prompt-injection tests plus output validation. |
| Low | Functional scope | `app/processing/` and project description | The inspected pipeline supports document/image processing; audio/video transcription/FFmpeg path was not found. | Needs product clarification | Implement and test audio/video support if it remains a product requirement; otherwise revise claims/docs. |
| Low | Dependency audit | `requirements.txt` | Python package advisory scan could not reach PyPI; global `pip check` also reported an unrelated installed `langchain-nomic`/Pillow conflict not declared in repository requirements. | Needs environment with package index | Run `pip-audit -r requirements.txt` in CI with package-index access and resolve only repository dependency findings. |

## 4. Testing summary

### Checks that passed

- Prior audit run: `python -m pytest -q` — **13 passed** (chat session ownership/length validation, upload filename/type helpers, and existing health/security tests). These results predate the last small error-surface and prompt-text changes.
- Final audit run: Python AST syntax parse — **42 Python files parsed successfully**.
- Final frontend lint: `npm.cmd run lint` — passed.
- Final frontend type check: `npx.cmd tsc --noEmit` — passed.
- Final frontend production build: `npm.cmd run build` — passed; Next.js compiled, type-checked, and generated 12 routes.
- Prior frontend dependency audit: `npm.cmd audit` — 0 vulnerabilities reported.
- Final `git diff --check` — passed.
- Secret-pattern scan of tracked source and local history — no key-like credential patterns found. This is a pattern scan, not a guarantee that all secret forms are absent.

### Checks that could not be completed

- Final backend test rerun and Ruff: `pytest` and `ruff` are not installed in the active project/global Python environments (`No module named pytest` / `No module named ruff`). The earlier 13-pass result is reported separately rather than presented as a post-fix verification.
- `pip-audit -r requirements.txt`: package index connectivity failed; no current Python CVE result is available.
- Dynamic local API, database-backed indexing, auth, and ingestion flows: local server/API attempts did not return reliably; no isolated database configuration was available.
- Frontend test suite: no test script/framework was configured in the frontend package.
- Gitleaks, ZAP, browser E2E, Lighthouse, load test, and coverage: tools were unavailable or no safe live target was supplied. No scores or latency values are fabricated.

## 5. Security assessment

- **Authorization:** Chat session namespace ownership is now enforced in user-facing chat routes, including history/deletion access. Upload and classroom file retrieval now apply user/course ownership checks.
- **Input handling:** Chat question/session/course lengths are capped. Upload names are sanitized and generated server-side, allowed extensions are constrained, uploads are streamed in chunks with a 100 MiB cap, and failed files are cleaned up where possible. Drive-download names receive safe generated local filenames and size checks.
- **Error disclosure:** Reviewed auth, chat, classroom, file, workflow, and AI paths return generic client-facing failures; indexing and classroom sync no longer persist raw exception strings. Diagnostics remain in logs; broad logging review is still needed.
- **Secrets:** `.env.example` files are tracked, not real `.env` files. No secrets were detected by the performed pattern scan. No secret rotation was indicated by that scan.
- **Cookies/CORS/deployment headers:** Code configuration was reviewed, but production headers, TLS, cookies behind the host proxy, and actual CORS behavior were not validated against a live deployment.
- **OWASP-oriented risks remaining:** transport certificate verification, refresh-token revocation, distributed rate limiting, upload boundary limits, localStorage key exposure, and durable background job handling remain outstanding.
- **AI-specific:** Main tutor, image interpretation, flashcard, and summary prompts now instruct the model to treat supplied material as untrusted. This reduces risk but does not prove resistance to prompt injection.

## 6. Performance assessment

No performance measurements were obtained. Lighthouse scores, API latency, P95, throughput, and error rate are **not available**.

Static observations:

- Uploads may consume temporary disk before route-level streaming checks because multipart parsing precedes endpoint execution.
- Document/image processing, embedding, and retrieval depend on database and external inference latency; these were not measured.
- In-process background jobs avoid an extra queue dependency but do not survive process termination reliably.
- A per-process model rate limiter and a per-run model-call cap exist; neither gives a global quota across deployed workers.
- The build output shows Next.js static prerendering for most pages; no bundle-size or browser-runtime profiling was performed.

## 7. Changes applied

Code changes on `audit-fixes`:

- Added owner-scoped chat session validation and bounded chat input lengths.
- Hardened upload type/name/size handling, course ownership validation, cleanup on failure, and file listing scoping.
- Made Google Drive local file naming and download size handling safer.
- Replaced raw client-visible provider/internal errors with generic responses in reviewed paths.
- Added untrusted-source instructions to tutor, image, flashcard, and summary prompts.
- Updated the classroom upload picker to match supported backend formats.
- Added tests for chat session scoping and file upload security helpers.
- Added this audit report.

No dependencies, production settings, database resources, cloud resources, or deployment settings were changed. No push, merge, or deploy was performed.

## 8. Remaining issues by priority

### Critical

None confirmed in the reviewed local source. Dynamic production checks were not performed.

### High

None confirmed. Production runtime and external integration behavior remain unverified, so this is not a production assurance statement.

### Medium

- Enable database certificate and hostname verification after confirming the provider CA requirements.
- Add server-side refresh-token revocation/rotation.
- Add shared request and inference rate limits.
- Enforce upload request-body and decompression limits at the edge/application boundary.
- Decide how user-supplied Groq keys should be stored and sent.
- Replace in-process long-running/background work with durable jobs and recovery.
- Run dependency audit with package-index access and investigate the global environment conflict separately.

### Low

- Add adversarial prompt-injection tests and output validation.
- Verify image/document ingestion with controlled fixtures and an isolated database.
- Confirm whether audio/video transcription is an intended supported feature.
- Establish frontend E2E/accessibility/performance coverage.

### Requires owner/environment input

- Database provider/CA configuration is required before changing TLS verification safely.
- No live OptiLearn frontend/backend URLs were supplied; live checks were therefore skipped.
- Production auth/session and Groq key handling decisions affect UX and deployment and need product/security choices.

## 9. Manual action checklist

- [ ] Supply authorized live frontend/API URLs before performing light production checks.
- [ ] Confirm PostgreSQL provider CA settings and enable certificate/hostname validation.
- [ ] Add a shared rate-limit store or hosting-edge policies for auth, upload, and inference.
- [ ] Decide on Groq key storage and refresh-token revocation/rotation.
- [ ] Configure request-body and archive/decompression limits in hosting infrastructure.
- [ ] Move critical indexing/sync work to a durable worker and monitor stale jobs.
- [ ] Run Python dependency auditing in CI with package index access.
- [ ] Enable GitHub Dependabot and secret scanning; configure branch protection.
- [ ] Review production CORS, security headers, cookie attributes, uptime monitoring, database backups, and connection/resource alerts.
- [ ] Add isolated database integration tests and browser E2E/accessibility checks.

## 10. Git change summary

- **Current branch:** `audit-fixes`
- **Base local history before audit commits:** `1d9536b Build OptiLearn AI learning platform`, `cc5abed Include frontend lib files for Vercel build`
- **Audit commits:** `51a0c08 Harden chat ownership and file uploads`; `b32242a Redact service errors and harden AI prompts`; this report is committed separately.
- **Code diff against pre-audit `cc5abed`:** 15 files changed, 215 insertions, 88 deletions (before counting this report).
- **Remote operations:** none; the configured `origin` was inspected locally only.
- **Final verification:** frontend lint, TypeScript check, and production build passed; 42 Python files parsed; prior backend suite passed 13 tests but could not be rerun after the last backend edits due missing pytest; Python dependency scan incomplete due unavailable package index.
