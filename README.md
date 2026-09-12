# Codex + Blender

A reproducible, code-first workflow for using GPT-6 Astra / Codex with Blender.

> **Git-controlled configuration and Blender Python are the source of truth. MCP is an interactive inspection layer, not the canonical scene state.**

The repository implements the workflow described by OpenAI's published GPT-6 Astra Blender example: programmatic `bpy` scene work, headless Blender execution, render inspection, structured validation, and iterative correction.

## Architecture

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
                     +----> clean rebuild
```

The control hierarchy is:

1. **YAML/JSON** — dimensions, assets, cameras, render settings, acceptance policy.
2. **`bpy` Python** — deterministic construction and scene transformations.
3. **Blender CLI** — clean builds, renders, inspection and structural validation.
4. **Codex + GPT-6 Astra** — structured multi-view visual review and bounded source correction.
5. **Blender MCP** — live summaries, screenshots, navigation and experiments.
6. **GUI/computer use** — exceptional UI-only work.

## What is proven today

The repository has a real GitHub Actions Blender smoke pipeline, not only Python/config tests.

`config/toolchain.yaml` pins **Blender 5.2.1 LTS**. CI downloads the official Blender archive, verifies the official SHA-256 checksum, launches Blender on Ubuntu 24.04, builds the scene from factory startup, renders the hero/front/side views with Eevee, validates exact scene state, runs deterministic image checks, and uploads the generated `.blend`, PNG and JSON evidence.

The CI work exposed and fixed two real runtime issues:

- Blender 5.2 uses the `BLENDER_EEVEE` engine identifier rather than the older `BLENDER_EEVEE_NEXT` value.
- Ubuntu headless Eevee needs the EGL/OpenGL runtime libraries used by the official Blender binary.

CI also runs a **two-clean-build reproducibility regression**. It compares normalized machine-readable scene manifests with the tolerance in `config/reproducibility.yaml`; it deliberately does not require byte-identical `.blend` files or PNGs.

The authenticated GPT-6 Astra correction loop and a live Blender MCP bridge are implemented/documented but are not exercised in public GitHub CI because they require an authenticated Codex session and, for MCP, a running Blender bridge.

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── .codex/
│   └── config.toml.example
├── .github/workflows/
│   ├── host-tests.yml
│   └── blender-smoke.yml
├── config/
│   ├── workflow.yaml
│   ├── acceptance.yaml
│   ├── evaluator.yaml
│   ├── autonomy.yaml
│   ├── reproducibility.yaml
│   └── toolchain.yaml
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
│   ├── reproducibility_check.py
│   ├── toolchain_env.py
│   └── check_environment.py
├── blender/
│   ├── entrypoint.py
│   ├── core/
│   └── jobs/
├── tests/
└── output/
```

## Requirements

- Blender available through `BLENDER_BIN` or `PATH` for local runs.
- Python 3.11+ for host-side orchestration.
- Codex CLI 0.153.0+ for GPT-6 Astra in Codex.
- An account/workspace with GPT-6 Astra available for model review.
- `pip install -r requirements.txt`.

The CI reference runtime is declared in `config/toolchain.yaml`; local installations may use another compatible Blender version, but the pinned CI version is the tested baseline.

## Quick start

```bash
pip install -r requirements.txt
python scripts/check_environment.py
python scripts/blender_runner.py all
```

Core outputs:

```text
output/
├── scene.blend
├── render.png
├── renders/
├── render_index.json
├── scene_state.json
├── validation.json
├── visual_evaluation.json
└── _resolved_workflow.json
```

Run deterministic render checks without Astra:

```bash
python scripts/visual_evaluator.py --skip-model
```

Run full GPT-6 Astra review:

```bash
python scripts/visual_evaluator.py
```

Run the bounded autonomous correction loop from a clean Git worktree:

```bash
python scripts/iteration_controller.py
```

Run two independent clean builds and compare the structural manifests:

```bash
python scripts/reproducibility_check.py
```

This produces `output/reproducibility.json` and per-run snapshots under `output/reproducibility/`.

## Acceptance and autonomous-loop safety

`config/acceptance.yaml` is authoritative for structural requirements, required render views, and iteration policy. Required camera names/roles live there rather than only in mutable scene configuration, so an autonomous correction cannot improve its score by silently reducing review coverage.

The parent controller snapshots protected files before each correction-worker turn. If the worker changes acceptance/evaluator/autonomy policy, the review schema/prompt, orchestration code, or structural-validator implementation, the controller restores those files and stops the loop.

A live MCP edit is never accepted as completion until its durable equivalent exists in repository source and survives a clean build.

## Optional Blender MCP

The official Blender Lab architecture is:

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

After installing the official server/add-on:

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Copy `.codex/config.toml.example` to `.codex/config.toml` for project-local configuration. MCP remains optional: deterministic scene construction, CI and render evaluation do not depend on a live MCP session.

## Research basis

Primary references:

- OpenAI — Architectural visualization with Astra: https://developers.openai.com/blog/architectural-visualization-with-astra
- OpenAI — GPT-6 Astra: https://developers.openai.com/api/docs/models/gpt-6-astra
- OpenAI — Codex commands/non-interactive execution: https://learn.chatgpt.com/codex/developer-commands
- OpenAI — Codex MCP: https://developers.openai.com/codex/extend/mcp
- Blender — MCP Server: https://www.blender.org/lab/mcp-server/
- Blender — releases: https://download.blender.org/release/
- Blender Lab MCP source mirror: https://github.com/bpype/blender_mcp
- MCP specification: https://modelcontextprotocol.io/specification/2026-07-28/

Community implementation used as secondary evidence:

- https://github.com/ahujasid/blender-mcp

See `docs/RESEARCH.md`, `docs/ARCHITECTURE.md`, `docs/AUTONOMOUS_LOOP.md`, `docs/SETUP.md`, `docs/SECURITY.md`, `docs/MCP.md`, and `docs/ROADMAP.md`.
