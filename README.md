# Codex + Blender

A reproducible, code-first workflow for using GPT-6 Astra / Codex with Blender.

> **Git-controlled configuration and Blender Python are the source of truth. MCP is an interactive inspection and experimentation layer, not the canonical scene state.**

This repository is based on research into OpenAI's published GPT-6 Astra Blender workflow, Blender's official Lab MCP server, Codex MCP/automation capabilities, and Blender's `bpy`/CLI automation model.

## Recommended architecture

OpenAI's published architectural-visualization workflow with GPT-6 Astra is primarily code-driven. Astra uses Blender's Python API (`bpy`), runs scripts through Blender's executable in background mode, reviews generated renders, and iterates. GUI interaction is supplementary rather than the durable control mechanism.

The control hierarchy used here is:

1. **Version-controlled YAML/JSON** — dimensions, assets, render settings, acceptance criteria.
2. **Version-controlled `bpy` Python** — deterministic construction and transformations.
3. **Blender CLI** — clean builds, renders, validation, CI.
4. **Blender MCP** — live inspection, screenshots, documentation, focused experiments.
5. **GPT-6 Astra vision** — qualitative visual critique.
6. **GUI/computer use** — exceptional UI-only work.

```text
Human brief
    |
    v
GPT-6 Astra / Codex
    |\
    | \---- Blender MCP ---- live inspection / experiments
    |
    +---- edits YAML + Python
                |
                v
         Blender --background
                |
               bpy
                |
        +-------+---------+
        |       |         |
     .blend   renders   scene_state.json
        \       |         /
         \------v--------/
          visual + structural QA
                 |
                 +----> revise source and rebuild
```

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── .codex/
│   └── config.toml.example
├── config/
│   ├── workflow.yaml
│   └── acceptance.yaml
├── docs/
│   ├── RESEARCH.md
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   └── ROADMAP.md
├── prompts/
│   └── visual_review.md
├── scripts/
│   ├── blender_runner.py
│   └── check_environment.py
├── blender/
│   ├── entrypoint.py
│   ├── core/
│   └── jobs/
├── tests/
├── output/
└── requirements.txt
```

## Requirements

- Blender 5.1+ when using Blender's current official Lab MCP integration.
- Python 3.11+ for host-side orchestration.
- Codex CLI or another MCP-capable client if using MCP.
- `pip install -r requirements.txt`

Set `BLENDER_BIN` if Blender is not on `PATH`.

Windows PowerShell:

```powershell
$env:BLENDER_BIN = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
```

macOS:

```bash
export BLENDER_BIN="/Applications/Blender.app/Contents/MacOS/Blender"
```

## Quick start

```bash
python scripts/check_environment.py
python scripts/blender_runner.py all
```

The workflow produces:

```text
output/
├── scene.blend
├── render.png
├── scene_state.json
├── validation.json
└── _resolved_workflow.json
```

Individual stages:

```bash
python scripts/blender_runner.py build
python scripts/blender_runner.py render
python scripts/blender_runner.py inspect
python scripts/blender_runner.py validate
```

## Optional Blender MCP

Blender's official Lab MCP architecture is:

```text
Codex / MCP client
      |
      | MCP over stdio
      v
  blender-mcp
      |
      | TCP
      v
Blender MCP add-on
      |
      v
     bpy
```

After installing the official server/add-on, register it with Codex:

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Copy `.codex/config.toml.example` to `.codex/config.toml` if project-local configuration is preferred.

## Required agent loop

For every meaningful scene change:

1. Inspect configuration and relevant builders.
2. Use MCP summaries/screenshots when a live Blender session is available.
3. Implement the durable change in YAML/Python.
4. Run `python scripts/blender_runner.py all`.
5. Inspect `output/scene_state.json` and `output/validation.json`.
6. Review the generated render(s).
7. Correct defects and repeat.
8. Finish only when a clean headless rebuild passes.

A live MCP edit is exploratory until the same result is reproduced by source-controlled configuration/code.

## Research basis

Primary references:

- OpenAI — Architectural visualization with Astra: https://developers.openai.com/blog/architectural-visualization-with-astra
- OpenAI — GPT-6 Astra: https://developers.openai.com/api/docs/models/gpt-6-astra
- OpenAI — Codex MCP: https://developers.openai.com/codex/extend/mcp
- OpenAI — Codex non-interactive mode: https://developers.openai.com/codex/non-interactive-mode
- OpenAI — Agent approvals & security: https://developers.openai.com/codex/agent-approvals-security
- Blender — MCP Server: https://www.blender.org/lab/mcp-server/
- Blender Lab MCP source mirror: https://github.com/bpype/blender_mcp
- MCP specification: https://modelcontextprotocol.io/specification/2026-07-28/

Community implementation used as secondary evidence:

- https://github.com/ahujasid/blender-mcp

See `docs/RESEARCH.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, and `docs/ROADMAP.md`.
