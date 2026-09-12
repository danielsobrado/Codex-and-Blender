# Autonomous visual correction loop

The target loop separates visual review from durable source edits.

1. Blender builds, renders, inspects, and validates the scene from repository source.
2. GPT-6 Astra reviews the actual render views and returns schema-constrained JSON.
3. Codex applies the smallest durable source change.
4. Blender rebuilds from source and produces new evidence.
5. The process stops on acceptance, structural failure, evaluator failure, no source change, or the configured iteration budget.

The repository remains the source of truth. Interactive MCP edits are exploratory until represented in YAML or Blender Python and reproduced by a clean build.

Each iteration should retain render evidence, scene state, validation, visual evaluation, and the source diff that produced it. The best-scoring evaluated artifacts should remain available even if a later iteration regresses.
