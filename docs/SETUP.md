# Setup guide

This guide separates the **core reproducible CLI workflow**, the **Astra visual/self-correction workflow**, and the **optional live MCP workflow**. Get the deterministic CLI path working first.

## 1. Clone and create a Python environment

```bash
git clone https://github.com/danielsobrado/Codex-and-Blender.git
cd Codex-and-Blender
python -m venv .venv
```

Activate the environment and install host dependencies:

```bash
pip install -r requirements.txt
```

Host Python uses PyYAML for configuration and Pillow for deterministic render metrics. Blender-side scripts intentionally use only Blender/standard-library modules.

## 2. Install Blender

For the researched current official Blender Lab MCP integration, use Blender 5.1 or newer.

If `blender` is not on `PATH`, set `BLENDER_BIN`.

Windows PowerShell:

```powershell
$env:BLENDER_BIN = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
```

macOS:

```bash
export BLENDER_BIN="/Applications/Blender.app/Contents/MacOS/Blender"
```

Linux usually needs no override when Blender is installed on `PATH`.

## 3. Install/update Codex CLI

The autonomous visual workflow requires a current Codex CLI with GPT-6 Astra support. The project environment check requires Codex CLI 0.153.0 or newer.

Verify:

```bash
codex --version
```

Use the same Codex authentication/account that has GPT-6 Astra available. The visual evaluator calls Codex directly, so this workflow does not add a separate OpenAI SDK/API integration.

## 4. Verify the host environment

```bash
python scripts/check_environment.py
```

This validates Blender and the minimum Codex CLI version. `blender-mcp` is checked as an optional command.

## 5. Prove the deterministic Blender workflow

Run:

```bash
python scripts/blender_runner.py all
```

Expected core artifacts:

```text
output/scene.blend
output/render.png
output/renders/FrontReviewCamera.png
output/renders/SideReviewCamera.png
output/scene_state.json
output/validation.json
output/_resolved_workflow.json
```

Then run:

```bash
python tests/blender_smoke.py
```

Structural validation must pass before visual automation or MCP adds value.

## 6. Prove visual evaluation

First test deterministic render checks without using Astra:

```bash
python scripts/visual_evaluator.py --skip-model
```

This produces `output/render_index.json` and `output/visual_evaluation.json`.

Then run the full visual review:

```bash
python scripts/visual_evaluator.py
```

Codex runs GPT-6 Astra with the rendered images attached and constrains the final result with `schemas/visual_evaluation.schema.json`.

If this step fails while Codex itself works, verify that your account/workspace can select GPT-6 Astra and that your Codex CLI is current.

## 7. Run the bounded autonomous loop

Start from a clean Git working tree:

```bash
git status --short
python scripts/iteration_controller.py
```

The controller repeatedly rebuilds from durable source, evaluates the resulting views, and asks a separate Codex correction worker for the smallest justified source edit.

Runtime policy is split intentionally:

- `config/acceptance.yaml` — iteration budget and acceptance policy;
- `config/evaluator.yaml` — deterministic/Astra evaluation settings;
- `config/autonomy.yaml` — protected files and snapshot policy.

Do not start with `--allow-dirty` unless you intentionally want the controller to operate on top of existing local source changes.

See `docs/AUTONOMOUS_LOOP.md` for stop conditions and evidence retention.

## 8. Install Blender's official Lab MCP server (optional)

The official Blender Lab project contains both the MCP server and Blender extension/add-on.

Primary references:

- https://www.blender.org/lab/mcp-server/
- https://github.com/bpype/blender_mcp

The exact installation commands can change with the Lab project, so prefer the instructions from the installed/current repository revision. The researched installation pattern is:

```bash
git clone https://projects.blender.org/lab/blender_mcp.git
cd blender_mcp
python -m venv .venv
```

Activate that environment, then install the server package according to its current requirements/package metadata. The package provides the `blender-mcp` executable.

The Blender extension can be built from the official repository and installed through Blender's extension/add-on mechanism. After installation, enable the MCP bridge server in Blender.

Verify the server command:

```bash
blender-mcp --help
```

## 9. Register Blender MCP with Codex

CLI registration:

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Or copy the repository template:

```text
.codex/config.toml.example -> .codex/config.toml
```

The local config file is intentionally ignored by Git.

## 10. Start MCP with inspection-only behavior

Before allowing broad live edits, prove these capabilities from the installed server version:

1. tool discovery works;
2. Blender is connected;
3. scene/object summaries work;
4. missing-file inspection works;
5. screenshots or viewport renders work.

Only after that should you enable broader mutation tools in an appropriately isolated environment.

## 11. Existing `.blend` files

Set:

```yaml
blender:
  startup_file: C:/path/to/source.blend
```

The builder only replaces the configured managed collection. Unrelated objects/collections are preserved.

For a fully generated scene, leave `startup_file: null`; the runner uses Blender factory startup.

## 12. Troubleshooting

### Blender executable not found

Set `BLENDER_BIN` or add Blender to `PATH`.

### Codex is installed but Astra evaluation fails

Update Codex CLI, verify model access for the authenticated account/workspace, then rerun `python scripts/check_environment.py`.

### Autonomous loop refuses to start

A dirty Git worktree is rejected by default. Review/commit/stash your changes first, or use `--allow-dirty` only when the overlap is intentional.

### MCP command not found

The MCP Python environment may not be activated or its executable may not be on `PATH`. Use an absolute command path in local `.codex/config.toml` if needed.

### MCP connects but Blender does not respond

Check that the Blender MCP extension is enabled and its bridge server is running in the Blender instance you intend to control.

### Headless build works but live MCP scene differs

That is configuration drift. Reopen the generated `output/scene.blend` or encode the live change in source and rebuild.

### Render regression across machines

Do not assume byte-identical output across GPU/backend/version combinations. Pin Blender/render settings and compare structural manifests plus calibrated visual metrics.
