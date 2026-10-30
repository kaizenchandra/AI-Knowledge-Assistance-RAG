# Roadmap and traceability

Repository discovery: only prompt.md existed; no existing app, tests, package versions or repository instructions discovered. Git/system Python launcher failed because macOS Command Line Tools are missing. Alternative runtimes will be checked. No cloud credentials or deployment authorization inferred.

All rows start **planned**; only verification report evidence can promote them. Complete phases in order; requirements/design precede significant implementation.

| Phase | Tasks/deliverables | Depends | Requirements | Tests / exit evidence | Main risk |
|---|---|---|---|---|---|
| 0 P0 | FRS, NFRS, assumptions, architecture, test plan | brief | all | requirements coverage reviewed | scope ambiguity |
| 1 P0 | backend/frontend, config, containers, migration, health | 0 | NFR-07/09 | clean boot, DB/Redis health, builds | runtime availability |
| 2 P0 | auth, memberships, workspace/KB CRUD | 1 | FR-01/02 | AUTH/TEN suites, browser selection | object authorization |
| 3 P0 | protected upload, worker, parsers, embeddings, Pinecone | 2 | FR-03/04/05 | DOC/ING/VEC suites and live index visibility | distributed races |
| 4 P0 | bounded authorized retrieval, generation, citations | 3 | FR-06/10 | RET/CIT suites and uploaded-source answer | hallucination |
| 5 P0 | durable graph, budgets, approval/tools | 4 | FR-07/11/12 | AGT/HITL/TOOL restart/replay tests | side-effect replay |
| 6 P0 | chat UI, SSE, history, stop/retry | 5 | FR-09/13 | CHAT/MEM and browser full workflow | transport cleanup |
| 7 P1 | feedback, evaluation, measured retrieval improvements | 6 | FR-06/14 | EVAL baseline and comparisons | evaluator validity |
| 8 P1 | quotas, audit, metrics, notifications, security/recovery | 7 | FR-15/16, NFR-02–06/10–12 | security/load/restore suites | untested operational assumptions |
| 9 P1 | Terraform, CI/CD, staging smoke and rollback | 8 | NFR-03/09 | deployed staging E2E and rollback evidence | access/cost |
| 10 P1 | readiness verdict, limitations, capacity/cost report | 9 | all NFRs | explicit go/no-go with evidence | false readiness |
| optional P2 | specialist agents, hybrid, OCR, connectors | measured need | FR-08 and P2 extensions | paired benchmark and threat review | complexity |

Test IDs are specified in the FRS; automation names map to those IDs. A requirement with only part of its acceptance verified remains partial. Provider absence permits development alternatives but does not close live integration gates. Infrastructure absence permits executable deployment preparation but does not close staging gates.
