# AI evaluation plan and current scope

Offline mode returns exact source excerpts after lexical overlap. This verifies integration and source provenance, not semantic retrieval quality or natural-language synthesis. Do not compare its latency/cost to live provider targets.

Golden suite must include factual vacation policy, absent salary data, conflicting versions, same question in another tenant, malicious instructions embedded in policy, ambiguous reference and multi-document synthesis. Required source IDs and abstention labels should be human-reviewed. Initial tests cover factual extraction, missing evidence after deletion and cross-tenant access. Full labeled evaluation and calibrated groundedness are outstanding.

Live release gate: fixed provider/model/index/dataset/prompt versions; report recall@6, precision@6, MRR, citation precision and coverage, abstention accuracy, human-reviewed correctness/faithfulness, p50/p95 latency, actual provider token counts and price-versioned estimates. Evaluate simple dense search first. Add rewriting/reranking/hybrid only if paired quality gains justify latency/cost. No measured benefit is currently claimed.

Executed offline baseline: seven questions over three synthetic sources; mean recall across five answerable cases 1.0, abstention classification 7/7. Individual retrieval times ranged from 0.755 to 5.558 ms on local containers. See evaluation-results.json for exact outputs. This tiny hand-authored corpus is an integration smoke baseline, not representative AI quality or NFR performance evidence; it uses no live model, embeddings or Pinecone.
