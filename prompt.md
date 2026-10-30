# MASTER PROMPT — END-TO-END ENTERPRISE AI AGENTIC RAG PLATFORM

## 1. ROLE AND MISSION

Act as a **Principal AI Architect, Enterprise Solution Architect, Staff Full-Stack Engineer, AI/ML Engineer, LLM Engineer, Security Architect, DevOps/SRE Engineer, and QA Automation Lead**.

Your task is to **design, architect, implement, test, deploy, and document a complete, real-time, enterprise-grade AI Agentic Retrieval-Augmented Generation (RAG) platform**.

The system must use:

- **LangGraph:** Stateful agent orchestration, workflows, conditional routing, persistence, and human-in-the-loop execution.
- **LangChain:** LLM integrations, retrievers, document loaders, embedding integrations, tools, and structured outputs.
- **Pinecone:** Managed vector database for semantic retrieval, metadata filtering, and tenant-aware knowledge isolation.
- **Python + FastAPI:** Backend APIs and AI orchestration.
- **Next.js + React + TypeScript:** Interactive, modern frontend.
- **PostgreSQL:** Transactional and application data.
- **Redis:** Caching, rate limiting, and appropriate ephemeral state.
- **AWS:** Cloud infrastructure, storage, security, monitoring, and deployment.

The result must be an **actually runnable full-stack application**, not a conceptual architecture, isolated chatbot example, collection of notebooks, or frontend mockup.

Implement real integrations with documented development alternatives when credentials or external infrastructure are unavailable.

### Primary business use case

Build an **Enterprise Knowledge Intelligence Assistant** that enables organizations to:

1. Upload and manage enterprise knowledge.
2. Automatically process, chunk, embed, and index documents in Pinecone.
3. Ask natural-language questions against authorized enterprise information.
4. Receive grounded answers with verifiable source citations.
5. Perform multi-step reasoning through LangGraph workflows.
6. Retrieve information from multiple authorized knowledge sources.
7. Execute approved tools and business workflows.
8. Stream answers and execution progress in real time.
9. Resume interrupted, failed, or human-approved workflows.
10. Monitor AI quality, performance, security, and operational costs.

Build this as a multi-tenant, extensible enterprise application supporting multiple organizations, workspaces, knowledge bases, users, and conversations.

---

# 2. NON-NEGOTIABLE ENGINEERING INSTRUCTIONS

Follow these instructions throughout the project.

1. **Inspect before implementation:** When a repository exists, examine its structure, dependency versions, scripts, coding standards, configuration, and existing tests. Follow applicable repository instructions.
2. **Requirements first:** Produce functional requirements, non-functional requirements, acceptance criteria, and an implementation roadmap before making significant code changes.
3. **Architecture before complexity:** Design appropriate bounded contexts and service boundaries. Prefer a modular monolith with independently executable ingestion workers unless evidence justifies microservices.
4. **Working implementation:** Do not stop after planning. Implement the agreed scope end to end, including the frontend, backend, AI workflows, infrastructure configuration, and tests.
5. **Production-oriented engineering:** Address timeouts, retries, idempotency, authorization, concurrency, data integrity, failure recovery, observability, resource limits, and secure deployment.
6. **No fake completion:** Never claim an integration, deployment, test, benchmark, or production-readiness requirement succeeded unless it was actually verified.
7. **No unnecessary overengineering:** Apply DDD, SOLID, Clean Architecture, and Hexagonal Architecture pragmatically.
8. **Version accuracy:** Verify current official documentation and compatible library versions before implementation. Pin dependencies and do not rely on obsolete LangChain, LangGraph, Pinecone, or cloud APIs.
9. **No hardcoded secrets:** Use environment configuration and a secrets-management solution.
10. **Incremental delivery:** Work through vertical slices, validating the frontend-to-backend-to-database path after each major feature.
11. **Secure by design:** Never rely on LLM-generated decisions as the sole authority for access control or privileged operations.
12. **No placeholder core functionality:** Mock providers are allowed for tests and offline development, but real integrations must be implemented where credentials are available.

If requirements are ambiguous, choose sensible defaults, document assumptions, and proceed. Ask questions only when the choice materially affects correctness, security, cost, or architecture.

---

# 3. TECHNOLOGY STACK AND ARCHITECTURE BASELINE

Use the following stack unless repository constraints or verified technical evidence justify another choice.

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Styling | Tailwind CSS, accessible component primitives |
| Frontend state | TanStack Query and minimal local state |
| Backend API | Python 3.12+, FastAPI, Pydantic |
| AI orchestration | LangGraph |
| LLM integration | LangChain |
| Vector database | Pinecone |
| Embeddings | Configurable embedding provider |
| LLM | Configurable provider and model |
| Relational database | PostgreSQL |
| Database migrations | Alembic |
| ORM | SQLAlchemy |
| Cache and rate limits | Redis |
| Object storage | Amazon S3 |
| Async ingestion | Durable queue and background worker |
| Event messaging | Amazon SQS by default; Kafka only when justified |
| Authentication | OIDC/OAuth 2.0-compatible identity provider |
| Observability | OpenTelemetry, metrics, logs, traces |
| AI tracing | LangSmith or a compatible tracing backend |
| Testing | Pytest, Playwright, frontend unit/component tests |
| Containerization | Docker |
| Local infrastructure | Docker Compose |
| Infrastructure as Code | Terraform |
| Cloud runtime | AWS ECS or EKS, selected through an ADR |
| CI/CD | GitHub Actions or repository-standard platform |
| Deployment | Automated staging and controlled production deployment |

### Architectural decisions

Use Hexagonal Architecture with:

- Domain layer
- Application/use-case layer
- Ports/interfaces
- Infrastructure/adapters layer
- API/presentation layer

Separate business rules and agent orchestration from Pinecone SDK calls, LLM provider implementations, database queries, and HTTP controllers.

Use a provider-independent abstraction for models, embeddings, reranking, and vector search.

Do not introduce a separate Java/Spring Boot service merely for architectural appearance. If enterprise integration requirements justify one, provide an ADR explaining the added service boundary.

---

# 4. STAGE ONE — COMPLETE FUNCTIONAL REQUIREMENTS

**Your first deliverable must be a detailed Functional Requirements Specification (FRS).**

Assign each requirement a unique identifier, priority (P0/P1/P2), user role, description, acceptance criteria, business value, API implications, UI implications, dependencies, and test scenarios.

At minimum, cover the following functional areas.

## FR-01: Authentication and Identity Management

Implement:

- User sign-in/sign-out.
- OIDC-compatible authentication.
- Access token validation.
- Refresh/session lifecycle handling.
- Session expiration and revocation.
- Role-based access control (RBAC).
- Tenant and workspace membership.
- Administrative roles.
- Secure API authorization.
- Protected frontend routes.
- Audit events for security-sensitive actions.

Use a development identity provider or documented local alternative where enterprise SSO is unavailable.

## FR-02: Multi-Tenant Workspace Management

Implement:

- Organization/tenant creation and administration.
- Workspace creation and management.
- Knowledge base creation.
- User roles and membership.
- Document-level access policies.
- Tenant-aware resource ownership.
- Tenant-specific configurations and quotas.
- Tenant-aware monitoring and cost reporting.
- Tenant offboarding and data deletion.

**Critical:** Tenant isolation must be enforced server-side in PostgreSQL, object storage, vector retrieval, document access, cache access, and agent tools.

## FR-03: Knowledge Base and Document Management

Implement:

- Drag-and-drop document uploads.
- Multi-file uploads.
- File validation and size limits.
- PDF, DOCX, TXT, Markdown, and HTML ingestion.
- File metadata inspection.
- Document preview.
- Document version history.
- Document tagging.
- Document status tracking.
- Delete, replace, and reprocess operations.
- Knowledge base selection and management.
- Bulk document operations.
- Upload and indexing progress.
- Document-level access permissions.

Treat URL ingestion and scanned-PDF OCR as configurable extensions with explicit security and resource controls.

## FR-04: Intelligent Document Ingestion Pipeline

Implement a real asynchronous ingestion workflow:

1. Receive the document.
2. Authenticate and authorize upload.
3. Validate type, size, and content.
4. Malware-scan or quarantine according to policy.
5. Store the original in protected object storage.
6. Persist document metadata and ingestion job.
7. Dispatch a durable ingestion event.
8. Extract text.
9. Normalize and clean content.
10. Detect and handle duplicates.
11. Chunk text intelligently.
12. Preserve chunk-to-document relationships.
13. Generate embeddings.
14. Write records to Pinecone.
15. Verify indexing and publish a searchable status.
16. Report progress, errors, and retry eligibility.

Support safe retries, deterministic identifiers, dead-letter handling, partial-failure recovery, and idempotent reprocessing.

## FR-05: Pinecone Vector Database Integration

Implement actual Pinecone integration supporting:

- Index provisioning.
- Correct embedding dimension and similarity metric.
- Serverless index configuration.
- Namespace-based tenant partitioning.
- Metadata filtering.
- Vector upserts.
- Similarity search.
- Vector deletion.
- Batch ingestion.
- Indexing status verification.
- Reindexing after model changes.
- Version-aware retrieval.
- Access-aware search.
- Query performance monitoring.

Define metadata such as:

- tenant_id
- workspace_id
- knowledge_base_id
- document_id
- document_version
- chunk_id
- source
- filename
- content_type
- access_scope
- created_at
- embedding_model_version
- ingestion_version

Select metadata fields and values compatible with the verified Pinecone API and filtering capabilities.

Do not assume an acknowledged vector write is immediately query-visible. Design for read-after-write freshness limitations.

## FR-06: Advanced Retrieval Engine

Implement:

- Dense semantic search.
- Configurable top-k retrieval.
- Query rewriting.
- Metadata filtering.
- Permission-aware retrieval.
- Document deduplication.
- Context window management.
- Reranking.
- Score thresholds calibrated against an evaluation dataset.
- Retrieval evaluation.
- Optional hybrid dense/sparse search after baseline measurement.
- Source provenance preservation.

Compare a straightforward retrieval baseline against enhanced retrieval. Retain improvements only when evaluation evidence justifies their latency and cost.

## FR-07: AI Agentic RAG Workflows

Implement a bounded, stateful LangGraph workflow supporting:

1. User query validation.
2. Intent classification.
3. Query planning where needed.
4. Retrieval routing.
5. Knowledge retrieval.
6. Relevance assessment.
7. Bounded query reformulation.
8. Optional authorized tool execution.
9. Evidence consolidation.
10. Answer generation.
11. Source citation construction.
12. Grounding checks.
13. Final response.
14. Human escalation when required.

Provide explicit graph state models, nodes, edges, conditional transitions, retry policies, and termination conditions.

Use deterministic steps for operations that do not require LLM reasoning.

Prevent infinite agent loops through configured step, time, token, and cost budgets.

## FR-08: Multi-Agent Collaboration

Design an optional extension using specialized agents:

- Coordinator/planner.
- Retrieval specialist.
- Research specialist.
- Answer synthesis specialist.
- Verification specialist.
- Tool-execution specialist.

Initially implement the simplest graph that meets the primary use case.

Introduce multiple independently acting agents only when benchmarked benefits outweigh extra latency, cost, and complexity.

## FR-09: Real-Time AI Chat

Implement a fully integrated conversational interface supporting:

- Chat creation.
- Streaming assistant responses.
- Streaming status messages.
- Stop/cancel generation.
- Chat history.
- Follow-up questions.
- Context-aware conversations.
- Session management.
- Conversation renaming and deletion.
- Regenerate answer.
- Copy response.
- Source citation interactions.
- Error and retry states.
- Chat feedback.
- Response completion indicators.

Use **Server-Sent Events (SSE)** as the default transport for streaming LLM output and graph progress.

Support authenticated streams, client cancellation, bounded event buffering, disconnect handling, and clear final/error events.

Define resumable run behavior separately from transport-level reconnection.

## FR-10: Source Citations and Explainability

Each evidence-based answer must include verifiable citations where supporting knowledge exists.

Implement:

- Source document identifiers.
- Source titles.
- Referenced chunks.
- Page/section information where available.
- Source previews.
- Citation links.
- Evidence availability checks.
- Source version tracking.
- Authorized source retrieval.
- Unsupported-claim handling.

Do not generate fictional citations.

When evidence is missing, stale, contradictory, or insufficient, clearly state the limitation instead of inventing an answer.

## FR-11: Human-in-the-Loop Approval

Implement LangGraph-based approval workflows for privileged tool operations.

Support:

- Paused execution.
- Durable checkpoints.
- Approval requests.
- Approval/rejection UI.
- Authorized approvers.
- Approval expiration.
- Workflow resumption.
- Audit history.
- Rejection and cancellation paths.
- Idempotent side effects after resumption.

Approval must be enforced server-side, not solely through an LLM instruction or frontend confirmation.

## FR-12: Agent Tools and External Integrations

Provide a secure tool registry supporting:

- Pinecone search.
- Authorized document metadata lookup.
- Knowledge base lookup.
- Safe internal API integrations.
- Optional external knowledge connectors.
- Read-only structured business queries where justified.

Each tool must define:

- Validated input/output schemas.
- Authorization requirements.
- Allowed operations.
- Timeout.
- Retry policy.
- Rate limit.
- Audit behavior.
- Error handling.
- Approval requirements.
- Idempotency behavior for mutations.

Do not expose unrestricted shell execution, arbitrary SQL, unrestricted browsing, or privileged APIs to the LLM.

## FR-13: Conversation Memory

Support:

- Short-term conversation context.
- Persistent LangGraph checkpoints.
- Conversation restoration.
- Controlled history summarization.
- Context truncation.
- Memory retention policies.
- Tenant isolation.
- User-controlled deletion.
- Optional long-term memory with explicit scope and consent.

Explain the distinction between graph checkpoints, conversation history, semantic memory, and the enterprise knowledge base.

## FR-14: Feedback and AI Quality Evaluation

Implement:

- Thumbs-up/down feedback.
- Optional feedback comments.
- Answer quality reporting.
- Failed-query analytics.
- Citation accuracy evaluation.
- Retrieval relevance evaluation.
- Groundedness/faithfulness evaluation.
- Latency and token monitoring.
- Evaluation dataset management.
- Prompt/model version comparisons.
- Regression testing.
- Cost-per-answer analysis.

Provide baseline metrics and representative golden test cases.

## FR-15: Administration and Analytics

Implement an administrative dashboard showing:

- User and workspace metrics.
- Document counts.
- Ingestion status.
- Failed ingestion jobs.
- Query volume.
- Model usage.
- Token consumption.
- Estimated LLM costs.
- Retrieval latency.
- End-to-end answer latency.
- Error rates.
- Agent execution outcomes.
- Feedback trends.
- Evaluation results.
- Quota consumption.

Provide filtering by tenant, workspace, date, and status where authorized.

## FR-16: Notifications and Operational Events

Support meaningful notifications for:

- Successful indexing.
- Ingestion failures.
- Approval requests.
- Approval completion.
- Processing failures.
- Quota warnings.
- Administrative events.

Use in-app notifications first. Implement optional email/webhook integrations when justified.

---

# 5. STAGE TWO — COMPLETE NON-FUNCTIONAL REQUIREMENTS

**Your second deliverable must be a detailed Non-Functional Requirements Specification (NFRS).**

For every NFR, define measurable acceptance criteria, validation strategy, responsible component, and release gate.

## NFR-01: Performance

Establish initial engineering targets, then validate against realistic infrastructure and model-provider conditions.

Suggested starting targets:

- p95 time to first streamed token: no more than 3 seconds.
- p95 completed standard RAG answer: no more than 12 seconds.
- p95 non-AI API latency: no more than 300 ms under the defined test load.
- Sustained 50 concurrent active streaming conversations in initial load testing.
- Query and ingestion workloads must not starve one another.

Measure the baseline and record exceptions instead of claiming targets are guaranteed.

## NFR-02: Scalability

Design for:

- Horizontal API scaling.
- Independent ingestion worker scaling.
- Bounded execution concurrency.
- Autoscaling based on meaningful resource and backlog metrics.
- Queue backpressure.
- Per-tenant rate limits and quotas.
- Predictable degradation under overload.

Document capacity assumptions and a cost-conscious scaling strategy.

## NFR-03: Availability and Reliability

Target 99.9% service availability for the initial production design, subject to confirmed provider capabilities and budget.

Implement:

- Health/readiness endpoints.
- Dependency failure detection.
- Timeouts.
- Circuit breaking where useful.
- Bounded retries with exponential backoff and jitter.
- Idempotent operations.
- Failure isolation.
- Graceful degradation.
- Recovery procedures.
- Explicit backup and restore tests.

## NFR-04: Security

Apply:

- OWASP ASVS principles.
- OWASP API Security recommendations.
- OWASP LLM Top 10 (current edition).
- Agentic AI threat modeling.
- Least privilege.
- Server-side authorization.
- Encryption in transit and at rest.
- Secret management.
- Data classification.
- Secure document processing.
- Prompt-injection defenses.
- Tool execution restrictions.
- Output validation.
- Audit logging.
- Supply chain security.

Demonstrate that malicious retrieved content cannot grant itself additional privileges.

## NFR-05: Privacy and Compliance

Provide controls for:

- Sensitive data identification.
- PII minimization.
- Data retention.
- Secure deletion.
- Tenant-specific data handling.
- Cross-border data residency assumptions.
- Provider data-processing configuration.
- Logging redaction.
- Consent where required.
- Auditability.

Document applicable regulatory requirements rather than asserting compliance or certification without evidence.

## NFR-06: Observability

Implement:

- Structured logs.
- Correlation/request IDs.
- Distributed tracing.
- LangGraph workflow telemetry.
- LLM request tracing.
- Retrieval metrics.
- Error metrics.
- Token and cost metrics.
- Operational dashboards.
- Alerts.
- Incident investigation support.

Protect prompts, document contents, and sensitive metadata in observability systems.

## NFR-07: Maintainability

Require:

- Clear domain boundaries.
- Explicit dependency direction.
- Type-safe contracts.
- Small cohesive components.
- Dependency injection.
- Database migration discipline.
- Automated linting and formatting.
- Architecture Decision Records.
- API documentation.
- Contributor documentation.
- Reproducible builds.

## NFR-08: Testability

All core business and AI workflows must be testable using controlled model and infrastructure adapters.

Support deterministic tests with recorded or mocked LLM responses, plus separate live-provider integration tests.

## NFR-09: Portability

Containerize application components.

Avoid unnecessary provider coupling outside infrastructure adapters.

Support local development without requiring a Kubernetes cluster.

## NFR-10: Cost Efficiency

Measure:

- LLM token cost.
- Embedding cost.
- Vector operations.
- Storage costs.
- Infrastructure costs.
- Cost per successful answer.
- Cost per ingested document.
- Cost per tenant.

Implement configurable token budgets, graph step budgets, batching, caching where safe, and model selection policies.

## NFR-11: Data Integrity and Consistency

Document ownership and transaction boundaries.

PostgreSQL must remain the source of truth for application metadata and access policies.

Pinecone is a derived search index, not the authoritative record for authorization or document lifecycle.

Implement reconciliation for partial failures, deleted documents, outdated vectors, and failed reindexing.

## NFR-12: Accessibility and User Experience

Target WCAG 2.2 AA where applicable.

Support:

- Responsive layouts.
- Keyboard navigation.
- Screen readers.
- Accessible contrast.
- Clear loading states.
- Recoverable errors.
- Perceived performance optimization.
- Dark/light themes.
- Mobile-friendly interactions.

## NFR-13: Disaster Recovery

Define:

- RPO and RTO.
- PostgreSQL backup strategy.
- Object storage versioning.
- Workflow checkpoint recovery.
- Infrastructure recovery.
- Vector index rebuild strategy.
- Restore validation.
- Disaster recovery runbooks.

## NFR-14: AI Quality and Safety

Set initial evaluation targets for:

- Retrieval recall.
- Answer groundedness.
- Citation accuracy.
- Unsupported-answer handling.
- Prompt-injection resistance.
- Cross-tenant isolation.
- Agent tool correctness.
- Workflow termination.
- Cost efficiency.

Establish and measure a baseline before setting final release thresholds.

Do not use raw answer similarity alone as the definition of correctness.

---

# 6. STAGE THREE — SYSTEM ARCHITECTURE AND DESIGN

Before implementation, produce a comprehensive architecture specification.

## 6.1 Required Architecture Artifacts

Produce:

1. Executive architecture summary.
2. System context diagram.
3. C4 container diagram.
4. Frontend component architecture.
5. Backend component architecture.
6. DDD bounded-context diagram.
7. Clean/Hexagonal Architecture diagram.
8. Agent orchestration graph.
9. Document ingestion sequence diagram.
10. Agent query sequence diagram.
11. Streaming lifecycle diagram.
12. Data model/ER diagram.
13. Deployment architecture.
14. Security trust boundary diagram.
15. Failure recovery diagram.

Use Mermaid diagrams where practical.

## 6.2 Backend Domain-Driven Design

Start with the following candidate bounded contexts:

- Identity and Access
- Tenant and Workspace
- Knowledge Management
- Document Ingestion
- Retrieval
- Agent Orchestration
- Conversation Management
- Evaluation and Feedback
- Usage and Billing Analytics
- Audit and Operations

Refine boundaries based on domain invariants and cohesive use cases rather than creating a separate deployable service per context.

Define:

- Aggregates.
- Aggregate roots.
- Entities.
- Value objects.
- Domain services.
- Application services.
- Repositories.
- Ports.
- Adapters.
- Domain events.
- Integration events.
- Transaction boundaries.
- Authorization policies.
- Domain-specific exceptions.

Use interfaces/ports for external dependencies, including:

- VectorStorePort
- EmbeddingProviderPort
- LLMProviderPort
- DocumentStoragePort
- DocumentParserPort
- JobQueuePort
- ConversationRepositoryPort
- CheckpointStorePort
- AuditEventPort

Adapt names and interfaces to actual use cases. Avoid generic abstractions with no meaningful alternative implementation or testing benefit.

## 6.3 Data Architecture

Design PostgreSQL entities such as:

- Tenant
- User
- TenantMembership
- Workspace
- WorkspaceMembership
- KnowledgeBase
- Document
- DocumentVersion
- DocumentChunkMetadata
- IngestionJob
- IngestionAttempt
- Conversation
- Message
- AgentRun
- AgentExecutionEvent
- ToolApproval
- UserFeedback
- EvaluationDataset
- EvaluationRun
- UsageRecord
- AuditEvent

Define:

- Primary/foreign keys.
- Unique constraints.
- Tenant scoping.
- Indexes.
- Optimistic concurrency where appropriate.
- Retention policies.
- Soft vs hard deletion.
- Referential integrity.
- Migration strategy.

Define clear consistency and reconciliation contracts among PostgreSQL, S3, Pinecone, the event queue, and LangGraph checkpoints.

## 6.4 Agentic RAG Architecture

Design an explicit workflow:

**START → Validate Request → Authorize → Classify Intent → Plan/Route → Retrieve → Assess Evidence → Rewrite if Necessary → Rerank → Generate Grounded Answer → Validate Citations → Stream Result → END**

Add optional conditional paths for:

- No relevant documents.
- Retrieval service failure.
- Model timeout.
- Ambiguous question.
- Human approval.
- Authorized tool execution.
- Excessive token usage.
- Agent step limit.
- Cancellation.

Specify the graph's typed state, checkpoint policy, event model, routing rules, and terminal outcomes.

Ensure that any external side effect can be safely handled during retry, interruption, or checkpoint replay.

## 6.5 Retrieval Strategy

Design an evaluation-driven retrieval pipeline.

Baseline:

1. Query normalization.
2. Authorization-aware source filtering.
3. Embedding generation.
4. Pinecone search.
5. Context selection.
6. Grounded answer generation.

Evaluate enhancements:

- Multi-query retrieval.
- Hybrid search.
- Reranking.
- Contextual compression.
- Parent-child retrieval.
- Metadata-aware routing.
- Semantic chunking.
- Query decomposition.

Select enhancements using measured quality, latency, and cost.

## 6.6 API Contract Design

Design versioned APIs such as:

- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `DELETE /api/v1/documents/{id}`
- `POST /api/v1/documents/{id}/reprocess`
- `GET /api/v1/ingestion-jobs/{id}`
- `POST /api/v1/knowledge-bases`
- `GET /api/v1/knowledge-bases`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations/{id}/messages`
- `GET /api/v1/agent-runs/{id}/events`
- `POST /api/v1/agent-runs/{id}/cancel`
- `POST /api/v1/agent-runs/{id}/resume`
- `POST /api/v1/tool-approvals/{id}/decision`
- `POST /api/v1/feedback`
- `GET /api/v1/admin/metrics`

Treat this list as a starting contract.

Specify request/response schemas, authorization rules, pagination, error semantics, idempotency, and OpenAPI documentation.

For SSE, document the event envelope and events such as `run.started`, `agent.step`, `token.delta`, `citation`, `approval.required`, `run.completed`, and `run.failed`.

Avoid exposing hidden model reasoning or confidential tool parameters to users.

---

# 7. STAGE FOUR — FRONTEND UI/UX DESIGN

Build an innovative, immersive, modern enterprise AI application.

### Design direction

- Premium SaaS visual quality.
- Modern dark-first appearance with optional light theme.
- Restrained gradients and glass effects.
- Professional typography.
- Smooth but lightweight animations.
- Consistent spacing and responsive grids.
- Accessible controls.
- Clear information hierarchy.
- Persistent navigation.
- Distinct loading, success, empty, and error states.

Do not sacrifice accessibility or performance for visual effects.

### Required screens

**1. Authentication**

Secure sign-in, logout, session-expiry handling, and appropriate error messages.

**2. Main dashboard**

Show knowledge bases, recent conversations, document processing activity, and usage statistics.

**3. AI Agent Chat Workspace**

Implement:

- ChatGPT-style conversation layout.
- Streaming answer rendering.
- Markdown and code rendering with sanitization.
- Citation indicators.
- Source reference panel.
- Visible agent progress states.
- Conversation history sidebar.
- Knowledge base selector.
- Stop/retry controls.
- Feedback actions.
- Responsive message composer.

**4. Knowledge Base Management**

Create, update, view, and delete authorized knowledge bases.

**5. Document Management**

Provide file upload, drag-and-drop, upload validation, indexing progress, status, previews, versions, filters, and delete/reprocess actions.

**6. Agent Workflow Viewer**

Show a safe, user-facing visualization of graph execution:

- Current stage.
- Completed stages.
- Retrieval activity.
- Tool execution status.
- Pending approvals.
- Failures and retries.
- Final result.

Do not expose private chain-of-thought.

**7. Human Approval Center**

Allow authorized users to review, approve, reject, or inspect pending actions.

**8. Analytics Dashboard**

Display ingestion, retrieval, response latency, token usage, quality, errors, and estimated costs.

**9. User and Workspace Settings**

Implement membership, preferences, quotas, and relevant access policies.

**10. Administrator Console**

Manage tenants, users, permissions, ingestion failures, and operational settings.

### Frontend engineering standards

Use:

- Strongly typed API contracts.
- Reusable components.
- Accessible forms.
- Controlled server state.
- Minimal unnecessary global state.
- Error boundaries.
- Safe Markdown rendering.
- Secure authentication integration.
- SSE connection cleanup.
- Optimistic updates only where appropriate.
- Browser automation tests.

Every frontend action must invoke an actual implemented backend flow. Do not leave inert buttons or permanently hardcoded dashboards.

---

# 8. STAGE FIVE — DEVELOPMENT AND IMPLEMENTATION PHASES

Produce a development roadmap with dependencies, deliverables, testing obligations, and exit criteria.

Use the following phases as the default implementation order.

## Phase 0 — Repository Discovery and Requirements

Deliver:

- Repository assessment.
- Assumptions.
- Functional requirements.
- Non-functional requirements.
- User stories.
- Acceptance criteria.
- Dependency matrix.
- Traceability matrix.
- Prioritized backlog.

**Exit:** Requirements and scope are documented and internally consistent.

## Phase 1 — Architecture and Project Foundation

Implement:

- Repository organization.
- Backend application bootstrap.
- Frontend application bootstrap.
- Domain/application/infrastructure boundaries.
- Shared configuration conventions.
- Dependency management.
- Docker Compose.
- Logging.
- Health checks.
- Database migrations.
- Development documentation.

**Exit:** Frontend and backend start locally, PostgreSQL/Redis connectivity works, and foundational tests pass.

## Phase 2 — Identity, Tenancy, and Knowledge Management

Implement:

- Authentication.
- Authorization.
- Tenant/workspace model.
- Membership.
- Knowledge base CRUD.
- Document metadata model.
- Access enforcement.
- Initial frontend screens.

**Exit:** Users can access only resources authorized to their tenant and workspace.

## Phase 3 — Document Ingestion and Pinecone

Implement:

- File upload API.
- S3-compatible storage.
- Ingestion queue.
- Worker.
- Parser.
- Chunking.
- Embeddings.
- Pinecone upsert.
- Job progress.
- Retry/recovery.
- Document deletion and reindexing.
- Ingestion dashboard.

**Exit:** A real uploaded document becomes searchable, and deletion/reprocessing behavior is verified.

## Phase 4 — Core RAG Engine

Implement:

- Embedding adapter.
- Pinecone retriever.
- Metadata filters.
- Knowledge base authorization.
- Context construction.
- LLM integration.
- Grounded answer generation.
- Citation resolution.
- Retrieval evaluation baseline.

**Exit:** An authorized user can ask a question and receive a grounded answer with valid citations.

## Phase 5 — LangGraph Agent Orchestration

Implement:

- Typed graph state.
- Conditional nodes.
- Retrieval planning.
- Evidence assessment.
- Bounded query rewriting.
- Tool registry.
- Checkpointing.
- Failure handling.
- Agent budgets.
- Human approval.
- Workflow continuation.

**Exit:** Graph executions can complete, pause, reject, resume, fail safely, and recover according to their documented contracts.

## Phase 6 — Real-Time Full-Stack Chat

Implement:

- Conversation management.
- SSE streaming.
- Agent progress.
- Source preview.
- Conversation history.
- Stop/retry controls.
- Frontend state management.
- Error handling.
- Reconnection behavior.
- Responsive chat UX.

**Exit:** Complete browser-to-backend-to-agent-to-Pinecone workflows operate without mock frontend responses.

## Phase 7 — Advanced Retrieval and Quality

Implement and evaluate:

- Reranking.
- Query reformulation.
- Hybrid retrieval if beneficial.
- Context optimization.
- Citation validation.
- Feedback collection.
- Quality dashboards.
- Automated evaluation.
- Regression datasets.

**Exit:** Retrieval and response quality have measurable baselines, and selected optimizations show documented benefits.

## Phase 8 — Security, Resilience, and Operations

Implement:

- Security hardening.
- Prompt-injection controls.
- Rate limits.
- Quotas.
- Timeout policies.
- Bounded retries.
- Backpressure.
- Observability.
- Cost monitoring.
- Audit logs.
- Backup/restore procedures.
- Operational alerts.

**Exit:** Critical security and failure-path tests pass, with residual risks documented.

## Phase 9 — Cloud Deployment and CI/CD

Implement:

- Production-oriented Docker images.
- Terraform infrastructure.
- Managed PostgreSQL.
- Managed Redis where justified.
- S3.
- IAM and secret management.
- AWS deployment environment.
- CI/CD workflows.
- Database migration deployment.
- Health checks.
- Autoscaling configuration.
- Rollback strategy.
- Monitoring.
- Staging environment.

**Exit:** A deployed staging system passes smoke, security, and end-to-end tests. Production deployment requires its own approval and readiness gates.

## Phase 10 — Production Readiness Assessment

Deliver:

- Performance test results.
- Security assessment.
- AI evaluation report.
- Disaster recovery review.
- Operational runbooks.
- Capacity planning.
- Cost estimates.
- Deployment/rollback verification.
- Known limitations.
- Go/no-go checklist.

**Exit:** Clearly distinguish verified readiness from outstanding risks and untested assumptions.

---

# 9. STAGE SIX — COMPLETE TESTING STRATEGY

Create a testing plan before implementation and maintain it throughout development.

## 9.1 Unit Tests

Test:

- Domain invariants.
- Validation.
- Authorization policies.
- Ingestion state transitions.
- Chunk ID generation.
- Duplicate detection.
- Retry decisions.
- Agent routing.
- Structured response parsing.
- Budget enforcement.

## 9.2 Integration Tests

Use realistic test dependencies or containers where appropriate.

Verify:

- FastAPI and PostgreSQL.
- Database migrations.
- Ingestion queue and worker.
- Storage integration.
- Pinecone adapter.
- LangChain provider adapters.
- LangGraph persistence.
- Cache behavior.
- SSE event delivery.

Keep tests requiring paid external services isolated from ordinary CI.

## 9.3 End-to-End Tests

Using Playwright, verify:

1. Login.
2. Create workspace.
3. Create knowledge base.
4. Upload document.
5. Observe indexing progress.
6. Ask a question.
7. Receive streamed answer.
8. Open valid citation.
9. Start follow-up conversation.
10. Review agent progress.
11. Approve/reject controlled action.
12. Delete document.
13. Confirm removed content is inaccessible.

## 9.4 AI/RAG Evaluation

Build a versioned golden dataset containing:

- Straightforward factual questions.
- Multi-document questions.
- Ambiguous questions.
- Unanswerable questions.
- Conflicting documents.
- Stale source versions.
- Low-relevance retrieval.
- Adversarial instructions.
- Cross-tenant questions.
- Multi-step agent workflows.

Evaluate:

- Recall@k.
- Precision@k.
- MRR/NDCG where useful.
- Answer correctness.
- Faithfulness/groundedness.
- Citation precision.
- Citation coverage.
- Abstention accuracy.
- Tool selection accuracy.
- Token consumption.
- Latency.
- Cost.

Use deterministic checks where feasible; calibrate model-based evaluators and retain human-reviewed examples.

## 9.5 Security Tests

Test:

- Broken authentication.
- Broken object-level authorization.
- Cross-tenant document leakage.
- Cross-tenant vector access.
- Citation endpoint authorization.
- Prompt injection.
- Malicious documents.
- Unauthorized tool execution.
- Forged approval decisions.
- Approval replay.
- SSRF through URL ingestion.
- Oversized uploads.
- Malformed file parsing.
- Secret disclosure.
- Sensitive logging.
- Resource exhaustion.

## 9.6 Load and Reliability Tests

Test:

- Concurrent chats.
- Streaming connection churn.
- Large ingestion batches.
- Queue backlog recovery.
- Database pool exhaustion.
- Pinecone throttling.
- Model provider 429/5xx.
- Agent timeout.
- Worker crash.
- Duplicate events.
- Checkpoint recovery.
- Deployment interruption.
- Deleted-document retrieval races.

Record actual measurements and test environment characteristics.

---

# 10. STAGE SEVEN — DEPLOYMENT AND DEVOPS

Design a reproducible deployment pipeline.

## Environment Strategy

Provide:

- Local development.
- Automated test environment.
- Staging.
- Production.

Keep secrets and persistent resources isolated by environment.

## CI Pipeline

Implement:

1. Dependency installation.
2. Formatting checks.
3. Static analysis.
4. Type checks.
5. Unit tests.
6. Integration tests.
7. Frontend build.
8. Backend build.
9. Container build.
10. Dependency/security scanning.
11. Infrastructure validation.
12. Artifact publishing.

## CD Pipeline

Implement:

1. Artifact promotion.
2. Infrastructure provisioning.
3. Secrets injection.
4. Database migrations.
5. Deployment rollout.
6. Readiness verification.
7. Smoke tests.
8. Critical E2E tests.
9. Monitoring verification.
10. Rollback on failure.

Production releases should use protected environments and appropriate approval gates.

## Infrastructure Requirements

Define and implement configuration for:

- AWS networking.
- Private database connectivity.
- S3 buckets.
- Managed database.
- Application runtime.
- Worker runtime.
- Secrets management.
- IAM policies.
- Load balancing.
- TLS.
- Logging.
- Monitoring.
- Autoscaling.
- Backup policies.
- Resource budgets.

Prefer managed cloud services when they reduce operational burden.

Use Terraform modules with scoped permissions and clearly documented prerequisites.

Never hardcode cloud credentials or imply that creating IaC equals deploying infrastructure.

---

# 11. REQUIRED DOCUMENTATION AND DELIVERABLES

Produce the following project artifacts:

1. `README.md` — Project overview and quick start.
2. `docs/functional-requirements.md`
3. `docs/non-functional-requirements.md`
4. `docs/architecture.md`
5. `docs/domain-design.md`
6. `docs/agent-workflows.md`
7. `docs/data-model.md`
8. `docs/api-design.md`
9. `docs/security.md`
10. `docs/ai-evaluation.md`
11. `docs/testing-strategy.md`
12. `docs/deployment.md`
13. `docs/operations-runbook.md`
14. `docs/production-readiness.md`
15. `docs/implementation-roadmap.md`
16. `docs/architecture-decisions/` for ADRs.

Also deliver:

- Complete frontend source.
- Complete backend source.
- AI agent and retrieval implementation.
- Pinecone integration.
- Database migrations.
- Docker configuration.
- Local development setup.
- Terraform and deployment configuration.
- Automated test suites.
- CI/CD workflows.
- Example environment configuration.
- Safe synthetic seed data.
- Architecture diagrams.
- API documentation.
- Verification report.

Use these paths as a suggested organization, adapting to existing repository conventions.

---

# 12. IMPLEMENTATION QUALITY RULES

All implementations must meet the following standards.

### Backend

- Correct asynchronous I/O boundaries.
- Typed API schemas.
- Domain-centered business logic.
- Explicit authorization.
- Well-defined transactions.
- Idempotency for replayable operations.
- Safe exception mapping.
- Bounded external API calls.
- Consistent pagination.
- Versioned API contracts.
- Structured logging.
- Database migration discipline.

### Agentic AI

- Explicit graph execution state.
- Durable checkpoints.
- Bounded reasoning and tool loops.
- Configurable prompts and models.
- Structured tool schemas.
- No unrestricted agent privileges.
- Verifiable source citations.
- Explicit abstention when evidence is insufficient.
- Safe workflow recovery.
- Quality and cost evaluation.

### Frontend

- Type-safe components.
- Reusable UI patterns.
- Accessible forms and navigation.
- Real backend integration.
- Secure authentication handling.
- Safe streaming cancellation.
- Error recovery.
- Loading and empty states.
- Responsive layouts.
- Automated component and E2E tests.

### Infrastructure

- Least-privilege access.
- Environment separation.
- Encrypted secrets.
- Immutable artifacts.
- Operational observability.
- Repeatable deployments.
- Backup/recovery procedures.
- Rollback support.
- Cost controls.

---

# 13. IMPLEMENTATION PROGRESS AND VERIFICATION REPORTING

At the end of every development phase, provide a concise report with:

**Phase:** Name and scope.

**Implemented:** Concrete files, endpoints, workflows, screens, and infrastructure changes.

**Architecture decisions:** Significant choices and trade-offs.

**Verification executed:** Commands and test results actually observed.

**Unverified items:** Checks or external integrations that could not be run.

**Known issues:** Defects, limitations, and technical debt.

**Remaining risks:** Security, data integrity, reliability, performance, cost, or deployment concerns.

**Next phase:** Next dependency-ordered implementation slice.

Do not mark requirements complete based only on code existing. Verify that the required behavior works.

Track requirements through implementation and tests using stable requirement IDs.

---

# 14. FINAL ACCEPTANCE CRITERIA

The final application must demonstrate the following workflow:

1. A user authenticates.
2. The user creates or selects an authorized workspace.
3. The user creates a knowledge base.
4. The user uploads a document.
5. The backend securely stores the document.
6. A durable worker extracts and chunks its content.
7. The configured embedding provider generates vectors.
8. The ingestion service indexes vectors in Pinecone.
9. The application confirms that content is searchable.
10. The user submits a question.
11. FastAPI authenticates and authorizes the request.
12. LangGraph executes the bounded agent workflow.
13. The retrieval layer searches only authorized knowledge.
14. The model generates an evidence-grounded answer.
15. The response streams to the frontend.
16. The user sees citations linking to authorized source material.
17. The conversation is saved and can be reopened.
18. An approval-required tool action pauses and resumes safely.
19. The user can inspect relevant execution activity.
20. Administrators can monitor activity, failures, quality, and costs.
21. Removing a document makes it inaccessible to subsequent authorized search and citation access according to the documented consistency contract.
22. Automated tests cover the critical workflow and relevant failure paths.
23. The system runs locally using documented instructions.
24. A staging deployment can be executed reproducibly when infrastructure access is available.

Production readiness must be assessed against verified NFRs, not inferred from successful local execution.

---

# 15. REQUIRED RESPONSE AND EXECUTION ORDER

Execute the project using the following strict sequence.

## STEP 1 — Functional Requirements Specification

Begin by writing the complete functional requirements.

For each requirement provide:

- Requirement ID.
- Description.
- User role.
- Business priority.
- User story.
- Acceptance criteria.
- Frontend responsibility.
- Backend responsibility.
- Dependencies.
- Test scenarios.

Distinguish P0 (required end-to-end capabilities), P1 (production hardening), and P2 (optional enhancements).

## STEP 2 — Non-Functional Requirements Specification

Write all NFRs with measurable targets, relevant assumptions, validation methods, and release gates.

## STEP 3 — Architecture and Technical Design

Provide:

- Recommended technology stack.
- Architecture diagrams.
- DDD bounded contexts.
- Clean/Hexagonal Architecture.
- Frontend architecture.
- Backend architecture.
- LangGraph workflow design.
- Pinecone indexing/retrieval design.
- PostgreSQL data model.
- API contracts.
- Security architecture.
- Deployment architecture.
- Architecture Decision Records.

Explain material trade-offs and reject unnecessary complexity.

## STEP 4 — Phased Implementation Plan

Produce a detailed phase-by-phase roadmap with:

- Objectives.
- Tasks.
- Dependencies.
- Deliverables.
- Priority.
- Acceptance criteria.
- Testing activities.
- Exit criteria.
- Risks.
- Completion evidence.

Include a traceability matrix linking requirements to phases and tests.

## STEP 5 — Implement the Application

After planning, execute the implementation phase by phase without unnecessary approval requests.

Implement complete vertical slices, not disconnected backend and frontend examples.

Reuse existing code where appropriate.

## STEP 6 — Test and Verify

Run all applicable checks available in the environment.

Fix failures within the authorized scope.

Never fabricate test results.

## STEP 7 — Deploy or Prepare Deployment

Configure local, staging, and production deployment paths.

Deploy to authorized infrastructure when credentials and permissions exist.

Otherwise provide executable deployment assets and disclose what remains unverified.

## STEP 8 — Final Engineering Report

Conclude with:

1. Completed functional requirements.
2. Completed non-functional requirements.
3. Architecture summary.
4. Implemented features.
5. Technologies and versions.
6. Test results.
7. Deployment status.
8. Performance measurements.
9. Security assessment.
10. AI evaluation findings.
11. Cost assumptions.
12. Known limitations.
13. Remaining risks.
14. Production-readiness verdict.
15. Recommended next improvements.

---

## FINAL DIRECTIVE

**Your responsibility is to deliver a functioning, enterprise-oriented AI Agentic RAG application with a demonstrable end-to-end workflow.**

Do not deliver only architecture diagrams, requirements, UI prototypes, pseudocode, sample notebooks, or disconnected API snippets.

Use Pinecone for real vector retrieval, LangGraph for meaningful stateful orchestration, LangChain for relevant AI integrations, FastAPI for real backend APIs, and Next.js for a fully integrated user experience.

Prioritize correctness, maintainability, enterprise security, data isolation, observability, measurable AI quality, and operational reliability.

**Start immediately with STEP 1: the complete Functional Requirements Specification. Then complete STEP 2, STEP 3, and STEP 4 before beginning implementation. Continue implementing and verifying the planned phases within the available environment.**
