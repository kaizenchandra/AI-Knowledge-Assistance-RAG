# ADR 003 — Explicit local alternatives

Accepted. Development uses a randomly generated operator token, local protected-volume storage and lexical retrieval with exact evidence excerpts. This is an integration harness, not a simulated generative model. Live mode uses LangChain OpenAI embeddings/chat and Pinecone. Non-development configuration rejects development tokens, offline providers and local storage. OIDC bearer validation exists; automated browser login/refresh/revocation requires further identity integration. Never expose development Compose ports beyond loopback.
