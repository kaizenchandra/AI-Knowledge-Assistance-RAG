# Functional requirements specification

Status: approved task scope, implementation not yet verified. Source: ../prompt.md. P0 is the usable end-to-end release; P1 is required before production; P2 is an opt-in extension. All API paths are under `/api/v1`. All resource lookups must revalidate the authenticated tenant, workspace membership, and resource lifecycle in the database. A UI control is complete only when its backend behavior and failure case are tested.

## FR-01 — Identity (P0), session administration (P1)
Role: member, administrator. Story/value: as a member I sign in to access only my organization's information.
Description: OIDC authorization code with PKCE, issuer/audience/signature/expiry verification, logout, refresh and revocation; explicit local development identity.
Acceptance: missing, expired, wrong-audience or forged tokens return 401; valid nonmembers cannot access workspace resources; development identity is disabled outside development. Revoked sessions fail on next request.
API/backend: `/session`, JWT validation, membership lookup, audited role changes. UI: sign-in/out, protected shell, expired-session recovery. Dependencies: identity provider, memberships, audit store.
Tests: AUTH-01 valid login; AUTH-02 invalid token matrix; AUTH-03 revoked session; AUTH-04 development-mode production rejection.

## FR-02 — Tenancy and workspaces (P0), quotas/offboarding (P1)
Role: administrator/member. Story/value: administer independent organizations without leaking information.
Description: tenant, workspace and knowledge-base CRUD, membership roles, document policies, quotas, configuration and offboarding.
Acceptance: tenant B never reads, modifies, searches or cites tenant A resources; roles are derived server-side; offboarding tombstones access immediately and removes derived records asynchronously.
API/backend: `/workspaces`, `/knowledge-bases`, `/memberships`; scope SQL, storage keys, cache keys, vectors and tools. UI: workspace/KB selectors and member administration. Dependencies: FR-01.
Tests: TEN-01 cross-tenant ID substitution on every route; TEN-02 viewer mutation denied; TEN-03 offboarding purge/retry.

## FR-03 — Document management (P0), versions/bulk operations (P1)
Role: editor/member. Story/value: upload and inspect trustworthy, current knowledge.
Description: multi-file drag/drop, PDF/DOCX/TXT/Markdown/HTML validation, metadata, preview, tags, status, delete/replace/reprocess, version history and permissions. URL import/OCR are P2, disabled by default.
Acceptance: bounded uploads reject unknown formats and oversized files before parsing; status reflects persisted jobs; deleted documents become inaccessible immediately; replacement does not expose incomplete versions.
API/backend: `/documents`, `/documents/{id}`, `/documents/{id}/reprocess`; immutable source versions and authorized preview. UI: progress, errors, retry and filters. Dependencies: FR-02/04.
Tests: DOC-01 all formats; DOC-02 oversized/malformed input; DOC-03 deletion during retrieval; DOC-04 version replacement.

## FR-04 — Durable ingestion (P0), quarantine/reconciliation (P1)
Role: editor/operator. Story/value: uploaded knowledge survives worker crashes and becomes searchable.
Description: authorize → validate → quarantine/scan → protected storage → transactional job → dispatch → parse → normalize → deduplicate → chunk → embed → upsert → verify visibility → publish.
Acceptance: persisted jobs survive restarts; repeated delivery produces deterministic chunk IDs; bounded retries end in observable failure; stale workers cannot publish deleted/replaced documents; no searchable status on mere upsert acknowledgement.
API/backend: job/status/retry endpoints, queue/outbox, leases and generation checks. UI: progress/error notifications. Dependencies: FR-03/05, storage, queue, parsers.
Tests: ING-01 crash/replay; ING-02 partial vector failure; ING-03 delayed visibility; ING-04 delete/reprocess races; ING-05 malicious/archive-bomb documents.

## FR-05 — Pinecone (P0), model migration (P1)
Role: operator. Story/value: isolate and retrieve durable semantic knowledge.
Description: serverless provisioning, dimension/metric validation, tenant namespaces, metadata filters, batch upsert/delete, version-aware retrieval and reindexing.
Acceptance: query namespace comes only from verified identity; filters include authorized workspace/KB; every match is reauthorized in SQL; incompatible embeddings fail readiness; writes are verified before publication.
Metadata: tenant/workspace/KB/document/version/chunk IDs, source filename/content type, access scope, creation timestamp, embedding and ingestion versions (scalar values).
API/backend: adapter and provisioning command. UI: indexing health. Dependencies: FR-02/04, embedding provider.
Tests: VEC-01 namespace/filter contract; VEC-02 live round trip; VEC-03 eventual consistency; VEC-04 model dimension mismatch.

## FR-06 — Retrieval (P0 baseline; P1 enhancements; P2 hybrid)
Role: member. Story/value: receive relevant authorized evidence within a bounded context.
Acceptance: top-k is bounded; SQL removes stale/deleted/unauthorized matches; sources retain provenance; missing evidence abstains. Query rewrite/reranking only ship after measured recall/latency/cost comparison against dense baseline.
API/backend: retrieval service, embedding/vector/rerank ports, context limits. UI: evidence and limitations. Dependencies: FR-05/10/14.
Tests: RET-01 golden relevance; RET-02 empty evidence; RET-03 duplicate chunks; RET-04 stale versions; RET-05 ACL filter.

## FR-07 — Stateful agent workflow (P0)
Role: member. Story/value: run bounded, recoverable question answering.
Description: validate, classify, plan/route, retrieve, assess, bounded rewrite, optional authorized tool, consolidate, synthesize, validate citations, finish/escalate.
Acceptance: typed graph state; explicit edges; maximum steps, wall time, context/output tokens; safe error terminal state; durable checkpoints survive process restart; deterministic access checks cannot be overridden by retrieved instructions.
API/backend: `/runs`, state graph and checkpoint store. UI: public stage events, no private reasoning. Dependencies: FR-06/11/12.
Tests: AGT-01 answer/abstain routing; AGT-02 loop/time budget; AGT-03 checkpoint recovery; AGT-04 malicious retrieved instructions.

## FR-08 — Optional specialist agents (P2)
Role: architect/operator. Story/value: adopt specialization only where measured quality warrants cost.
Acceptance: coordinator/retriever/research/synthesis/verifier/tool specialists remain disabled until benchmark demonstrates improvement with no isolation regression; same budget and permissions apply.
API/backend: optional graph composition. UI: stage summaries. Dependencies: FR-07/14. Tests: MULTI-01 paired benchmark and failure isolation.

## FR-09 — Chat and streaming (P0), advanced management (P1)
Role: member. Story/value: ask questions, follow up and restore conversations.
Description: create/history/rename/delete conversations, authenticated SSE, stage/token/final/error events, stop, retry/regenerate, copy, feedback and citations.
Acceptance: history persists; bounded event buffers; disconnect cancels generation; only one active run per conversation; cancellation is distinct from durable approval pause; reconnect never silently repeats side effects.
API/backend: `/conversations`, `/conversations/{id}/messages`, `/runs/{id}/cancel`. UI: responsive composer, history, completion/error states and AbortController cleanup. Dependencies: FR-01/07/10/13.
Tests: CHAT-01 full SSE transcript; CHAT-02 split UTF-8/event frames; CHAT-03 disconnect/cancel; CHAT-04 concurrent submissions/history restore.

## FR-10 — Citations (P0)
Role: member. Story/value: independently verify answer evidence.
Acceptance: every returned citation resolves to an authorized current chunk with document/version/title and page/section when known; fabricated IDs are rejected; deleted source returns 404; insufficient or conflicting evidence is disclosed.
API/backend: `/citations/{chunk_id}`, provenance validation. UI: source panel and preview. Dependencies: FR-03/06. Tests: CIT-01 valid source; CIT-02 forged/stale/cross-tenant reference; CIT-03 unsupported claims.

## FR-11 — Human approval (P0)
Role: approver/requester. Story/value: control privileged operations before execution.
Acceptance: LangGraph interrupt persists; only authorized approver can decide; expiry, rejection, cancellation and replay are handled; approved payload is immutable; resumed tool rechecks permissions; side effect occurs at most once.
API/backend: `/approvals`, `/approvals/{id}/decision`, durable checkpoint and idempotency receipt. UI: proposed action, scope, expiry, approve/reject and audit status. Dependencies: FR-07/12. Tests: HITL-01 restart/resume; HITL-02 forged/replayed/expired approval; HITL-03 concurrent decisions.

## FR-12 — Secure tools (P0 internal, P2 external)
Role: member/approver. Story/value: use knowledge and approved business operations safely.
Acceptance: registry entries specify typed input/output, role/scope, timeout, retry/rate limits, audit and mutation idempotency; no shell, arbitrary SQL or unrestricted URL tool; model text cannot create privileges.
API/backend: authorized search/metadata/KB lookup and controlled mutation. UI: tool progress and approval context. Dependencies: FR-02/11. Tests: TOOL-01 schema rejection; TOOL-02 permission failure; TOOL-03 timeout/replay.

## FR-13 — Memory (P0 history/checkpoints, P1 retention, P2 semantic memory)
Role: member/admin. Story/value: continue work while controlling data retention.
Acceptance: bounded recent history feeds follow-ups; checkpoint recovery does not imply SSE replay; deleting conversation removes history/checkpoints by retention contract; semantic memory requires consent and separate scope.
API/backend: conversation history/deletion and scheduled retention. UI: restore/delete/preferences. Dependencies: FR-09. Tests: MEM-01 follow-up; MEM-02 context truncation; MEM-03 deletion/isolation.

## FR-14 — Quality and feedback (P0 feedback/baseline, P1 comparisons)
Role: member/evaluator. Story/value: detect regressions using evidence.
Acceptance: one editable feedback per user/answer; versioned golden dataset covers answerable, unanswerable, ambiguous, conflicting, stale, adversarial and cross-tenant cases; report recall/precision/MRR, citations, abstention, latency/tokens/cost with evaluator limitations.
API/backend: `/feedback`, evaluation command/results. UI: vote/comment and quality dashboard. Dependencies: FR-06/09. Tests: EVAL-01 deterministic baseline; EVAL-02 ownership; EVAL-03 prompt/model comparison.

## FR-15 — Administration and analytics (P1)
Role: tenant admin/operator. Story/value: diagnose quality, capacity and spend.
Acceptance: live tenant/workspace/date/status filters; document/jobs/query/error/latency/token/cost/feedback/quota metrics derive from recorded events; unknown cost is unknown, never zero; unauthorized aggregation denied.
API/backend: `/analytics`, `/admin/jobs`, membership/quota administration. UI: dashboards/settings/admin console. Dependencies: FR-02/04/14. Tests: ADM-01 aggregate fixtures and scope; ADM-02 failed job retry; ADM-03 restricted administration.

## FR-16 — Notifications (P1; email/webhook P2)
Role: member/operator. Story/value: act on indexing, approvals, errors and quota warnings.
Acceptance: durable in-app events are scoped, deduplicated and markable as read; retries do not duplicate events; no secrets or full documents in notification payload.
API/backend: `/notifications`. UI: inbox/status badges. Dependencies: FR-04/11/15. Tests: EVT-01 event delivery/replay; EVT-02 cross-tenant denial.
