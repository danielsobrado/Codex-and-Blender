# Codex + Blender agent contract

## Mission

Build and modify Blender scenes through a reproducible, inspectable, source-controlled workflow.

## Non-negotiable source of truth

- `config/*.yaml` and Python under `blender/` are authoritative.
- Generated `.blend`, PNG and JSON files under `output/` are build artifacts.
- Blender MCP is an interactive inspection/debugging layer.
- A live MCP mutation is **not complete** until its durable equivalent exists in YAML/Python and survives a clean headless rebuild.

## Required completion loop

For every meaningful scene change:

1. Read the relevant YAML and Python first.
2. Inspect the live scene with structured MCP tools/screenshots when available.
3. Make the smallest durable source change.
4. Run `python scripts/blender_runner.py all`.
5. Read `output/scene_state.json` and `output/validation.json`.
6. Inspect generated render evidence.
7. Fix structural or visual defects.
8. Repeat until acceptance passes or a real blocker is documented.

Never claim completion solely because an interactive Blender viewport looks correct.

## Evidence hierarchy

Use the cheapest reliable evidence source:

1. Exact Blender state for transforms, names, materials, cameras, object counts and file references.
2. Deterministic image/geometry checks when they answer the question.
3. Model visual reasoning for composition, realism, style and qualitative defects.
4. Human review for genuinely subjective or ambiguous final decisions.

Do not infer exact dimensions or topology from pixels when Blender state can answer directly.

## MCP policy

Prefer structured, read-oriented MCP tools first:

- scene/datablock summaries;
- object details;
- missing-file checks;
- screenshots;
- viewport navigation;
- Blender API documentation.

Use broad Python execution only when structured tools are insufficient and the environment is explicitly suitable for it.

If an MCP experiment improves the scene, immediately encode the successful change in repository source and prove it with a clean rebuild.

## Scene ownership

Generated content belongs under `scene.managed_collection` from `config/workflow.yaml`.

Do not delete or rewrite unrelated user collections/objects when a source `.blend` is configured.

Project-specific builders must preserve this ownership boundary.

## Reproducibility

- Prefer factory startup for generated scenes.
- Keep configurable values in YAML.
- Seed procedural randomness explicitly before using it.
- Pin external asset revisions where practical.
- Keep generated outputs out of source asset directories.
- Treat manifests/validation JSON as machine-readable evidence.
- Do not depend on a developer's saved Blender startup state.

## Rendering

Use preview-quality settings while geometry, camera, material and lighting decisions are still changing.

Do not spend final-render cost before structural checks pass.

When multiple views are configured, assess all relevant views rather than optimizing one attractive camera while breaking others.

## Failure handling

- Fail loudly on invalid/missing configuration.
- Preserve the original exception context where useful.
- Log actionable stage information.
- Do not silently substitute a different renderer, asset or camera when a configured dependency is missing.
- If an acceptance rule cannot currently be evaluated, report it explicitly instead of inventing a pass.

## Implementation principles

- KISS and YAGNI.
- Small files with one responsibility.
- Configuration in YAML; avoid task constants hidden in Python.
- Minimal comments: explain durable design intent, not the history of a revision.
- Keep host orchestration independent from Blender's bundled Python where possible.

## Security boundary

Blender-side Python executes with the permissions of the Blender process. Follow `docs/SECURITY.md` and do not assume the Codex shell sandbox automatically constrains a separately running Blender instance.

## Before finishing

Confirm all applicable items:

- [ ] Source represents the intended scene.
- [ ] `python scripts/blender_runner.py all` succeeds.
- [ ] `output/validation.json` reports `passed: true`.
- [ ] Required render evidence exists.
- [ ] No important live-only MCP changes remain.
- [ ] No unrelated scene/source content was destroyed.
