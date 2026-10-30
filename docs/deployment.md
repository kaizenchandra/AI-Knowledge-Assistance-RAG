# Deployment

Local: copy `.env.example` to `.env`, replace DB_PASSWORD and DEV_TOKEN with independent random hex strings, then `docker compose up -d --build`. Open http://localhost:3100; authenticate with organization `local` and configured token. API docs at http://localhost:8100/docs. Named volumes persist database and originals. Stop with `docker compose stop`; do not remove volumes unless data loss is intended.

Live provider mode: set PROVIDER=live, OPENAI_API_KEY, CHAT_MODEL, PINECONE_API_KEY, PINECONE_HOST and matching embedding settings. Provision Pinecone with the provided command, inspect dimension/metric, and run a live upload/query/delete test in a dedicated test namespace. No credentials are included. Offline mode is the default and clearly labeled.

Cloud preparation: Terraform uses an existing VPC/private subnets, HTTPS load balancer target groups, Secrets Manager runtime configuration and immutable API/web image references. It provisions encrypted RDS, Redis, source bucket, ECS services/logging/roles. Network, certificates, ECR images and secrets are deployment prerequisites rather than silently created public resources. Apply only to an authorized account after plan review and cost review. Runtime production gates remain open; do not deploy production based on local tests.

Release order: build and scan immutable images → review Terraform plan → apply infrastructure → run Alembic migration/bootstrap as one ECS task → roll worker/API/web services → readiness check → authenticated browser smoke → observe alerts. Roll back images to previous digests if smoke fails; schema rollback requires a reviewed compatible migration/restore plan. Current CD assets do not automate all these gates.
