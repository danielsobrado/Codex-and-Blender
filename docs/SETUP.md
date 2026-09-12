# Setup guide

This guide separates the **core reproducible CLI workflow** from the **optional live MCP workflow**. Get the CLI workflow working first.

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

The host environment needs PyYAML. Blender-side scripts intentionally use only Blender/standard-library modules.

## 2. Install Blender

For the current official Blender Lab MCP integration, use Blender 5.1 or newer.

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

Verify:

```bash
python scripts/check_environment.py
```

## 3. Prove the deterministic workflow first

Run:

```bash
python scripts/blender_runner.py all
```

Expected artifacts:

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

The structural validation must pass before MCP is needed.

## 4. Install Codex CLI

Follow the current OpenAI Codex installation documentation for your platform, then verify:

```bash
codex --version
```

Codex MCP reference:
https://developers.openai.com/codex/extend/mcp

## 5. Install Blender's official Lab MCP server

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

## 6. Register Blender MCP with Codex

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

## 7. Start with inspection-only behavior

Before allowing broad live edits, prove these capabilities from the installed server version:

1. tool discovery works;
2. Blender is connected;
3. scene/object summaries work;
4. missing-file inspection works;
5. screenshots or viewport renders work.

Only after that should you enable broader mutation tools in an appropriately isolated environment.

## 8. Agent workflow

The normal task sequence should be:

```text
Codex reads AGENTS.md
        |
        v
edit YAML/Python source
        |
        v
python scripts/blender_runner.py all
        |
        +--> structural JSON
        +--> preview renders
        |
        v
MCP inspection if useful
        |
        v
visual/structural review
        |
        v
source patch + clean rebuild
```

Do not treat a successful live MCP edit as the end state.

## 9. Existing `.blend` files

Set:

```yaml
blender:
  startup_file: C:/path/to/source.blend
```

The builder only replaces the configured managed collection. Unrelated objects/collections are preserved.

For a fully generated scene, leave `startup_file: null`; the runner uses Blender factory startup.

## 10. Troubleshooting

### Blender executable not found

Set `BLENDER_BIN` or add Blender to `PATH`.

### MCP command not found

The MCP Python environment may not be activated or its executable may not be on `PATH`. Use an absolute command path in local `.codex/config.toml` if needed.

### MCP connects but Blender does not respond

Check that the Blender MCP extension is enabled and its bridge server is running in the Blender instance you intend to control.

### Headless build works but live MCP scene differs

That is configuration drift. Reopen the generated `output/scene.blend` or encode the live change in source and rebuild.

### Render regression across machines

Do not assume byte-identical output across GPU/backend/version combinations. Pin Blender/render settings and compare structural manifests plus calibrated visual metrics.
