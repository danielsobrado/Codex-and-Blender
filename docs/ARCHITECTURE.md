# Reference architecture

## Design goals

The system must be:

- reproducible from source;
- inspectable by humans and agents;
- safe to iterate without destroying unrelated scene content;
- usable headlessly;
- compatible with interactive MCP inspection;
- testable with structural evidence;
- extensible to visual self-correction.

## Components

### 1. Source specification

`config/workflow.yaml` contains scene and execution configuration.

It should own values that vary by project/task:

- Blender executable/startup source;
- output paths;
- managed collection;
- objects and transforms;
- cameras;
- lights;
- render settings.

`config/acceptance.yaml` contains quality requirements independently from construction.

### 2. Host runner

`scripts/blender_runner.py`:

- loads YAML outside Blender;
- resolves repository-relative paths;
- embeds acceptance configuration into the resolved JSON;
- invokes Blender;
- returns a non-zero exit code on failure.

This keeps third-party host dependencies out of Blender's bundled Python environment.

### 3. Blender entry point

`blender/entrypoint.py` is the Blender-side dispatcher.

Actions:

- `build` — create/update the managed scene content and save `.blend`;
- `render` — render primary and review cameras;
- `inspect` — emit structural scene state;
- `validate` — evaluate acceptance rules;
- `all` — run the complete durable pipeline in one Blender process.

### 4. Scene ownership

A project builder owns one configured collection.

When starting from an existing `.blend`, rebuilding replaces only that collection. This is safer than clearing all `bpy.data.objects` and allows generated content to coexist with artist-authored material.

If the project is fully generated, Blender starts from factory startup for a clean environment.

### 5. Build artifacts

Canonical generated artifacts:

```text
output/scene.blend
output/render.png
output/renders/*.png
output/scene_state.json
output/validation.json
output/_resolved_workflow.json
```

Artifacts are not authoritative source.

## Execution flow

```text
workflow.yaml + acceptance.yaml
          |
          v
  host runner resolves paths
          |
          v
_resolved_workflow.json
          |
          v
 Blender background process
          |
          +--> build managed collection
          +--> save .blend
          +--> render configured cameras
          +--> inspect scene
          +--> validate acceptance
          |
          v
      exit status
```

## Standalone actions

`build` uses the configured startup file when present; otherwise it uses factory startup.

`render`, `inspect` and `validate` automatically open the generated `.blend` when it exists. This makes individual post-build stages useful without forcing a full reconstruction every time.

`all` remains the final reproducibility gate.

## Camera model

Cameras are configured as a list. Exactly one should normally have `primary: true`.

The primary camera renders to `paths.render_file`. Optional review cameras render under `paths.render_dir`.

This supports future multi-view visual evaluation without hiding diagnostic views inside agent logic.

## Validation model

Structural validation is a hard gate.

Current rules include:

- required objects exist;
- active camera exists when required;
- managed collection exists when required;
- missing external files do not exceed the configured limit.

Visual thresholds exist in configuration but are deliberately disabled until calibrated.

The validation file is explicit about pass/fail and errors. A future evaluator should add separate visual results rather than mixing subjective model critique into exact Blender checks.

## MCP role

MCP should answer interactive questions such as:

- what objects/datablocks are in the current scene?
- what is the exact transform/material state of this object?
- are external files missing?
- what does the viewport currently show?
- can I quickly test this camera/material adjustment?

Durable authoring still flows back into source.

## Future evaluator layer

Target loop:

```text
build
  |
  v
structural validation ---- fail ---> source fix
  |
 pass
  v
preview multi-view renders
  |
  +--> deterministic metrics
  +--> semantic/perceptual metrics
  +--> GPT-6 visual critique
  |
  v
acceptance decision
  |
  +--> pass -> final render/export
  +--> fail -> structured patch plan -> source fix -> rebuild
```

The evaluator should have an iteration budget and must surface unresolved failures rather than looping indefinitely.

## Asset architecture

For larger projects add an explicit asset manifest rather than scattering paths through scripts.

Recommended fields:

```yaml
assets:
  - id: sofa_main
    source: assets/furniture/sofa.blend
    revision: null
    collection: Sofa
    license: project-owned
```

A later validator should verify:

- file presence;
- expected library/collection names;
- optional content hashes/revisions;
- license metadata when required.

## Determinism

"Deterministic" means the scene graph is derived from controlled inputs. It does not promise byte-identical raster output across all Blender builds, GPUs and render backends.

For procedural projects:

- put seeds in configuration;
- pin Blender major/minor versions for CI;
- pin external assets;
- compare normalized structural manifests;
- use calibrated perceptual tolerances for renders rather than raw file hashes.
