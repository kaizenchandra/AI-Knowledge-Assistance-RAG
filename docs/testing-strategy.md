# Test strategy

Before implementation: unit-test scoped ownership, chunk identity, bounded parsing, routing and budgets. Integration-test real database transaction boundaries, durable worker replay, history, authenticated SSE, citations and document deletion. Deterministic development adapters isolate provider behavior; separately enabled live tests exercise Pinecone, model, S3 and OIDC.

Critical browser scenario: authenticate → create workspace/KB → upload synthetic policy → wait for ready → ask policy question → observe stage/token/final → open source → follow up → request controlled action → approve/reject → delete source → confirm citation and retrieval deny it. Include second-tenant ID substitution, viewer writes, invalid tokens, wrong approver and replay.

Failure matrix: duplicate event, worker lease expiry, parser exception, model timeout/429, delayed vector visibility, partial upsert, cancellation, checkpoint restart, concurrent approval, deletion during retrieval and indexing. Never use real customer content in fixtures.

Quality: versioned golden questions with expected source IDs and abstention; compute retrieval precision/recall/MRR and citation validity deterministically. Human-calibrated groundedness and correctness assessments are separate from structural citation checks. Track model/prompt/dataset versions, input/output tokens, latency and estimated cost; unknown measurements stay null.

Release checks: backend lint/type/tests, frontend lint/type/unit/build, Playwright, dependency/security scans, Terraform format/validate, container build. Staging additionally requires 50-stream load test, backup/restore, live integrations and rollback. Do not reinterpret skipped checks as passes.
