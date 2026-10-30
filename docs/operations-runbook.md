# Operations runbook

Health: `/health/live` checks process; `/health/ready` checks PostgreSQL and Redis. Live provider health/dimension checks are not included yet. Inspect `docker compose ps` and `docker compose logs --tail=100 api worker migrate`. Logs expose safe IDs and exception classes, not raw provider exception payloads.

Ingestion: queued/processing status should progress to ready. Failed rows retain jobs and safe errors. Reprocess through the approval center; an administrator approves a new generation. Do not manually mark a document ready. Expired processing leases can retry after ten minutes; four attempts end in failed. Investigate parser/provider/storage root cause before retrying.

Approval recovery: retry the same authorized decision after a transport/process failure. Terminal decisions return conflict, and receipt prevents duplicate effects. For failures before the initial graph interrupt persists, operator recovery is currently required; no automatic sweeper is claimed.

Deletion: tombstone blocks future retrieval/citation immediately. Worker removes source/vectors/chunks later. Reconcile late upserts and orphan storage before claiming physical deletion. Backups/checkpoints require an explicit retention schedule.

Backup: use managed RDS snapshots/PITR and encrypted object backups. Restore into isolated staging; run migrations, tenant-isolation checks, upload/query/citation and approval resume. Record measured RPO/RTO. No restore drill has yet been executed. Checkpoint tables contain sensitive data and belong in backup/retention design.

Incident: restrict tenant/provider access, preserve audit IDs, rotate compromised secrets, inspect scoped activity, restore affected data only with authorization, and run regression tests before reopening. Do not place document content or tokens in incident logs.
