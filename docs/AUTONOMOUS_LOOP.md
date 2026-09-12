# Autonomous visual correction loop

The autonomous loop separates visual judgment from durable source editing. The repository remains the source of truth throughout the run.

## Pipeline

```text
source YAML/Python
      |
      v
Blender headless build
      |
      +--> structural validation ---- fail --> stop
      |
      v
primary + review renders
      |
      v
deterministic image checks
      |
      +--> exact image failure
      |
      v
GPT-6 Astra visual review
      |
      +--> pass --------------------------> finish
      |
      v
Codex correction worker
      |
      v
durable source change
      |
      +-------------------------------> rebuild
```

Run it with:

```bash
python scripts/iteration_controller.py
```

Use `--max-iterations N` to temporarily lower the configured budget. `--allow-dirty` exists for deliberate advanced use, but a clean working tree is the normal and safer starting point.

## Visual evaluator

`scripts/visual_evaluator.py` builds `output/render_index.json` from the configured camera contract and evaluates every required render.

The deterministic layer checks:

- required-view existence;
- width and height;
- luminance standard deviation;
- near-black pixel fraction;
- near-white pixel fraction.

Thresholds live in `config/evaluator.yaml`.

When deterministic checks are usable, Codex is launched in a read-only sandbox with the render images attached. GPT-6 Astra receives:

- the ordered camera/view list;
- the actual render images;
- access to `scene_state.json` for exact scene facts;
- access to `validation.json` for structural status;
- `prompts/visual_review.md` as the review contract;
- `schemas/visual_evaluation.schema.json` as the required final response shape.

The evaluator therefore keeps exact machine evidence separate from qualitative model judgment.

For image checks without an Astra call:

```bash
python scripts/visual_evaluator.py --skip-model
```

## Correction worker

If evaluation fails and budget remains, the controller launches a separate Codex turn with a workspace-write sandbox.

That worker receives the current visual evaluation and repository instructions. It is told to make the smallest justified durable source change and return control. It must not:

- edit generated `output/` artifacts as the fix;
- recursively invoke the controller;
- commit or push;
- modify protected quality-gate files.

The parent controller performs the next Blender build and decides whether the change improved the result.

## Protected quality gates

`config/autonomy.yaml` owns the protected-file list.

Before each correction turn, the controller hashes and snapshots those files. After Codex returns, the controller checks them again. If any protected file changed, it restores the original bytes and stops with `protected_quality_gate_modified`.

This prevents the loop from succeeding by weakening its evaluator, acceptance rules, schema, or review prompt.

## Stop conditions

The loop is deliberately bounded. It stops on:

- `accepted` — evaluation passed;
- `build_or_structural_validation_failed` — the scene no longer builds or violates structural requirements;
- `visual_evaluator_failed` — the evaluator infrastructure could not produce a trustworthy result;
- `correction_worker_failed` — Codex could not complete the correction turn;
- `protected_quality_gate_modified` — a worker attempted to change protected evaluation policy;
- `no_source_change` — the worker found no justified durable fix or made no source change;
- `iteration_budget_exhausted` — the configured maximum was reached.

The process never retries indefinitely.

## Evidence retention

Every evaluated iteration is copied under:

```text
output/iterations/001/
output/iterations/002/
...
```

Snapshots include available render evidence, scene state, structural validation, visual evaluation, Git source diff and working-tree status.

`output/best/` tracks the highest-scoring evaluated evidence seen during the run. A later regression therefore does not destroy the best visual evidence already produced.

`output/run_report.json` records the run-level stop reason, source revision, iteration outcomes and best score.

## MCP relationship

Blender MCP is not required for this loop. MCP remains useful for live scene inspection, viewport navigation, screenshots and experiments, but an MCP-only mutation is not a completed correction.

Any useful live experiment must still be represented in durable source and survive the same headless build/evaluation path.

## Current limitations

The evaluator currently performs absolute render sanity checks plus Astra qualitative review. Reference-image regression metrics such as calibrated SSIM/LPIPS-style comparisons are intentionally not enabled until a project has approved reference renders and meaningful thresholds.

The GitHub-hosted CI currently tests host Python/configuration only. Real Blender smoke CI still requires a runner with a pinned Blender installation.
