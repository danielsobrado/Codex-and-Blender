# Research: GPT-6 Astra / Codex + Blender

Research date: 2026-09-12.

## Executive conclusion

The strongest current evidence supports a **code-first Blender workflow** rather than a GUI-first one.

OpenAI's architectural-visualization example shows GPT-6 Astra in Codex creating an editable Blender scene through `bpy`, running Blender scripts in background mode with `--python`, examining generated renders, correcting problems and iterating. Computer-use/UI interaction was used as a supplementary inspection mechanism, not as the durable representation of the work.

The production implication is:

**version-controlled scene specification + `bpy` code → Blender CLI → `.blend` + renders + manifest → structural/visual evaluation → source revision**.

MCP fits beside that loop as the live inspection/control plane.

## 1. What OpenAI actually demonstrated

OpenAI's published architectural visualization project is the most important source because it describes the mechanism, not only the result.

Observed pattern:

- Astra authored Blender content using the Python API (`bpy`).
- The scene included architecture, furniture, vegetation, materials, lights and cameras.
- Blender's executable was used in background mode with Python scripts for camera/render work.
- Preview renders were reviewed before committing to expensive final rendering.
- Visual inspection found and corrected scene/render problems.
- Computer use was also used to inspect Blender, but did not replace the programmatic workflow.
- The project extended into Blender-to-Unreal transfer, reinforcing that the scene was treated as structured data rather than a one-off viewport artifact.

This is why this repository treats code/configuration as canonical.

Primary source:
https://developers.openai.com/blog/architectural-visualization-with-astra

## 2. Why GPT-6 Astra is a good fit

OpenAI documents GPT-6 Astra as supporting the capabilities relevant to this loop, including image input, computer use and MCP/tool use. Image input is enough for render critique; Blender itself remains responsible for image generation.

Primary source:
https://developers.openai.com/api/docs/models/gpt-6-astra

The important capability combination is not merely "3D knowledge". It is:

- long-horizon coding;
- spatial/visual reasoning;
- tool use;
- image critique;
- iterative error correction;
- enough context to keep a procedural scene coherent across many edits.

## 3. Blender CLI + `bpy`

This is the reproducibility layer.

Typical pattern:

```bash
blender --background --factory-startup --python blender/entrypoint.py -- --action all --config output/_resolved_workflow.json
```

Advantages:

- deterministic, reviewable source;
- Git diffs;
- repeatable builds;
- suitable for CI and batch work;
- explicit configuration;
- easy generation of machine-readable state;
- no dependence on fragile UI coordinates.

Limitations:

- some interactive Blender context/operators can be inconvenient headlessly;
- artists may still need viewport inspection;
- final rendering can be computationally expensive;
- bit-for-bit render determinism across hardware/backends should not be assumed.

## 4. Official Blender Lab MCP

Blender's current official Lab integration has two runtime pieces:

```text
MCP client ⇄ MCP/stdio ⇄ blender-mcp ⇄ TCP ⇄ Blender add-on ⇄ bpy
```

The MCP server is separate from Blender. The add-on runs inside Blender and bridges requests to Blender's Python environment.

The official implementation exposes capabilities such as:

- scene/datablock summaries;
- object detail summaries;
- missing-file and linked-library inspection;
- Blender Python API documentation lookup;
- screenshots;
- viewport navigation;
- thumbnail/full viewport rendering;
- Python execution in a running Blender instance;
- CLI/background execution tools.

The exact tool list is versioned implementation detail and should be discovered from the installed MCP server rather than permanently assumed.

Primary sources:

- https://www.blender.org/lab/mcp-server/
- https://github.com/bpype/blender_mcp

At the time of this research, Blender's Lab page specifies Blender 5.1+ for this integration.

## 5. Codex MCP integration

Codex supports local STDIO MCP servers and project configuration. Relevant controls include server command/arguments, startup/tool timeouts, enable/disable behavior and tool allow/deny lists.

Canonical registration shape:

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Primary source:
https://developers.openai.com/codex/extend/mcp

Codex non-interactive mode is also important for automation. `codex exec` supports machine-readable event streams and structured outputs, which makes it suitable for a later CI/evaluation orchestrator.

Primary source:
https://developers.openai.com/codex/non-interactive-mode

## 6. MCP versus CLI

They solve different problems.

| Capability | CLI + bpy | MCP | GUI/computer use |
|---|---:|---:|---:|
| Clean deterministic rebuild | Excellent | Poor if used only as live mutation | Poor |
| Git reviewability | Excellent | Only if mirrored into source | Poor |
| Batch rendering | Excellent | Good as wrapper | Weak |
| Live scene inspection | Moderate | Excellent | Good |
| Screenshots/viewport context | Moderate | Excellent | Excellent |
| Fast experiment | Good | Excellent | Good |
| CI suitability | Excellent | Moderate | Weak |
| UI-only workflow | Weak | Moderate | Excellent |

Recommended priority:

**CLI/`bpy` first → MCP second → GUI automation third**.

The best production solution is hybrid, not exclusive.

## 7. Why MCP should not be the source of truth

A live scene mutation can produce an excellent result but still be operationally bad if nobody can reproduce it.

Bad loop:

```text
render problem → live edit → looks better → done
```

Production loop:

```text
render problem
→ gather structured + visual evidence
→ experiment live if useful
→ identify durable source change
→ patch YAML/Python
→ clean rebuild
→ rerender
→ accept only the rebuilt result
```

This avoids configuration drift between repository state and `.blend` state.

## 8. Visual evaluation

OpenAI's Astra example already demonstrates qualitative render critique. A production system should combine several evaluators instead of relying only on a model looking at RGB images.

Recommended hierarchy:

1. **Blender structural assertions** for exact facts.
2. **Project-specific deterministic image/geometry checks** where possible.
3. **Perceptual metrics** for regression against stable golden views.
4. **Semantic image metrics** for broad style/content correspondence.
5. **GPT-6 visual critique** for high-level multi-constraint reasoning.
6. **Human review** for final subjective decisions.

Useful research references:

- SSIM documentation: https://docs.pytorch.org/ignite/master/generated/ignite.metrics.SSIM.html
- LPIPS/deep perceptual similarity: https://arxiv.org/abs/1801.03924
- CLIP: https://arxiv.org/abs/2103.00020
- Vision Transformer: https://arxiv.org/abs/2010.11929

No universal threshold should be copied into the project. Thresholds need calibration against approved and rejected renders from the target domain.

## 9. Multi-view review

A single hero camera can hide broken geometry. The stronger loop evaluates several stable views per iteration.

Suggested roles:

- hero/presentation view;
- front/side/rear diagnostic views;
- detail views for high-risk geometry;
- optional object-ID/depth/normal passes for automated checks.

The starter scene already supports multiple configured cameras and renders review views.

## 10. Machine-readable scene state

The agent should not reopen Blender simply to answer questions such as "does object X exist?".

A useful manifest contains:

- scene name;
- active camera;
- objects and types;
- transforms;
- dimensions/bounds;
- materials;
- mesh counts;
- missing external files;
- render engine;
- managed collection identity.

The repository emits `output/scene_state.json` and a separate `output/validation.json`.

This deliberately overlaps some MCP summaries. CLI validation proves the clean build independently; MCP inspects the interactive scene.

## 11. Community Blender MCP implementations

`ahujasid/blender-mcp` is a notable community project and useful secondary evidence for real-world adoption, Codex setup patterns and safety-oriented modes.

It must not be confused with Blender's official Lab MCP project.

Community source:
https://github.com/ahujasid/blender-mcp

The default recommendation for this repository is to target the official Blender Lab integration unless a community implementation provides a specifically required capability.

## 12. Security conclusion

Blender's official MCP documentation warns that model-driven Python execution is powerful and should be isolated appropriately. The core architectural point is that the Blender process itself is an execution boundary.

Codex sandbox controls are valuable, but a separately running Blender process should not be assumed to inherit the same restrictions automatically.

See `docs/SECURITY.md`.

OpenAI security reference:
https://developers.openai.com/codex/agent-approvals-security

## 13. Reference architecture

```text
requirements / brief
        |
        v
GPT-6 Astra / Codex
        |
        +------ MCP ------> interactive Blender
        |                    | summaries/screenshots
        |                    v
        |<-------------------+
        |
        v
Git-controlled YAML + bpy
        |
        v
Blender CLI clean build
        |
        +--> scene.blend
        +--> render views
        +--> scene_state.json
        +--> validation.json
        |
        v
structural + visual evaluation
        |
        +--> pass → final render/export
        |
        +--> fail → patch source and repeat
```

This repository implements the lower half of that loop now and documents the remaining autonomous evaluation work in `docs/ROADMAP.md`.
