# API contracts

Interactive OpenAPI: `/docs`; schema: `/openapi.json`. Base `/api/v1`. Headers: `Authorization: Bearer <access token>`, `X-Tenant-ID: <organization id>`. Tenant header selects an existing membership; it never grants it. Missing/invalid identity →401, absent role/membership →403, inaccessible resource →404, conflicting run/approval →409, oversized file →413, unsupported format →415, rate limit →429, unavailable limiter →503.

| Route | Methods | Behavior |
|---|---|---|
| /session | GET | verified actor, mode |
| /workspaces | GET, POST | scoped listing; admin creation |
| /knowledge-bases | GET, POST | workspace-scoped list and editor creation |
| /documents?kb_id= | GET, POST multipart | list and durable upload; 202 accepted |
| /documents/{id} | DELETE | immediate tombstone, asynchronous purge |
| /citations/{chunk_id} | GET | reauthorized current source excerpt |
| /conversations | GET, POST | owner-scoped history list/create |
| /conversations/{id}/messages | GET, POST | history and authenticated SSE question |
| /approvals | GET, POST | workspace queue and reprocessing request |
| /approvals/{id}/decision | POST | admin approve/reject and graph resume |
| /feedback | POST | owner-scoped upsert of answer feedback |
| /analytics | GET | tenant-admin status counts and audit activity |

SSE POST returns `data: <JSON>\n\n`, types stage, token, final, error. Final replaces provisional tokens and includes persisted message ID, citations and run ID. Error is terminal; no silent replay. Client AbortController cancels the transport. Expired run lease prevents indefinite conversation lock after API crash. Lists currently cap at 100 without cursor pagination; this is an explicit limitation for larger tenants.
