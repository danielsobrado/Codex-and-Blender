# Roadmap

Status values: `TODO`, `PARTIAL`, `DONE`, `DEFERRED`.

## P0 — reproducible core

### R1 Source-controlled scene construction — DONE

Acceptance:

- YAML contains configurable scene values.
- `bpy` code performs durable construction.
- managed collection ownership is enforced.
- clean factory startup is used for fully generated scenes.

### R2 Headless runner — DONE

Acceptance:

- build/render/inspect/validate/all actions exist;
- host YAML resolves to Blender-readable JSON;
- errors propagate through process exit status;
- standalone post-build actions reopen the generated `.blend`.

### R3 Structural scene manifest — DONE

Acceptance:

- scene/object/camera/render state emitted as JSON;
- transforms and object dimensions are present;
- external-file status is represented.

### R4 Structural quality gate — DONE

Acceptance:

- required objects validated;
- active camera validated;
- managed collection validated;
- missing external files validated;
- machine-readable pass/fail emitted.

## P1 — visual self-correction

### V1 Multi-view render contract — PARTIAL

Implemented:

- multiple cameras can be configured;
- cameras have named roles and required/optional semantics;
- review cameras render automatically;
- host evaluator emits `render_index.json` with ordered view metadata.

Remaining:

- optional contact-sheet generation;
- optional normal/depth/object-ID diagnostic passes.

### V2 Visual evaluator — PARTIAL

Implemented:

- required-view existence checks;
- image dimensions, luminance spread, dark-frame and bright-frame heuristics;
- GPT-6 Astra review through Codex CLI image inputs;
- read-only evaluator sandbox;
- strict JSON-schema output;
- view-specific evidence, severity and confidence;
- deterministic failures kept separate from model critique;
- project-configured thresholds rather than hidden constants.

Remaining:

- optional reference-image regression mode;
- calibrated SSIM/LPIPS-style metrics where a project has approved references;
- optional semantic/reference comparison beyond the current Astra qualitative review.

### V3 Iteration controller — DONE

Implemented loop:

```text
build -> validate -> render -> deterministic review -> Astra review
      -> patch durable source -> rebuild
```

Acceptance met:

- iteration budget comes from `config/acceptance.yaml`;
- structural/build failure stops immediately;
- evaluator infrastructure failure stops immediately;
- every evaluated iteration is snapshotted;
- best-scoring evidence is retained;
- unresolved failures are reported when the budget is exhausted;
- no-change detection prevents pointless retries;
- quality-gate files are protected and restored if a correction worker modifies them;
- correction workers cannot treat generated output as the durable fix;
- MCP remains optional and cannot bypass source-controlled reconstruction.

## P1 — MCP integration

### M1 Official Blender MCP installation guide/test — PARTIAL

Implemented:

- documented official Blender Lab server/add-on architecture;
- documented Codex MCP registration;
- environment check detects the optional `blender-mcp` command.

Remaining:

- automated connection smoke test;
- record installed-version tool discovery;
- demonstrate/read-test a live scene query.

### M2 MCP inspection adapter — TODO

Add optional host helpers for:

- scene summary;
- object detail;
- missing files;
- screenshot/render capture.

Keep the deterministic CLI workflow independent from MCP availability.

### M3 Constrained project MCP tools — TODO

Investigate a project-specific layer for safe/high-value operations:

- set camera pose;
- set object transform;
- set material parameter;
- trigger preview render;
- get scene manifest;
- validate scene.

Generic code execution remains an escape hatch, not the default.

## P1 — testing and CI

### T1 Host unit tests — PARTIAL

Current:

- configuration tests;
- render-index and deterministic visual-evaluator tests;
- autonomous quality-gate restoration tests;
- Python compilation in CI.

Remaining:

- path-resolution edge cases;
- Blender command-composition tests;
- malformed-config cases;
- correction-worker subprocess tests with a fake executable.

### T2 Blender smoke CI — TODO

Acceptance:

- pinned Blender version available on runner;
- clean scene builds;
- `.blend`, render, state and validation artifacts produced;
- validation passes;
- artifacts uploaded for inspection.

### T3 Reproducibility regression — TODO

Run two clean builds and compare normalized manifests with numeric tolerances.

Do not require byte-identical PNG files across different render hardware.

## P2 — production assets

### A1 Asset manifest — TODO

Track asset source, revision, expected collection/object and ownership/license metadata.

### A2 Dependency validator — TODO

Detect missing/moved images, linked libraries and expected asset IDs before expensive rendering.

### A3 Cache strategy — TODO

Add a content-addressed/local asset cache without making source configuration machine-specific.

## P2 — performance

### P1 Preview/final render profiles — TODO

Separate preview quality from final output explicitly in YAML.

### P2 Incremental scene builds — TODO

Only after profiling proves full managed-collection rebuilds are too expensive.

Do not sacrifice reproducibility prematurely.

## P2 — agent observability

### O1 Structured run report — PARTIAL

Implemented:

- source revision;
- iteration number;
- stop reason;
- evaluator score;
- snapshot paths;
- best score.

Remaining:

- stage durations;
- Blender version in the top-level run report;
- normalized render settings;
- final validation/evaluator summaries in the top-level report.

### O2 Codex non-interactive integration — PARTIAL

Implemented:

- `codex exec` for read-only visual evaluation;
- image attachment through Codex CLI;
- JSON-schema constrained evaluator output;
- separate workspace-write correction worker;
- ephemeral Codex sessions for loop turns.

Remaining:

- optional `--json` event capture for detailed CI/observability traces.

## Next high-impact work

1. T2 — real Blender smoke CI on a pinned Blender runner.
2. V2 — approved-reference regression mode rather than universal similarity thresholds.
3. T3 — reproducibility regression across two clean scene builds.
4. M1 — live official-MCP smoke test and installed-tool inventory.
