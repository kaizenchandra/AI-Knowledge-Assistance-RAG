# Non-functional requirements

These are release targets, not observed results. Initial load: 50 active streams, 10 tenants, 10,000 documents, 20 MB per upload, 5 simultaneous ingestion jobs; region and provider model must be recorded with every benchmark.

| ID | Acceptance and assumptions | Owner/component | Validation and release gate |
|---|---|---|---|
| NFR-01 Performance | p95 first token ≤3 s, answer ≤12 s, non-AI API ≤300 ms at stated load; ingestion does not starve chat | API/worker/provider | 30-minute load run with percentile distributions; staging gate |
| NFR-02 Scale | API and worker scale independently; bounded concurrent requests/jobs; tenant overload returns 429/503; queue backlog drains after burst | Redis, queue, ECS | burst and saturation tests; production gate |
| NFR-03 Reliability | 99.9% monthly target; bounded retries/timeouts; readiness detects essential failures; restore RPO ≤24 h and RTO ≤4 h | SRE/storage/API | fault injection, backup restore and monthly SLI; production gate |
| NFR-04 Security | zero critical/high unresolved security findings; every resource route passes cross-tenant and role tests; TLS, encryption and least privilege; no LLM authority escalation | all components | ASVS/API/LLM threat review, dependency scans, adversarial tests; production gate |
| NFR-05 Privacy | no document/prompt/secrets in default logs; explicit retention and region; tombstone immediate, purge ≤24 h subject to documented backup expiry | data/privacy | log inspection, deletion drills, provider terms review; production gate; no certification implied |
| NFR-06 Observability | request/run/job IDs on all events; latency/errors/tokens and missing-cost indicators; alerts within 5 min of sustained failure | telemetry | trace correlation and alert drill; staging gate |
| NFR-07 Maintainability | dependency direction enforced; pinned compatible dependencies; migrations tested forward; typed API and lint/type/build checks pass | engineering | CI and architecture review; every release |
| NFR-08 Testability | offline adapters deterministic; security/ingestion/graph branches testable; live paid tests separately enabled | QA/adapters | unit/integration/browser suites; every release |
| NFR-09 Portability | documented local containers; no Kubernetes prerequisite; provider calls isolated behind ports | platform | clean-machine bootstrap; staging gate |
| NFR-10 Cost | bounded input/output/steps; tenant usage ledger; estimate identified by pricing version; no claim of exact cost without provider usage | agent/analytics | budget tests and reconciled invoice sample; production gate |
| NFR-11 Integrity | SQL authoritative; outbox/lease replay safe; tombstones block stale vectors immediately; current-version checks on every citation/search result | data/worker | crash/replay/concurrent-delete tests and reconciliation drill; every release |
| NFR-12 Accessibility | WCAG 2.2 AA target; keyboard operations, labels, focus, contrast, responsive 360px layout; dark/light preferences | frontend | automated axe plus manual keyboard/screen-reader review; production gate |

Release policy: unexecuted gates remain open. Local offline success cannot certify model quality, Pinecone freshness, cloud availability, performance or regulatory compliance. External endpoints, deployment account, region, identity provider, model, retention requirements and spend limits require environment-specific configuration.
