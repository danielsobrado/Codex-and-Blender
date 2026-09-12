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

Current:

- multiple cameras can be configured;
- review cameras render automatically.

Remaining:

- support named camera roles and per-view acceptance requirements;
- generate contact sheet/index metadata;
- add optional normal/depth/object-ID diagnostic passes.

### V2 Visual evaluator — TODO

Implement a host-side evaluator that combines:

- deterministic image heuristics;
- optional SSIM/LPIPS-style regression metrics;
- semantic comparison where appropriate;
- GPT-6 Astra visual critique.

Acceptance:

- returns structured JSON;
- separates exact failures from subjective critique;
- every visual problem references evidence/view;
- no uncalibrated universal thresholds.

### V3 Iteration controller — TODO

Build:

```text
build -> validate -> render -> evaluate -> patch source -> rebuild
```

Acceptance:

- configurable iteration budget;
- hard stop on structural build failure;
- best-known artifacts retained;
- unresolved failures reported when budget is exhausted;
- live MCP experiments never bypass durable source updates.

## P1 — MCP integration

### M1 Official Blender MCP installation guide/test — TODO

Acceptance:

- documented setup for official Blender Lab server/add-on;
- connection smoke test;
- tool discovery recorded from installed version;
- read-only scene query demonstrated.

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

- configuration tests included.

Remaining:

- path-resolution tests;
- command-composition tests;
- malformed-config cases.

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

### O1 Structured run report — TODO

Capture:

- stage durations;
- Blender version;
- source revision;
- render settings;
- validation result;
- evaluator result;
- iteration number;
- generated artifact paths.

### O2 Codex non-interactive integration — TODO

Use `codex exec --json` and schema-constrained output for automated review/CI experiments.

Reference:
https://developers.openai.com/codex/non-interactive-mode
