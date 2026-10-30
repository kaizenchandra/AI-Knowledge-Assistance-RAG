# Agent workflows

Chat state: question, KB, verified actor, bounded recent history, evidence, answer, citations. Each run gets a fresh tenant-prefixed thread ID. Graph nodes: retrieve → answer if evidence exists, otherwise abstain → END. PostgreSQL checkpoint saver persists state. Request timeout is 45 seconds, recursion limit 8, six retrieved chunks, 16,000 context characters, 4,000-character question, six recent messages truncated to 2,000 characters each, and live model output cap 1,200 tokens.

Only custom stage/token events and a final answer reach the UI. Checkpoints can contain sensitive evidence; restrict database access and include them in retention/deletion policy. A durable checkpoint does not currently provide a public chat-run resume API. Approval resumption is implemented independently of SSE reconnection.

Approval graph interrupts before any mutation. API authorizes administrator, locks approval, checks expiry and commits an immutable decision. Command(resume=...) resumes the tenant-scoped graph. The node rechecks the database decision, approver membership, source ownership and terminal receipt, then creates one new document generation/job transactionally. Supported tool is explicitly requested document reprocessing; there is no unrestricted LLM tool dispatcher.

Current limitations: no iterative planning/rewrite/reranking, token-cost ledger, provider-priced budgets, semantic memory, claim-level entailment verification or independently acting specialist agents. Citation-number validity does not prove claim support. These remain open requirements, not hidden mocked nodes.
