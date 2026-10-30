"""Frozen initial PostgreSQL schema."""

from alembic import op

revision = "001"
down_revision = None

SCHEMA = [
    "CREATE TABLE events (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\tkind VARCHAR(60) NOT NULL, \n\tresource_id VARCHAR(64) NOT NULL, \n\tcreated DOUBLE PRECISION NOT NULL, \n\tPRIMARY KEY (id)\n)",
    "CREATE INDEX ix_events_tenant_id ON events (tenant_id)",
    "CREATE TABLE tenants (\n\tid VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tPRIMARY KEY (id)\n)",
    "CREATE TABLE members (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\trole VARCHAR(20) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, subject), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)",
    "CREATE INDEX ix_members_tenant_id ON members (tenant_id)",
    "CREATE TABLE workspaces (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)",
    "CREATE INDEX ix_workspaces_tenant_id ON workspaces (tenant_id)",
    "CREATE TABLE knowledge_bases (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tworkspace_id VARCHAR(36) NOT NULL, \n\tname VARCHAR(120) NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(workspace_id) REFERENCES workspaces (id)\n)",
    "CREATE INDEX ix_knowledge_bases_workspace_id ON knowledge_bases (workspace_id)",
    "CREATE INDEX ix_knowledge_bases_tenant_id ON knowledge_bases (tenant_id)",
    "CREATE TABLE workspace_access (\n\tid VARCHAR(36) NOT NULL, \n\tworkspace_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (workspace_id, subject), \n\tFOREIGN KEY(workspace_id) REFERENCES workspaces (id)\n)",
    "CREATE INDEX ix_workspace_access_workspace_id ON workspace_access (workspace_id)",
    "CREATE TABLE conversations (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tworkspace_id VARCHAR(36) NOT NULL, \n\tkb_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\ttitle VARCHAR(120) NOT NULL, \n\tactive_until DOUBLE PRECISION NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(kb_id) REFERENCES knowledge_bases (id)\n)",
    "CREATE INDEX ix_conversations_tenant_id ON conversations (tenant_id)",
    "CREATE TABLE documents (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tworkspace_id VARCHAR(36) NOT NULL, \n\tkb_id VARCHAR(36) NOT NULL, \n\tfilename VARCHAR(240) NOT NULL, \n\tkey VARCHAR(300) NOT NULL, \n\tdigest VARCHAR(64) NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tdeleted BOOLEAN NOT NULL, \n\terror VARCHAR(200), \n\tcreated DOUBLE PRECISION NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(kb_id) REFERENCES knowledge_bases (id)\n)",
    "CREATE INDEX ix_documents_tenant_id ON documents (tenant_id)",
    "CREATE INDEX ix_documents_kb_id ON documents (kb_id)",
    "CREATE INDEX ix_documents_workspace_id ON documents (workspace_id)",
    "CREATE TABLE approvals (\n\tid VARCHAR(36) NOT NULL, \n\ttenant_id VARCHAR(36) NOT NULL, \n\tworkspace_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\tdocument_id VARCHAR(36) NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\texpires DOUBLE PRECISION NOT NULL, \n\tdecision_by VARCHAR(200), \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(document_id) REFERENCES documents (id)\n)",
    "CREATE INDEX ix_approvals_tenant_id ON approvals (tenant_id)",
    "CREATE TABLE chunks (\n\tid VARCHAR(64) NOT NULL, \n\tdocument_id VARCHAR(36) NOT NULL, \n\tversion INTEGER NOT NULL, \n\ttext TEXT NOT NULL, \n\tpage INTEGER, \n\tembedding JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(document_id) REFERENCES documents (id)\n)",
    "CREATE INDEX ix_chunks_document_id ON chunks (document_id)",
    "CREATE TABLE jobs (\n\tid VARCHAR(36) NOT NULL, \n\tdocument_id VARCHAR(36) NOT NULL, \n\tversion INTEGER NOT NULL, \n\tkind VARCHAR(20) NOT NULL, \n\tstate VARCHAR(20) NOT NULL, \n\tattempts INTEGER NOT NULL, \n\tavailable DOUBLE PRECISION NOT NULL, \n\tlease VARCHAR(36), \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(document_id) REFERENCES documents (id)\n)",
    "CREATE INDEX ix_jobs_document_id ON jobs (document_id)",
    "CREATE TABLE messages (\n\tid VARCHAR(36) NOT NULL, \n\tconversation_id VARCHAR(36) NOT NULL, \n\trole VARCHAR(20) NOT NULL, \n\ttext TEXT NOT NULL, \n\tcitations JSON NOT NULL, \n\tcreated DOUBLE PRECISION NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(conversation_id) REFERENCES conversations (id)\n)",
    "CREATE INDEX ix_messages_conversation_id ON messages (conversation_id)",
    "CREATE TABLE feedback (\n\tid VARCHAR(36) NOT NULL, \n\tmessage_id VARCHAR(36) NOT NULL, \n\tsubject VARCHAR(200) NOT NULL, \n\tscore INTEGER NOT NULL, \n\tcomment VARCHAR(1000) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (message_id, subject), \n\tFOREIGN KEY(message_id) REFERENCES messages (id)\n)",
]


def upgrade():
    for statement in SCHEMA:
        op.execute(statement)


def downgrade():
    op.drop_table("feedback")
    op.drop_table("messages")
    op.drop_table("jobs")
    op.drop_table("chunks")
    op.drop_table("approvals")
    op.drop_table("documents")
    op.drop_table("conversations")
    op.drop_table("workspace_access")
    op.drop_table("knowledge_bases")
    op.drop_table("workspaces")
    op.drop_table("members")
    op.drop_table("tenants")
    op.drop_table("events")
