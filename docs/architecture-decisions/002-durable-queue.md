# ADR 002 — PostgreSQL jobs for the initial durable queue

Accepted deviation from default SQS. Upload metadata and job creation commit in one SQL transaction; worker claims rows with FOR UPDATE SKIP LOCKED, a ten-minute lease, generation fencing and four attempts. This avoids an unimplemented transactional dual-write. PostgreSQL is already mandatory and supports the initial low-volume target. SQS integration remains a production scaling extension: outbox dispatcher publishes job IDs; workers still claim SQL jobs idempotently. No claim of SQS deployment or throughput certification.

Trade-offs: polling load, no heartbeat during long provider calls, finite lease and no queue-native DLQ. Failed SQL job rows act as the inspectable dead-letter set. Operator must test lease expiry and job reconciliation under target load before production.
