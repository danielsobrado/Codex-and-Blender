# Codex + Blender

A reproducible, code-first workflow for using GPT-6 Astra / Codex with Blender.

> **Git-controlled configuration and Blender Python are the source of truth. MCP is an interactive inspection and experimentation layer, not the canonical scene state.**

This repository is based on research into OpenAI's published GPT-6 Astra Blender workflow, Blender's official Lab MCP server, Codex automation capabilities, and Blender's `bpy`/CLI automation model.

## Architecture

The durable control hierarchy is:

1. **Version-controlled YAML/JSON** — dimensions, assets, cameras, render settings and acceptance policy.
2. **Version-controlled `bpy` Python** — deterministic construction and transformations.
3. **Blender CLI** — clean builds, renders, inspection and structural validation.
4. **Codex + GPT-6 Astra** — multi-view visual evaluation and bounded source correction.
5. **Blender MCP** — live inspection, screenshots, documentation and focused experiments.
6. **GUI/computer use** — exceptional UI-only work.

```text
Human brief
    |
    v
GPT-6 Astra / Codex
    |\
    | \---- Blender MCP -------- live inspection / experiments
    |
    +---- YAML + Python -------- durable source
                |
                v
         Blender --background
                |
               bpy
                |
       .blend + renders + state
                |
                v
     structural + image checks
                |
                v
      Astra multi-view review
                |
        pass ---+--- fail
                     |
                     v
               Codex correction
                     |
                     +----> rebuild from source
```

The correction controller never treats a live Blender/MCP mutation as completion. A successful correction must exist in repository source and survive the next clean Blender build.

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── .codex/
│   └── config.toml.example
├── config/
│   ├── workflow.yaml
│   ├── acceptance.yaml
│   ├── evaluator.yaml
│   └── autonomy.yaml
├── schemas/
│   └── visual_evaluation.schema.json
├── docs/
│   ├── RESEARCH.md
│   ├── ARCHITECTURE.md
│   ├── AUTONOMOUS_LOOP.md
│   ├── MCP.md
│   ├── SECURITY.md
│   ├── SETUP.md
│   └── ROADMAP.md
├── prompts/
│   └── visual_review.md
├── scripts/
│   ├── blender_runner.py
│   ├── visual_evaluator.py
│   ├── iteration_controller.py
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

- Blender installed and available through `BLENDER_BIN` or `PATH`.
- Python 3.11+ for host-side orchestration.
- Codex CLI 0.153.0+ for GPT-6 Astra in Codex.
- An account/workspace with GPT-6 Astra available in Codex.
- `pip install -r requirements.txt`

The visual evaluator uses the authenticated Codex CLI directly; it does not require a separate OpenAI SDK integration.

Set `BLENDER_BIN` when Blender is not on `PATH`.

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
pip install -r requirements.txt
python scripts/check_environment.py
python scripts/blender_runner.py all
```

The deterministic Blender stage produces the scene, primary/review renders, exact scene state, and structural validation.

Run the visual evaluator separately:

```bash
python scripts/visual_evaluator.py
```

For deterministic image checks without an Astra call:

```bash
python scripts/visual_evaluator.py --skip-model
```

## Autonomous self-correction

Start from a clean Git working tree, then run:

```bash
python scripts/iteration_controller.py
```

The bounded controller performs:

```text
build -> structural validation -> multi-view renders
      -> deterministic image checks -> Astra review
      -> source correction -> rebuild
```

The maximum iteration count comes from `config/acceptance.yaml`. Runtime autonomy policy, including protected quality-gate files and snapshot behavior, is in `config/autonomy.yaml`.

Important behavior:

- visual review runs through Codex in a read-only sandbox;
- correction runs separately in a workspace-write sandbox;
- protected quality-gate files are hashed before correction;
- if a correction worker changes a protected file, the controller restores it and stops;
- generated `output/` files are never accepted as durable fixes;
- each evaluated iteration is snapshotted;
- the best-scoring evidence is retained under `output/best/`;
- structural/build failure stops the loop immediately;
- an unchanged source tree stops the loop instead of retrying indefinitely.

Outputs include:

```text
output/
├── scene.blend
├── render.png
├── renders/
├── render_index.json
├── scene_state.json
├── validation.json
├── visual_evaluation.json
├── run_report.json
├── iterations/
└── best/
```

## Individual Blender stages

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

Copy `.codex/config.toml.example` to `.codex/config.toml` if project-local configuration is preferred. MCP remains optional: deterministic CLI construction and autonomous render evaluation do not depend on a live MCP connection.

## Agent rules

`AGENTS.md` defines the operating contract. In normal work, a scene change is complete only after a clean rebuild and validation. During a nested autonomous correction-worker turn, the parent controller owns rebuild/render/evaluation, so the worker only makes the smallest justified durable source change and returns control.

## Research basis

Primary references:

- OpenAI — Architectural visualization with Astra: https://developers.openai.com/blog/architectural-visualization-with-astra
- OpenAI — GPT-6 Astra: https://developers.openai.com/api/docs/models/gpt-6-astra
- OpenAI — Codex commands/non-interactive execution: https://learn.chatgpt.com/codex/developer-commands
- OpenAI — Codex MCP: https://developers.openai.com/codex/extend/mcp
- Blender — MCP Server: https://www.blender.org/lab/mcp-server/
- Blender Lab MCP source mirror: https://github.com/bpype/blender_mcp
- MCP specification: https://modelcontextprotocol.io/specification/2026-07-28/

Community implementation used as secondary evidence:

- https://github.com/ahujasid/blender-mcp

See `docs/RESEARCH.md`, `docs/ARCHITECTURE.md`, `docs/AUTONOMOUS_LOOP.md`, `docs/SECURITY.md`, `docs/SETUP.md`, `docs/MCP.md`, and `docs/ROADMAP.md`.
