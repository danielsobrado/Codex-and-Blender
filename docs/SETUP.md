# Setup guide

This guide separates the **deterministic Blender workflow**, the **GPT-6 Astra self-correction workflow**, and the **optional live MCP workflow**. Prove the deterministic path first.

## 1. Clone and install host dependencies

```bash
git clone https://github.com/danielsobrado/Codex-and-Blender.git
cd Codex-and-Blender
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
```

Host Python uses PyYAML and Pillow. Blender-side scripts use Blender/standard-library modules only.

## 2. Install Blender

The repository's tested CI baseline is declared in `config/toolchain.yaml` and is currently Blender **5.2.1 LTS**.

The official Blender Lab MCP integration researched by this project requires Blender 5.1 or newer. For the most reproducible local behavior, start with the repository's pinned CI version.

If Blender is not on `PATH`, set `BLENDER_BIN`.

Windows PowerShell example:

```powershell
$env:BLENDER_BIN = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

macOS example:

```bash
export BLENDER_BIN="/Applications/Blender.app/Contents/MacOS/Blender"
```

On Ubuntu/headless Linux with Eevee, the CI runner installs the EGL/OpenGL runtime libraries:

```bash
sudo apt-get update
sudo apt-get install --yes libegl1 libgl1
```

## 3. Install/update Codex CLI

The autonomous visual workflow requires a Codex CLI with GPT-6 Astra support. The project environment check requires Codex CLI 0.153.0 or newer.

```bash
codex --version
```

Use the Codex authentication/account that has GPT-6 Astra available. The evaluator calls Codex directly and does not require a separate OpenAI SDK integration.

## 4. Verify the environment

```bash
python scripts/check_environment.py
```

This validates Blender and the minimum Codex version. `blender-mcp` is optional.

## 5. Prove the deterministic Blender workflow

```bash
python scripts/blender_runner.py all
```

Expected artifacts include:

```text
output/scene.blend
output/render.png
output/renders/FrontReviewCamera.png
output/renders/SideReviewCamera.png
output/scene_state.json
output/validation.json
output/_resolved_workflow.json
```

Then run deterministic render evaluation and the smoke assertions:

```bash
python scripts/visual_evaluator.py --skip-model
python tests/blender_smoke.py
```

The structural validator and deterministic image evaluator must pass before model review adds value.

## 6. Prove clean-build reproducibility

```bash
python scripts/reproducibility_check.py
```

The default contract runs two independent clean builds, inspects and validates each one, then compares their normalized scene-state JSON with the tolerance from `config/reproducibility.yaml`.

Outputs:

```text
output/reproducibility.json
output/reproducibility/run_01/scene_state.json
output/reproducibility/run_02/scene_state.json
```

Do not replace this with byte comparisons of `.blend` or rendered PNG files across different hardware/backends.

## 7. Prove GPT-6 Astra visual evaluation

```bash
python scripts/visual_evaluator.py
```

Codex runs GPT-6 Astra with the render images attached and constrains the final response with `schemas/visual_evaluation.schema.json`.

Required camera names/roles come from protected `config/acceptance.yaml`. Mutable workflow configuration cannot silently remove a required review view.

## 8. Run bounded autonomous correction

Start from a clean worktree:

```bash
git status --short
python scripts/iteration_controller.py
```

Policy is split intentionally:

- `config/acceptance.yaml` — structural/view requirements and iteration budget;
- `config/evaluator.yaml` — deterministic/Astra evaluation settings;
- `config/autonomy.yaml` — protected files and snapshot behavior.

The nested correction worker edits durable scene source; the parent process owns rebuild/render/evaluation. If the worker changes a protected quality-gate file, the parent restores it and stops.

See `docs/AUTONOMOUS_LOOP.md`.

## 9. Install Blender's official Lab MCP server (optional)

Primary references:

- https://www.blender.org/lab/mcp-server/
- https://github.com/bpype/blender_mcp

Prefer the installation instructions from the current Lab revision because packaging may change. After the Blender extension/bridge and `blender-mcp` executable are installed, verify:

```bash
blender-mcp --help
```

## 10. Register Blender MCP with Codex

```bash
codex mcp add blender -- blender-mcp
codex mcp list
```

Or copy:

```text
.codex/config.toml.example -> .codex/config.toml
```

The local config file is intentionally ignored by Git.

Before enabling broad live edits, prove tool discovery, Blender connection, scene/object summaries, missing-file inspection and screenshot/render capture.

## 11. Existing `.blend` files

Set:

```yaml
blender:
  startup_file: C:/path/to/source.blend
```

The builder replaces only the configured managed collection. For a fully generated scene, leave `startup_file: null`; the runner uses Blender factory startup.

## 12. CI contract

`.github/workflows/blender-smoke.yml` is a real runtime test. It:

1. resolves the pinned Blender toolchain from YAML;
2. verifies the official Blender archive checksum;
3. runs Blender on Ubuntu 24.04;
4. builds and renders all required views;
5. runs structural and deterministic visual validation;
6. verifies generated artifacts and Blender version;
7. runs the two-clean-build reproducibility regression;
8. uploads `.blend`, PNG and JSON evidence.

The public CI deliberately does not invoke authenticated Astra or a live MCP bridge.

## 13. Troubleshooting

### Blender executable not found

Set `BLENDER_BIN` or add Blender to `PATH`.

### Linux Eevee fails to initialize EGL

Install the EGL/OpenGL runtime packages shown above. Do not switch render engines merely to hide an environment dependency.

### Codex is installed but Astra evaluation fails

Update Codex CLI, verify model access for the authenticated account/workspace, then rerun `python scripts/check_environment.py`.

### Autonomous loop refuses to start

A dirty Git worktree is rejected by default. Review/commit/stash changes first, or use `--allow-dirty` only when the overlap is intentional.

### MCP connects but Blender does not respond

Check that the Blender MCP extension is enabled and its bridge server is running in the intended Blender instance.

### Headless build works but live MCP scene differs

That is configuration drift. Reopen the generated `.blend` or encode the live change in source and rebuild.

### Render regression across machines

Pin Blender/render settings and compare structural state plus calibrated visual metrics. Do not assume byte-identical images across hardware/backend combinations.
