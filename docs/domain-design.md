# Domain design

Identity context: Tenant and Member (unique tenant/subject). Member role is viewer, editor or admin; workspace access is explicit for non-admins. Knowledge context: Workspace → KnowledgeBase → Document → Chunk. Ingestion Job holds attempt, availability, lease and generation. Document lifecycle is independent of job delivery and vector visibility.

Conversation belongs to exactly one actor, tenant, workspace and KB. Messages carry citations that point to immutable chunk/version identities. Approval belongs to a tenant/workspace/document and stores a fixed reprocess operation, requester, expiration and authorized decision. Audit Event records actor, action, resource ID and time without raw prompt/document content.

Application policy is in security/retrieval/worker/graphs; adapter concerns are in adapters/config/db. This initial modular structure is intentionally small. Controllers still perform some transaction orchestration; additional use-case extraction is appropriate as scope grows. Do not claim complete domain isolation from framework types.
