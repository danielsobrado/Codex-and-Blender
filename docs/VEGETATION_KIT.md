# Reference vegetation kit

Open `output/vegetation_kit.blend`. Individual reusable files are in `output/objects/`.
The scene is an asset display, not a reconstruction of the landscape. It contains no character or rocks.

Included: four grasses (short, tall, dry, wide blade), four shrubs (low, round, tall, sage), two prickly-pear cactus sizes, green agave, and golden yucca.

Each GLB contains one mesh with embedded double-sided PBR materials, a ground-centered origin, UVs, and meter scale. Blender Z-up is converted to standard glTF Y-up on export. The labels, display ground, lights and cameras are excluded. Objects are marked as Blender assets in the main blend. Exact dimensions, triangle counts and seeds are in `output/objects/manifest.json`.

These are stylized geometry-based interpretations of the screenshot. They do not reproduce its high-detail textured game assets. No external textures were necessary or downloaded; there are no third-party texture dependencies. Wind animation, collision meshes and LODs are not included. Use instancing for repeated vegetation and add LODs for dense terrain.

## Rebuild

Activate `.venv`, set `BLENDER_BIN` to your Blender executable, then run:

```powershell
python scripts/blender_runner.py all
```

The current kit parameters are in `config/workflow.yaml`, and geometry/export code is in `blender/jobs/vegetation.py`. The previous rock configuration is preserved in `config/rock_workflow.yaml`; its existing `output/scene.blend` is preserved too. Vegetation-specific structural acceptance is in `config/vegetation_acceptance.yaml`.

Validate the actual exported files in a separate Blender process:

```powershell
& $env:BLENDER_BIN --background --factory-startup --python-exit-code 1 --python blender/jobs/verify_vegetation_exports.py
```

## Optional ChatGPT texture prompts

These prompts add surface detail later; the GLBs already work without them. Ask for base color only first. Generated pictures are not calibrated normal or roughness maps. Current UVs are simple per-face UVs; continuous leaf veins require re-unwrapping each complete blade or leaf before assigning an atlas.

**Grass blade atlas:** Create a 2048 by 2048 PNG botanical texture atlas with transparent background, 12 isolated complete grass blades arranged in separate vertical columns, bases at bottom and pointed tips at top. Mediterranean dry hillside vegetation: ochre gold, straw yellow, muted olive green. Fine longitudinal veins, occasional dry margins, subtle mottling. Straight flat blades, orthographic front view, even unlit base color, no cast shadows, no specular highlights, no soil, no text. Leave generous transparent padding around every blade.

**Shrub leaf atlas:** Create a 2048 by 2048 transparent PNG atlas of 16 separate narrow lanceolate shrub leaves in a regular 4 by 4 grid. Each leaf points upward with its stem at the bottom. Olive green, yellow-green and a few dusty sage variants, clear central midrib and subtle branching veins, slightly irregular natural edges. Flat orthographic botanical surface scan, diffuse albedo only, neutral illumination, no cast shadows, no branches, no labels. Generous transparent gutters.

**Cactus surface:** Create a seamless 2048 by 2048 base-color texture of prickly-pear cactus skin, muted dark olive and dusty sage green, fine waxy mottling, scattered tiny tan areoles, subtle age marks. Flat even illumination, no highlights, no shadows, no perspective, no whole cactus silhouette, no text. Make all four edges tile seamlessly.

**Agave surface:** Create a 2048 by 2048 texture of a single complete agave leaf, base centered at bottom and needle tip at top, transparent background. Dusty olive-sage surface, restrained longitudinal fibers, pale narrow edge, slight ochre drying near tip. Flat orthographic base color, no shadows or reflections, no pot, no ground, no labels.

## MCP setup

Project-local `.codex/config.toml` registers the installed official Blender MCP executable in `.venv/Scripts/`. `python scripts/check_blender_mcp.py` checks MCP initialization, tool discovery, and live read-only scene queries, saving `output/mcp_check.json`. The existing live bridge listens on localhost port 9876. Reload Codex if the newly registered tools are not visible in the current task. The configuration does not replace unsaved live Blender content.
