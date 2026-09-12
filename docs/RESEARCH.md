# Research: GPT-6 Astra / Codex + Blender

Research date: 2026-09-12.

## Executive conclusion

The strongest current evidence supports a **code-first Blender workflow rather than a GUI-first workflow**.

OpenAI's published architectural-visualization example shows GPT-6 Astra in Codex creating an editable Blender scene through `bpy`, running Blender scripts in background mode, examining generated renders, correcting visual/geometry problems and iterating. Computer use was supplementary; the durable work was programmatic.

Blender's official Lab MCP server complements that workflow with live inspection and interactive control, but MCP is not a replacement for reproducible source.

The recommended production architecture is therefore:

```text
version-controlled scene specification + bpy
        |
        v
Blender CLI clean build
        |
        +--> .blend
        +--> multi-view renders
        +--> exact scene manifest
        +--> structural validation
        |
        v
render sanity checks + GPT-6 Astra visual review
        |
        +--> pass
        |
        +--> fail -> Codex patches durable source -> rebuild

Blender MCP sits beside this loop for live inspection and experiments.
```

## 1. What OpenAI actually demonstrated with Blender

OpenAI's architectural-visualization project is the most important primary source because it describes the mechanism, not only the final images.

The demonstrated pattern included:

- Astra authoring Blender content through the Python API (`bpy`);
- architecture, furniture, vegetation, materials, lights and cameras;
- Blender's executable running scripts in background mode;
- preview renders inspected before more expensive rendering;
- visual feedback used to find and correct scene problems;
- Blender UI/computer use used as an additional inspection mechanism;
- structured Blender-to-Unreal transfer rather than a one-off viewport result.

The practical conclusion is that Astra's Blender strength comes from the combination of **spatial reasoning + coding + visual feedback + iteration**, not from superior mouse automation alone.

Primary source:
https://developers.openai.com/blog/architectural-visualization-with-astra

## 2. GPT-6 Astra evidence relevant to 3D/CAD work

OpenAI describes GPT-6 Astra as its most capable model for difficult end-to-end work and documents image input, software engineering, computer use and structured outputs among the capabilities relevant to this workflow.

Primary model source:
https://developers.openai.com/api/docs/models/gpt-6-astra

OpenAI also reports a **95.9% BenchCAD score for GPT-6 Astra versus 83.3% for GPT-5.6 Sol** in its published launch results.

That number should not be misrepresented as a Blender benchmark. BenchCAD is evidence of substantially stronger CAD/spatial reconstruction capability, which is directionally relevant to procedural Blender work.

Primary benchmark source:
https://openai.com/index/gpt-6-astra/

The capability combination that matters here is:

- long-horizon code work;
- spatial/visual reasoning;
- image critique;
- structured output;
- tool use;
- iterative correction;
- sufficient context for a large procedural scene.

## 3. Blender CLI + `bpy` is the reproducibility layer

Typical shape:

```bash
blender --background --factory-startup --python blender/entrypoint.py -- --action all --config output/_resolved_workflow.json
```

Advantages:

- deterministic/reviewable source;
- Git diffs;
- repeatable clean builds;
- batch and CI suitability;
- explicit dimensions/settings;
- machine-readable manifests;
- no dependence on viewport coordinates;
- easy reconstruction from scratch.

Limitations:

- some Blender operators depend on interactive context and are awkward headlessly;
- complex artistic decisions still benefit from viewport inspection;
- final rendering can be expensive;
- byte-identical renders should not be assumed across Blender versions, GPU backends or hardware.

The correct target is **semantic reproducibility**, not blindly demanding identical PNG bytes on every machine.

## 4. Official Blender Lab MCP

Blender's official Lab integration has two runtime components:

```text
MCP client
   |
   | stdio/MCP
   v
blender-mcp server
   |
   | local TCP bridge
   v
Blender extension/add-on
   |
   v
bpy / live Blender scene
```

The server is separate from Blender. The extension runs inside Blender and provides access to the live Blender Python environment.

The researched official implementation exposes capabilities including:

- scene/datablock summaries;
- object detail summaries;
- missing-file/linked-library inspection;
- Blender Python API documentation lookup;
- screenshots;
- viewport navigation;
- thumbnail/full viewport rendering;
- Python execution in a running Blender instance;
- CLI/background execution helpers.

The exact tool names are implementation/version details. A production integration should discover the installed tool set instead of permanently assuming a copied list.

Primary sources:

- https://www.blender.org/lab/mcp-server/
- https://github.com/bpype/blender_mcp

At the research date, Blender's Lab documentation specifies Blender 5.1+ for the integration.

## 5. Codex is now sufficient for both visual review and source correction

Current Codex CLI documentation makes the hybrid loop simpler than requiring a custom OpenAI API client.

`codex exec` supports:

- non-interactive execution;
- `--image` / `-i` to attach one or more images to the initial prompt;
- `--output-schema` to require a JSON-schema-shaped final response;
- `--output-last-message` to write the final response to a file;
- `--sandbox read-only` for inspection/evaluation;
- `--sandbox workspace-write` for repository-local corrections;
- `--ephemeral` for runs that should not persist rollout/session files;
- model override with `--model`;
- configuration overrides such as model reasoning effort;
- optional JSON event streams with `--json`.

Primary command reference:
https://learn.chatgpt.com/codex/developer-commands

OpenAI's current ChatGPT/Codex guidance states that GPT-6 Astra in Codex requires **Codex CLI 0.153.0 or newer**.

Primary availability source:
https://help.openai.com/en/articles/20001275/

This enables a clean two-agent boundary:

```text
Evaluator:
  codex exec
  + Astra
  + render images
  + read-only sandbox
  + JSON schema

Correction worker:
  codex exec
  + Astra
  + visual_evaluation.json
  + workspace-write sandbox
  + source-only instructions
```

That boundary is preferable to giving one model turn unrestricted responsibility for judging its own edits.

## 6. MCP versus CLI versus GUI/computer use

They solve different problems.

| Capability | CLI + bpy | MCP | GUI/computer use |
|---|---:|---:|---:|
| Clean deterministic rebuild | Excellent | Weak if used only as live mutation | Weak |
| Git reviewability | Excellent | Only when mirrored to source | Weak |
| Batch rendering | Excellent | Good as wrapper | Weak |
| Live scene inspection | Moderate | Excellent | Good |
| Screenshots/viewport context | Moderate | Excellent | Excellent |
| Precise scripted transforms | Excellent | Excellent | Moderate |
| Fast live experiments | Good | Excellent | Good |
| CI suitability | Excellent | Moderate | Weak |
| UI-only features | Weak | Moderate | Excellent |

Recommended priority:

**CLI/`bpy` first -> MCP second -> GUI automation third**.

The best solution is hybrid, but the layers must have clear ownership.

## 7. Why MCP should not be the source of truth

A live scene mutation can look excellent and still be operationally bad if it cannot be reproduced.

Bad loop:

```text
render problem -> live edit -> looks better -> done
```

Production loop:

```text
render problem
-> collect exact + visual evidence
-> experiment live if useful
-> identify durable change
-> patch YAML/Python
-> clean rebuild
-> rerender
-> accept the rebuilt result only
```

This prevents repository/`.blend` drift.

## 8. Visual evaluation should use multiple evidence classes

A model looking at RGB images alone should not answer questions that Blender can answer exactly.

Recommended evidence hierarchy:

1. **Blender structural assertions** — object existence, camera identity, transforms, dimensions, material links, external-file status.
2. **Deterministic image checks** — missing renders, resolution, blank/near-black/near-white output, project-specific measurable defects.
3. **Reference-image metrics** — SSIM/LPIPS-style regression only where approved references and calibrated thresholds exist.
4. **Semantic/reference checks** — where broad correspondence matters more than pixels.
5. **GPT-6 Astra visual critique** — composition, realism, style, cross-view consistency and high-level defects.
6. **Human review** — genuinely subjective final decisions.

Research references for future reference-image mode:

- SSIM: https://docs.pytorch.org/ignite/master/generated/ignite.metrics.SSIM.html
- LPIPS/deep perceptual similarity: https://arxiv.org/abs/1801.03924
- CLIP: https://arxiv.org/abs/2103.00020

No universal SSIM/LPIPS/semantic threshold should be copied into the project. Thresholds need calibration against approved/rejected renders from the target domain.

## 9. Multi-view review is essential

One attractive hero camera can hide serious geometry problems.

Useful stable roles include:

- hero/presentation view;
- front/side/rear diagnostic views;
- detail cameras for risky geometry;
- optional object-ID/depth/normal diagnostic passes.

A view contract should identify the camera, role, whether it is required and the exact rendered path. The model should be told the attachment ordering explicitly.

This repository now generates an ordered `render_index.json` on the host before visual review.

## 10. Machine-readable scene state prevents visual guessing

The agent should not infer exact facts from pixels when the Blender scene can state them directly.

A useful manifest contains:

- scene name;
- Blender version;
- active camera;
- object names/types;
- transforms;
- dimensions/bounds;
- materials;
- mesh counts;
- collection ownership;
- missing external files;
- render engine.

This repository emits `output/scene_state.json` and a separate `output/validation.json`.

The overlap with MCP is intentional: CLI validation proves a clean rebuild independently, while MCP inspects a live interactive scene.

## 11. Bounded self-correction is safer than an open-ended loop

An autonomous renderer/editor should have explicit stopping conditions.

Recommended stops:

- accepted visual/structural result;
- structural build failure;
- evaluator infrastructure failure;
- correction-worker failure;
- no durable source change;
- attempted quality-gate modification;
- iteration budget exhaustion.

The correction worker should not be allowed to make the task pass by weakening the evaluator. Quality-gate files should therefore be protected outside the worker's discretion and verified after every correction turn.

This repository implements byte-level protection/restoration for the configured quality-gate files.

## 12. Best-result retention matters

Autonomous visual iteration is not monotonic. A later change can make one view better and another worse.

Each evaluated iteration should preserve:

- renders;
- render index;
- scene state;
- validation;
- model evaluation;
- source diff/status.

The highest-scoring evaluated evidence should remain available even if the next iteration regresses.

The current controller retains per-iteration snapshots and `output/best/` evidence.

## 13. Asset handling for production scenes

Real projects need more than generated primitives.

Recommended asset policy:

- track source/provenance/license metadata;
- pin revisions for external asset packages;
- distinguish linked versus owned/generated collections;
- validate missing textures/libraries before expensive rendering;
- keep machine-specific cache paths out of canonical configuration;
- avoid letting the agent delete unrelated user collections when operating on an existing `.blend`.

The managed-collection pattern in this repository is the initial ownership boundary. A full asset manifest remains roadmap work.

## 14. Performance strategy

Do not optimize final render quality before scene correctness.

Recommended iteration strategy:

```text
cheap structural checks
-> preview render(s)
-> deterministic image sanity checks
-> Astra review
-> correction
-> only then high-quality/final rendering
```

Preview and final profiles should ultimately be separate configuration. Incremental scene rebuilds should be added only if profiling shows that clean managed-collection rebuilds are too expensive.

## 15. Community Blender MCP implementations

`ahujasid/blender-mcp` is a notable community project and useful secondary evidence for adoption, setup patterns and alternative tool design.

It must not be confused with Blender's official Lab MCP project.

Community source:
https://github.com/ahujasid/blender-mcp

The default recommendation here remains the official Blender Lab integration unless a community implementation provides a specifically required capability.

## 16. Security boundary

Blender-side Python runs with the permissions of the Blender process. Model-generated Blender Python must therefore be treated as local code execution.

Codex sandbox controls are useful, but a separately running Blender process should not automatically be assumed to inherit the same restrictions.

Practical implications:

- keep source/assets versioned or backed up;
- use managed ownership boundaries;
- prefer structured/read-only MCP tools for inspection;
- separate visual evaluation from writable correction turns;
- protect quality-gate source from the correction worker;
- avoid unrestricted execution modes when a workspace sandbox is sufficient.

See `docs/SECURITY.md`.

OpenAI security reference:
https://developers.openai.com/codex/agent-approvals-security

## 17. Reference architecture implemented by this repository

```text
requirements / brief
        |
        v
Git-controlled YAML + bpy <-------------------------+
        |                                            |
        v                                            |
Blender CLI clean build                              |
        |                                            |
        +--> scene.blend                             |
        +--> primary/review renders                  |
        +--> scene_state.json                        |
        +--> validation.json                         |
        |                                            |
        v                                            |
deterministic render checks                          |
        |                                            |
        v                                            |
Codex + GPT-6 Astra                                  |
(read-only images + JSON schema)                     |
        |                                            |
        +--> accepted                                |
        |                                            |
        +--> defects -> Codex correction worker -----+
                        (workspace-write)

Optional side channel:
Codex <-> Blender MCP <-> live Blender
for inspection, screenshots and experiments.
```

## 18. What is implemented versus still open

Implemented now:

- deterministic headless scene construction;
- multi-camera render generation;
- exact scene-state export;
- structural validation;
- deterministic image heuristics;
- Astra image review through Codex CLI;
- strict visual-evaluation JSON schema;
- bounded autonomous source-correction loop;
- protected quality gates;
- per-iteration/best evidence retention;
- host CI/unit tests.

Still open/high-value:

- real Blender smoke CI with a pinned Blender runner;
- calibrated reference-image regression mode;
- two-clean-build reproducibility test;
- live official-MCP smoke/inventory test;
- production asset manifest/dependency validator;
- richer run timing/observability.

See `docs/ROADMAP.md` for the maintained status.
