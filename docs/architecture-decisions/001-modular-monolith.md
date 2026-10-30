# ADR 001 — Modular monolith with separate ingestion worker

Accepted for initial implementation. Keep domain policy and provider adapters in separate modules within one Python package. Run API and durable ingestion worker as separate processes/containers; avoid network boundaries for ordinary domain calls. Choose ECS Fargate over EKS because no Kubernetes operational requirement exists. Trade-off: shared schema and deployment coordination; split services only after measured scaling or organizational need.
