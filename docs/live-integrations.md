# Live integration verification

No external model, Pinecone, S3 or OIDC credentials were configured during this continuation. Tests requiring those services are explicitly opt-in. A configured adapter, a contract test and a successful live request are different evidence levels.

## Preflight

Set the relevant values in the ignored `.env`; never paste secrets into a report or commit them. Model/vector mode requires PROVIDER=live, OPENAI_API_KEY, CHAT_MODEL, PINECONE_API_KEY, PINECONE_HOST, PINECONE_INDEX and matching embedding settings. S3 mode requires STORAGE=s3, S3_BUCKET and AWS credentials through the standard SDK chain. S3_ENDPOINT_URL is optional for compatible test services.

```sh
docker compose run --rm --no-deps api python -m app.preflight
```

Preflight reads Pinecone index readiness/dimension/metric/host and S3 bucket access. It never calls the model, creates an index or writes an object. API readiness now includes configured external dependency checks. Error responses omit upstream exception strings and credentials. A matching dimension does not prove embedding compatibility: changing model/dimensions changes the metadata fingerprint and requires reprocessing all documents.

## Paid provider smoke test

Use an existing dedicated test index and a tightly scoped test bucket. Provisioning is never automatic. These commands incur provider usage when enabled:

```sh
docker compose run --rm --no-deps -e RUN_LIVE_TESTS=1 api python -m pytest -q tests/test_live.py -k pinecone
docker compose run --rm --no-deps -e RUN_S3_TESTS=1 api python -m pytest -q tests/test_live.py -k s3
```

The Pinecone test embeds synthetic text, creates vectors in a random smoke namespace, polls query visibility, checks another namespace returns no data, calls the model, deletes its vectors and polls deletion visibility. Cleanup runs in `finally`; inspect failed cleanup before rerunning. The S3 test puts/gets/deletes a random synthetic object and verifies 404 afterward. No customer documents are used. The dispatch-only live-integration workflow uses the protected staging environment and requires explicit selection for billable tests; it has not run on GitHub.

## Real local malware scanner

```sh
docker compose -f compose.yaml -f compose.scanner.yaml up -d --build
docker compose -f compose.yaml -f compose.scanner.yaml run --rm --no-deps -e RUN_SCANNER_TESTS=1 api python -m pytest -q tests/test_live.py -k clamav
```

This enables SCAN_MODE=clamav for API/worker, waits for scanner health, keeps signatures in a named volume and exposes no scanner host port. The tested image is x86 and uses emulation on Apple Silicon. It needs up to 2 GB of memory. Production must supply a privately reachable maintained scanner; Terraform now requires CLAMD_HOST and SCAN_MODE in the runtime secret. The scanner is not provisioned by cloud Terraform.

Worker sequence is protected source storage → scan → isolated extraction → embedding/indexing. Malware is quarantined in SQL and never parsed/indexed; the original remains in restricted storage for operator review/deletion. Scanner outage or protocol error triggers bounded job retry, never a clean result. Parsing runs in a child process with no provider secrets, Linux address-space/CPU/file-size/file-descriptor limits, and a parent wall-clock deadline. This is resource isolation, not a complete OS security sandbox; network/filesystem isolation still requires container/runtime controls.

## S3-compatible local service attempt

The optional compose.storage.yaml accepts local MinIO credentials and MINIO_IMAGE from `.env.integrations` and connects the API via S3_ENDPOINT_URL. Docker Hub rejected `minio/minio:RELEASE.2025-04-22T22-12-26Z`, and Quay returned HTTP 401 for the same release; that service has **not** been started or verified. Set MINIO_IMAGE to an accessible approved pinned image, or use an existing S3-compatible endpoint. Do not interpret the passing boto3 import or mocked contract tests as a storage round trip.

## Consistency changes

Vector records include embedding fingerprint, chunk identity and tenant/workspace metadata. Visibility probes filter the exact chunk to avoid false negatives when identical vectors tie. Queries exclude incompatible embedding generations. Obsolete ingestion and successful reprocessing enqueue generation-specific vector purges; a purge never deletes another document generation. SQL still reauthorizes results. Crash-after-write-before-cleanup scenarios need a periodic reconciliation sweep and stress validation before physical-deletion guarantees are complete.
