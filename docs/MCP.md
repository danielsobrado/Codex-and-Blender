# Blender MCP guide

## Official versus community projects

There are multiple Blender MCP projects. Keep them distinct.

### Official Blender Lab MCP

Blender's official Lab integration:

- project page: https://www.blender.org/lab/mcp-server/
- source mirror: https://github.com/bpype/blender_mcp

Architecture:

```text
MCP client
   |
   | MCP / stdio
   v
blender-mcp server process
   |
   | local TCP bridge
   v
Blender MCP extension/add-on
   |
   v
bpy / live Blender scene
```

This is the default target for this repository.

### Community implementation

A notable community project is:

https://github.com/ahujasid/blender-mcp

It has broad adoption and useful practical patterns, but it is not the Blender Foundation/Lab implementation. Configuration options and tool names from that project must not be assumed to apply to the official server.

## What MCP is good at

MCP is most valuable for interactive state that is awkward to obtain from a fresh CLI build alone:

- scene/datablock summaries;
- object detail lookup;
- dependency/missing-file checks;
- Blender API documentation lookup;
- screenshots;
- viewport navigation;
- quick live experiments;
- live render/thumbnail requests.

The official server also exposes broader execution capabilities. These are powerful but should not replace durable source authoring.

## What MCP is not

MCP is not a scene file format, a version-control system, or a guarantee of reproducibility.

A model can make many live scene edits through MCP and leave no durable explanation of how to recreate them. That is why this repository requires every accepted change to survive the CLI build path.

## Codex configuration

Basic registration:

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Project-local template:

```toml
[mcp_servers.blender]
command = "blender-mcp"
startup_timeout_sec = 20
tool_timeout_sec = 180
enabled = true
required = false
```

Codex supports per-server controls such as enable/disable behavior, timeouts and tool filtering. See:

https://developers.openai.com/codex/extend/mcp

## Tool discovery

Treat the installed MCP server's discovered schema as authoritative.

Tool names and input schemas are implementation/version details. Do not hard-code a large permanent list in agent logic without checking the server version.

The researched official tool surface includes categories for:

- object/scene summaries;
- missing external files and linked libraries;
- Python API documentation;
- screenshots/window capture;
- viewport navigation;
- thumbnail/viewport rendering;
- Blender code execution;
- Blender CLI/background execution.

## Recommended usage policy

### Normal task

```text
1. Read source.
2. Build headlessly.
3. Use MCP summaries/screenshots to diagnose.
4. Experiment live only when useful.
5. Encode the fix in source.
6. Rebuild headlessly.
7. Accept the rebuilt result.
```

### Evidence selection

If the question is exact:

- "Where is this object?" → structured state.
- "Which material is assigned?" → structured state.
- "Is a file missing?" → dependency check.
- "Does the composition feel balanced?" → render/screenshot + visual reasoning.

Do not use pixels to answer exact scene-state questions unnecessarily.

## MCP and long-running jobs

Interactive MCP is useful for live work, but batch construction/render jobs are cleaner through direct Blender CLI execution.

Use MCP as a control/inspection plane and Blender CLI as the reproducible batch execution plane.

## Security posture

The MCP bridge reaches Blender's Python runtime. Use least-privilege tool exposure and isolate Blender appropriately for autonomous/untrusted workflows.

See `docs/SECURITY.md`.

## Future project-specific MCP layer

For production automation, narrow tools can be better than broad generic execution. Candidate operations:

```text
get_scene_manifest
validate_scene
set_camera_pose
set_object_transform
set_material_parameter
render_review_views
rebuild_scene
```

These operations can validate inputs, log intent and map changes back to durable project configuration.

Do not implement this layer until repeated tasks justify it; the current official MCP + CLI workflow is intentionally simpler.
