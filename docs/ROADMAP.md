# Roadmap

Status values: `TODO`, `PARTIAL`, `DONE`, `DEFERRED`.

## P0 — reproducible core

### R1 Source-controlled scene construction — DONE

- YAML contains configurable scene values.
- `bpy` performs durable construction.
- managed collection ownership is enforced.
- factory startup is used for fully generated scenes.

### R2 Headless runner — DONE

- build/render/inspect/validate/all actions exist;
- YAML resolves to Blender-readable JSON;
- failures propagate through process exit status;
- standalone post-build actions reopen the generated `.blend`.

### R3 Structural scene manifest — DONE

- scene/object/camera/render state emitted as JSON;
- transforms and dimensions included;
- materials/mesh counts included;
- external-file status represented.

### R4 Structural quality gate — DONE

- required objects validated;
- active camera validated;
- managed collection validated;
- missing external files validated;
- machine-readable pass/fail emitted.

## P1 — visual self-correction

### V1 Multi-view render contract — PARTIAL

Done:

- multiple configured cameras;
- named camera roles;
- protected required-view policy in `acceptance.yaml`;
- automatic review renders;
- machine-readable render index.

Remaining:

- optional normal/depth/object-ID diagnostic passes;
- project-specific detail-view templates if real use cases require them.

### V2 Visual evaluator — PARTIAL

Done:

- deterministic image validity/brightness checks;
- structured GPT-6 Astra multi-view critique;
- schema-constrained JSON output;
- every model problem references evidence/views;
- required review coverage cannot be downgraded by mutable workflow config.

Remaining:

- approved-reference regression mode;
- calibrated SSIM/LPIPS-style thresholds where a project has stable golden views;
- optional semantic reference comparison where justified.

Do not add universal perceptual thresholds without calibration data.

### V3 Iteration controller — DONE

- bounded iteration budget;
- hard stop on build/structural failure;
- iteration evidence snapshots;
- best-known evaluated artifacts retained;
- source correction through a separate Codex worker;
- clean-worktree requirement by default;
- quality-gate files restored and loop stopped if a correction worker modifies them;
- gate implementation files are also protected;
- live MCP experiments cannot bypass durable source updates.

## P1 — MCP integration

### M1 Official Blender MCP installation guide/test — PARTIAL

Done:

- setup documented for the official Blender Lab server/add-on;
- project-local Codex MCP template included.

Remaining:

- live connection smoke test on a workstation;
- record actual tool discovery from the installed version;
- demonstrate a read-only scene query and screenshot against the generated `.blend`.

### M2 MCP inspection adapter — TODO

Add optional helpers only if they improve the real live workflow for:

- scene summary;
- object detail;
- missing files;
- screenshot/render capture.

The deterministic CLI path must remain independent from MCP availability.

### M3 Constrained project MCP tools — TODO

Investigate project-specific high-value operations such as camera/object/material edits, preview rendering, manifest retrieval and validation. Generic Python execution remains an escape hatch, not the default.

## P1 — testing and CI

### T1 Host unit tests — PARTIAL

Current coverage includes:

- configuration contracts;
- visual render-index/required-view behavior;
- deterministic render metrics;
- protected-file restoration;
- toolchain resolution;
- reproducibility comparator/tolerance behavior.

Remaining:

- more malformed-config/path-resolution cases;
- subprocess failure/timeout cases where useful.

### T2 Blender smoke CI — DONE

Proven in GitHub Actions with the pinned Blender toolchain:

- official Blender archive/download and SHA-256 verification;
- Blender 5.2.1 LTS launches on Ubuntu 24.04;
- clean scene builds;
- Eevee renders hero/front/side views headlessly;
- structural validation passes;
- deterministic visual evaluation passes;
- expected `.blend`, render, state and validation artifacts are produced;
- artifacts are uploaded for inspection.

The first runtime passes also found and fixed the Blender 5.2 Eevee enum change and missing Linux EGL dependency.

### T3 Reproducibility regression — DONE

- two independent clean builds;
- each build inspected and structurally validated;
- normalized `scene_state.json` manifests compared recursively;
- numeric tolerance configured in YAML;
- exact difference paths emitted on failure;
- reports/snapshots retained as artifacts;
- enforced in the real Blender smoke workflow;
- no requirement for byte-identical PNG or `.blend` output.

## P2 — production assets

### A1 Asset manifest — TODO

Track asset source, revision, expected collection/object and ownership/license metadata.

### A2 Dependency validator — TODO

Detect missing/moved images, linked libraries and expected asset IDs before expensive rendering.

### A3 Cache strategy — TODO

Add a content-addressed/local asset cache only when real production assets justify it.

## P2 — performance

### P1 Preview/final render profiles — TODO

Separate fast iterative/CI preview quality from final output explicitly in YAML. Current CI intentionally renders the normal sample profile and therefore proves the real render path, but it is slower than necessary for future complex scenes.

### P2 Incremental scene builds — TODO

Only after profiling proves full managed-collection rebuilds are too expensive. Do not sacrifice reproducibility prematurely.

## P2 — observability

### O1 Structured run report — PARTIAL

Current autonomous reports capture iterations, scores, stop reason and snapshots.

Remaining useful fields:

- per-stage durations;
- Blender/source revision in the run report;
- render settings summary;
- evaluator/model metadata;
- artifact sizes/paths.

### O2 Codex non-interactive integration — DONE

The visual evaluator and correction worker use `codex exec`; visual review uses attached images plus schema-constrained output, and the correction turn uses a separate writable sandbox.

## Next high-impact work

1. **V2** — approved-reference visual regression with calibrated project-specific metrics.
2. **M1** — real workstation smoke test of the official Blender MCP bridge and tool inventory.
3. **P1 performance** — preview/final render profiles before production scenes make CI expensive.
4. **A1/A2** — asset manifest/dependency validation when real external assets enter the workflow.
