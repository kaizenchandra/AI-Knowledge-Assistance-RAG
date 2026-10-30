# Engineering verification report — 2026-10-29

## Continuation: live-integration preparation and ingestion hardening

This section supersedes the baseline counts below; the original report is retained as prior evidence.

Implemented:

- Read-only Pinecone/S3/scanner preflight, configured-dependency readiness, bounded SDK I/O, and opt-in synthetic provider smoke tests. Pinecone validation checks host, dimension, cosine metric and ready state; queries include an embedding fingerprint. Existing vectors without this metadata require reprocessing.
- Exact-chunk query-visibility probes and durable generation-specific purge jobs. An obsolete or deleted generation schedules cleanup even if the finishing worker has lost its lease. Crash-before-cleanup reconciliation is still outstanding.
- Request-body size/time limits before multipart parsing, including chunked bodies; Next.js proxy limit adjusted to accommodate the documented 20 MB file limit plus framing.
- Resource-limited, credential-free parser subprocess with wall timeout and Linux memory/CPU/file-size/file-descriptor limits. Valid PDF, DOCX, TXT, Markdown and HTML fixtures exercised. This is not a full network/filesystem sandbox.
- Real local ClamAV service, fail-closed INSTREAM client, scanner readiness, non-development scanner requirement and a quarantined lifecycle state. The protected source is retained for operator handling and never parsed/indexed after detection.
- Answer regeneration with a preserved audit/history trail, and exclusion of prior assistant messages whose cited sources are deleted, revoked, unready or outdated.
- Scanner Compose overlay and VS Code startup task; optional configurable S3-compatible overlay; dispatch-only protected-environment workflow for explicitly selected paid smoke tests. Terraform runtime secret contract and S3 bucket-readiness IAM permission updated.

Observed verification:

| Check | Result |
|---|---|
| Full backend suite against isolated PostgreSQL, real scanner enabled | **28 passed, 2 skipped in 3.64 s** |
| Skipped tests | Pinecone/model and S3 live smoke tests; no credentials configured |
| Real scanner | Clean file accepted; EICAR rejected; uploaded EICAR document became quarantined and cleanup succeeded |
| Failure-path tests | Declared/chunked oversize requests rejected before app; scanner protocol failures fail closed; obsolete-generation and lost-lease/delete race queue cleanup; deleted evidence excluded from model memory |
| Browser workflow with scanner and regenerate | **2 passed in 10.7 s**, including mobile layout check |
| TypeScript | Passed |
| Backend static checks | Passed after formatting/import cleanup |
| Terraform format/validate | Passed after runtime secret/IAM changes |
| Containers | Built and started with scanner overlay; no cloud deployment |
| Final readiness | status=ok; scanner=ready; model/Pinecone/S3=not_enabled |

External integration blockers: `.env` has no OPENAI_API_KEY, CHAT_MODEL, PINECONE_API_KEY, PINECONE_HOST, S3_BUCKET or OIDC issuer/audience/JWKS values. Docker Hub denied the attempted MinIO pull and Quay returned 401; an approved accessible image is now an explicit MINIO_IMAGE input. S3 was not falsely substituted with an in-memory test. No paid model/vector/cloud resources were provisioned. The real local scanner image required x86 emulation on Apple Silicon and successfully loaded signatures.

Run instructions and precise evidence levels are in [live-integrations.md](live-integrations.md). Full browser OIDC/refresh, tenant offboarding/quotas, document version history/ACLs, usage accounting, notifications, reconciliation/retention, broader AI evaluation and cloud release gates remain open. Production verdict remains **NO-GO**.

---

## Outcome and scope

Implemented and launched a functioning local full-stack vertical slice at http://localhost:3100, with API at http://localhost:8100. PostgreSQL and Redis are healthy; API, separate worker and Next.js run as containers. This is **not completion of the full enterprise brief**, and production readiness is **NO-GO**. Live Pinecone/LLM/S3/OIDC and AWS deployment remain unverified; additional feature and hardening work is listed in production-readiness.md.

## Requirements and architecture delivered

Wrote FRS covering FR-01–16, NFRS covering NFR-01–12, architecture, domain/data/API/workflow designs, ADRs, dependency-ordered roadmap, testing strategy, security assessment, evaluation plan, deployment and operating documentation before/alongside implementation. No whole FR/NFR is marked complete merely because files exist.

Selected modular monolith plus independent worker; FastAPI/SQLAlchemy/PostgreSQL for authoritative state, Redis for request limits, LangGraph for checkpointed answer/approval state, LangChain/Pinecone/S3 adapters, Next.js/React/TanStack Query UI. Accepted deviation: SQL durable queue instead of SQS in the initial slice, avoiding transactional dual-write loss. Cloud target is ECS Fargate, with Terraform requiring existing private networking and HTTPS routing.

## Verified implementation

- Local identity, server-side role and tenant/workspace checks; JWT signature/issuer/audience/expiry tests; membership grant/revoke and scoped workspaces.
- Workspace/KB creation, real multipart upload and asynchronous worker processing; deterministic chunking, bounded parsing, retry/job persistence and source status.
- Local upload→query→grounded source excerpt→citation flow, saved conversations, feedback, rename and deletion including associated checkpoints.
- Authenticated SSE progress/token/final events, browser cancellation control, current-version source reauthorization and immediate deletion denial.
- LangGraph durable approval interrupt/resume for reprocessing; administrator enforcement, expired/rejected decisions and duplicate-decision prevention.
- Integrated library, chat/source panel, approvals, basic analytics and membership settings; responsive 390px layout.
- Containers, frozen migration, resolved dependency locks, CI checks and Terraform preparation.

## Checks actually executed

| Check | Observed result |
|---|---|
| Backend container build from pinned resolution | Passed on Python 3.12 |
| Next.js optimized container build | Passed, Next.js 16.4.3 with TypeScript checking |
| Fresh database creation + frozen Alembic upgrade + checkpoint bootstrap | Passed against disposable PostgreSQL database |
| `pytest -q -p no:cacheprovider tests`, integration enabled | **12 passed in 1.47 s** on fresh database |
| `ruff check --no-cache app tests` | All checks passed |
| `ruff format --check --no-cache app tests migrations` | 19 files already formatted |
| `npm run typecheck` | Passed |
| Playwright final suite | **2 passed in 9.8 s**: full workflow and mobile layout |
| Desktop chat/source preview | Screenshot visually inspected; real answer and authorized source rendered |
| `npm audit --audit-level=high` | 0 reported vulnerabilities |
| `pip-audit --disable-pip --no-deps -r requirements.lock` (2.9.0, disposable container) | No known vulnerabilities found; lock is pinned but not hash-verified |
| Terraform format/init/validate | Passed; AWS provider 6.71.0, Terraform 1.17.0 |
| Local Compose status | API/web/worker running, PostgreSQL/Redis healthy |
| Final `/health/ready` | `{"status":"ok","provider":"offline"}` |
| Synthetic retrieval evaluation | Seven queries over three documents; mean answerable recall 1.0, abstention classification 7/7 |

Backend tests include deterministic chunks/version identity, parser rejection and HTML script removal, production-mode rejection, OIDC token claims, upload/SSE/history/citations, deleted-source abstention, cross-tenant access denial, viewer mutation denial, approval checkpoint/replay/rejection/expiry, duplicate upload, conversation erasure and membership scope.

Initial failures found and fixed: generic frontend 204-response type, occupied host port 8000, task shell-command quoting, navigation-selector whitespace, Terraform block syntax, formatting/import issues and container cache permissions. Tests reported above were rerun after relevant fixes. CI workflow exists but was not executed on GitHub.

## Performance, quality, costs and security

Individual offline retrieval calls measured 0.755–5.558 ms in the tiny synthetic corpus; these are not p95 production or 50-user load results. Browser test duration is test execution time, not an answer latency SLO. No NFR performance/availability claim is made.

Offline answers are exact evidence excerpts and explicitly labeled. Live semantic search, generative answer correctness, faithfulness, calibrated abstention and citation entailment were not evaluated. Structural citation checks do not prove factual support. No model/vector calls were made for this baseline.

No paid cloud/model/vector resources were provisioned. Live costs are unknown and shown as unavailable. Terraform includes potentially billable multi-AZ database, two Redis nodes and ECS infrastructure; region/account-specific estimates and budgets are required before apply.

Negative authorization tests passed, but this is not a penetration test or security certification. Open gates include scanner/quarantine, parser isolation, ingress body limits, comprehensive quotas, full OIDC session lifecycle, independent SQL isolation defense, retention/reconciliation and deployed IAM/TLS verification.

## Phase assessment

| Phase | Delivered and tested | Outstanding / next gate |
|---|---|---|
| 0 requirements | FRS/NFRS/design/roadmap/test plan | refine detailed enterprise stories with deployment context |
| 1 foundation | builds, migrations, DB/Redis, Compose | clean-machine replication and full backend typing |
| 2 identity/tenancy | local auth, bearer verification, roles/workspaces/memberships | browser SSO/refresh, tenant administration/offboarding |
| 3 ingestion | local durable upload/index/delete/reprocess | live Pinecone/S3, malware and failure/reconciliation matrix |
| 4 RAG | local retrieval/excerpts/citations | live quality and semantic thresholds |
| 5 agents | persisted bounded graph and approval resume | broader tools, planning/budgets, crash reconciler |
| 6 chat | browser end-to-end stream/history/source/stop controls | robust public run resumption, regenerate, richer error testing |
| 7 quality | feedback and measured synthetic baseline | representative live dataset and calibrated evaluators |
| 8 hardening | authorization, limits, safe defaults, logs | quotas, telemetry/alerts, retention, load/failure/restore gates |
| 9 deployment | validated Terraform and CI configuration | authorized account plan/apply, staging E2E and rollback |
| 10 readiness | explicit NO-GO and documented residual risks | close production-readiness gates |

Full limitations and next dependency-ordered work are in production-readiness.md. The original prompt remains unchanged.
