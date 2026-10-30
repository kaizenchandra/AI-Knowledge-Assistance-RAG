# Production readiness: NO-GO

The local end-to-end workflow is runnable and verified with offline retrieval/generation adapters. This does **not** satisfy the entire enterprise brief. No functional area with outstanding acceptance conditions is marked fully complete, and no production NFR is certified.

Continuation update: request-body limits, resource-limited parser subprocesses, ClamAV scanning/quarantine, provider preflight, embedding-version filters, generation-specific purge jobs, regenerate UI and stale-history filtering are now implemented. Real local ClamAV has passed clean/EICAR and uploaded-document quarantine checks. The scanner-enabled browser/API workflow passes separately from credential-dependent cloud tests. See [live integration instructions](live-integrations.md) and the latest section of [verification report](verification-report.md). Remaining cells below retain broader release gates; scanner integration no longer means a missing adapter, but still needs production deployment and operating validation.

| Area | Current evidence | Remaining release gate |
|---|---|---|
| FR-01 identity | local login, RS256 claims tests, server membership revocation | browser OIDC redirect/PKCE, refresh, session/token revocation lifecycle, real IdP test |
| FR-02 tenancy | tenant/workspace/role checks and membership administration | organization administration/offboarding, independent DB isolation defense, quotas, per-document ACL |
| FR-03/04 documents | upload/parse/jobs/reprocess/delete; parser fixtures for all five formats; resource-limited subprocess; real ClamAV/quarantine | immutable source version history, tags/bulk operations, production scanner lifecycle, OS sandbox, orphan reconciliation |
| FR-05 Pinecone | SDK adapter, preflight dimension/metric/host checks, version fingerprint and targeted purge; opt-in live test | credential-backed round trip, throttling, crash/reconciliation stress, full model migration |
| FR-06/07 retrieval/graph | bounded graph and lexical baseline, durable checkpoints | calibrated semantic thresholds, planning/rewrite/rerank measurement, claim support validation, public chat resume API |
| FR-08 specialist agents | intentionally deferred P2 design | demonstrated benchmark benefit |
| FR-09/10/13 chat/citations/memory | browser stream/source/history, deletion/abstention, checkpoint erasure, regenerate, stale-history evidence exclusion | transport reconnection policy, full retention sweeper, semantic citation entailment |
| FR-11/12 approval/tools | durable reprocess interrupt, decision/replay/expiry checks | crash-before-interrupt reconciler, generic typed tool registry and timeout/rate policies, concurrency stress |
| FR-14 quality | feedback and seven-case/three-source lexical baseline | representative human-reviewed live quality data, calibrated groundedness/citation coverage, regression comparisons |
| FR-15/16 operations | basic counts/activity, indexing/approval states and toast notifications | cost/token ledger, date filters, quality/latency dashboards, durable user notification inbox |
| NFR-01/02/03 | functional local tests only | 50-stream load run, scaling/backpressure, availability measurements, provider fault injection, backup/restore drill |
| NFR-04/05 | negative authorization and token tests | security review, scanner, resource quotas, retention/data residency, penetration/dependency/image scanning |
| NFR-06/07/08/09 | structured logs, pinned resolution, formatting/tests/builds, Compose | full distributed tracing/alerts, backend static typing, provider portability tests, clean-machine replication |
| NFR-10/11/12 | finite execution limits, job generation fencing, labeled responsive UI | measured costs, reconciliation/consistency stress tests, WCAG audit, keyboard/screen-reader checks, theme support |

Cloud status: Terraform format and validate pass; no plan against a real account, apply, staging rollout or production deployment. Existing VPC/private subnet egress, TLS load balancer routing, ECR images, runtime secret contents, application-specific DB credentials and organization identity must be configured. Terraform creates resource definitions; it does not constitute operational readiness.

Cost assumptions: local offline mode incurs no model/vector API usage. Live mode incurs embedding/model/Pinecone/storage costs. Prepared cloud configuration includes multi-AZ RDS, two Redis nodes, private networking prerequisites and ECS resources; obtain a region-specific estimate and budget before apply. The UI shows unknown estimated cost, not fabricated zero.

Next priorities: full OIDC lifecycle; credential-backed live provider validation and source freshness; representative quality/abstention evaluation; quotas/usage accounting; reconciliation/retention; OS sandbox and production scanner operations; staging load and restore/rollback drills. Do not expose the development token mode publicly.
