# Knowledge Intelligence

A runnable multi-tenant knowledge assistant with Next.js, FastAPI, PostgreSQL, Redis, a durable ingestion worker, LangGraph checkpoints and approval workflows. Live adapters use Pinecone, LangChain/OpenAI and S3. The default local mode uses lexical retrieval and clearly labeled source excerpts without paid services.

**Status: working local vertical slice, not the completed enterprise platform or a production-ready release.** See [verification](docs/verification-report.md) and [remaining gates](docs/production-readiness.md). The original scope is preserved in [prompt.md](prompt.md).

## Run locally

Requires Docker with Compose. Copy [.env.example](.env.example) to `.env` and replace `DB_PASSWORD` and `DEV_TOKEN` with independent random hex strings (for example, `openssl rand -hex 32`). A generated local `.env` is already present in this working copy and is ignored by Git.

```sh
docker compose up -d --build
```

Open **http://localhost:3100**. Enter organization `local` and the `DEV_TOKEN` from your local `.env`. Token is kept in browser memory only. API documentation: **http://localhost:8100/docs**. All published local ports bind to loopback.

1. In Settings, create a workspace and knowledge base.
2. In Knowledge, upload [the synthetic policy](samples/policy.txt) or your own supported file.
3. Wait until the document is `ready`.
4. In Chat, ask “How much vacation do employees receive?” and open its citation.
5. Reprocess from Knowledge, then approve/reject in Approvals.
6. Delete a source to block subsequent retrieval and source access.

Stop with `docker compose stop`. Database and original files persist in named volumes. Do not remove those volumes unless deletion is intended. No cloud resources are created by local startup.

The current local instance also runs real ClamAV. To keep scanning enabled on restart, use `docker compose -f compose.yaml -f compose.scanner.yaml up -d --build` (the VS Code startup task uses this configuration). See [live integration verification](docs/live-integrations.md) for scanner and credential-dependent provider tests. The scanner uses x86 emulation on Apple Silicon and a 2 GB memory limit.

## Implemented behavior

- Database-enforced application ownership checks for tenants, workspace memberships and conversation owners; viewer/editor/admin policies.
- OIDC RS256 bearer verification and explicit development token mode; membership administration and immediate membership revocation.
- Workspace and knowledge-base creation/listing; multi-file uploads; PDF/DOCX/TXT/Markdown/HTML parsing with size/text/archive limits.
- Persistent SQL job queue, worker leases, retry limits, deterministic chunk IDs, generation fencing and failure status.
- Live embedding/Pinecone adapters with namespaces, KB filters, SQL reauthorization and query-visibility checks; local lexical alternative.
- LangGraph retrieve/answer/abstain graph, PostgreSQL checkpoints, bounded context/output and request timeouts.
- Authenticated SSE with progress, provisional tokens, final/error events and browser cancellation.
- Conversation history, rename/delete with checkpoint erasure, authorized source previews and answer feedback.
- Durable human approval for document reprocessing, expiration checks, role revalidation and transactional side-effect receipt.
- Basic organization counts/audit activity, structured request logs, Redis request limits and health checks.

## Verification commands

```sh
docker compose run --rm -e RUN_INTEGRATION=1 api python -m pytest -q -p no:cacheprovider tests
docker compose run --rm --no-deps api ruff check --no-cache app tests
docker compose run --rm --no-deps api ruff format --check --no-cache app tests migrations
docker compose run --rm api python -m app.evaluate
cd frontend
npm ci
npm run typecheck
npx playwright install chromium
npm test
```

Integration tests create synthetic, uniquely identified tenants in the configured database. Use a disposable database for CI; do not point tests at production. The evaluation runner removes its temporary corpus. [CI](.github/workflows/ci.yml) builds containers and runs backend, browser and Terraform checks.

## Live providers and deployment

See [deployment](docs/deployment.md), [operations](docs/operations-runbook.md), [security](docs/security.md) and [architecture](docs/architecture.md). `python -m app.provision_index` explicitly provisions a potentially billable Pinecone index; it is never run automatically. Set the resulting host and matching embedding dimension before enabling live mode. Configure `CHAT_MODEL` explicitly.

Cloud Terraform is prepared for existing private networking and HTTPS target groups. The load balancer must route `/api/*` to the API and other paths to the web service; local Next.js proxies API traffic over the Compose network. Terraform defaults service desired count to zero until migrations, runtime secrets and release gates are configured. No AWS deployment was performed.

Pinned direct dependencies are in [requirements](backend/requirements.txt), the tested resolution in [Python lock](backend/requirements.lock), and [npm lock](frontend/package-lock.json). Local containers use Python 3.12 and Node 24. [Dependency evidence](docs/dependency-evidence.md) records documentation consulted.

## Design and requirements

- [Functional requirements](docs/functional-requirements.md), [non-functional requirements](docs/non-functional-requirements.md), [roadmap](docs/implementation-roadmap.md)
- [Architecture](docs/architecture.md), [domain](docs/domain-design.md), [data](docs/data-model.md), [API](docs/api-design.md), [agent workflows](docs/agent-workflows.md)
- [Testing](docs/testing-strategy.md), [evaluation](docs/ai-evaluation.md), [measured synthetic baseline](docs/evaluation-results.json)

Unfinished enterprise capabilities include browser SSO/refresh, full OS isolation and production scanner operations, full document versions/ACLs, tenant offboarding, quotas/cost accounting, richer retrieval/evaluation, notifications, telemetry dashboards, complete CI/CD promotion/rollback, performance/restore verification and production security review. These are tracked explicitly rather than represented by inert controls or simulated integrations.
