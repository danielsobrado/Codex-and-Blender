# Tropical jungle vegetation kit

Open `output/tropical/jungle_vegetation_kit.blend`. All 16 individual GLBs are in `output/tropical/objects/`. The previous dry-hillside kit is preserved in `output/vegetation_kit.blend` and `output/objects/`.

## Included assets

- Short, tall and broad-blade jungle grass; broad-leaf ground cover.
- Small and large ferns, elephant-ear-inspired plant, banana-like understory plant.
- Young palm, tall ringed-trunk palm, branching jungle canopy tree, hanging vine cluster.
- Four construction pieces: palm frond, fern frond, broad leaf and individual vine strand.

These are stylized mesh interpretations of the reference vegetation, not copies of the game's textured assets. The display scene lets you inspect individual pieces; it does not recreate the full forest.

## Reuse and generation

Import any GLB into your engine or Blender. Every file contains one mesh with embedded double-sided PBR materials and meter scale, without display labels, cameras or ground. Blender Z-up is converted to glTF Y-up. Plants use base origins; standalone fronds/leaves start at their stems. Vines use a bottom-reference origin, with their attachment height recorded by the configured `height` (3.2 m cluster; 2 m strand).

Use the complete plants as instances for terrain scattering. Use construction pieces to assemble new plants. Randomize rotation around the vertical axis and vary scale moderately. Scatter grass densely, broad leaves and ferns in groups, then place trees sparsely and suspend vines beneath branches. These meshes have no wind rig, collision or LODs; dense runtime forests will need engine-specific optimization. Exact triangle counts and dimensions are in `output/tropical/objects/manifest.json`.

To generate different shapes, change seeds, dimensions, frond counts, leaflet pairs, crown radii and palette in `config/tropical_workflow.yaml`. The durable builders are `blender/jobs/tropical.py` and `blender/jobs/vegetation.py`.

Activate `.venv`, set `BLENDER_BIN`, then rebuild:

```powershell
python scripts/blender_runner.py all --config config/tropical_workflow.yaml
```

Validate exported files in a disposable Blender process:

```powershell
& $env:BLENDER_BIN --background --factory-startup --python-exit-code 1 --python blender/jobs/verify_vegetation_exports.py -- output/tropical/objects
```

Evidence is under `output/tropical/`: `scene_state.json`, `validation.json`, `glb_validation.json`, `render.png`, and two detail renders in `renders/`.

## Optional texture-generation prompts

No textures were downloaded or required. Current assets use embedded material colors. For a more realistic surface pass, use these prompts in ChatGPT. Current UVs are per-face; unwrap entire leaves/fronds or trunks before applying directional atlases. A generated base-color image is not a calibrated normal or roughness map.

**Tropical grass atlas:** Create a 2048 x 2048 transparent PNG texture atlas containing 12 isolated whole tropical grass blades, upright in separate columns, base at bottom and pointed tip at top. Deep jungle green, fresh lime green, subtle yellow-green sun-aged tips, fine longitudinal veins. Flat orthographic base-color scan with neutral illumination, no shadows, no highlights, no ground, no text. Generous transparent gutters around each blade.

**Palm and fern atlas:** Create a 4096 x 4096 transparent PNG botanical atlas, four isolated palm fronds in the upper half and four isolated fern fronds in the lower half. Complete silhouettes with stems downward, non-overlapping leaflets, rich tropical green with restrained color variation and visible midribs. Orthographic flat albedo scan, no directional lighting, no shadows, no scene or text. Generous transparent padding between fronds.

**Broad-leaf atlas:** Create a 2048 x 2048 transparent PNG atlas of eight individual complete tropical leaves: four large heart-shaped elephant-ear leaves and four elongated banana leaves. Dark glossy-green coloration represented as diffuse base color only, clear central veins and fine side veins, a few natural edge splits on banana leaves. Flat front-facing scan, evenly lit, no highlights, no shadows, no stems crossing other cells, no text.

**Palm bark:** Create a seamless 2048 x 2048 PBR base-color texture of gray-tan tropical palm trunk bark, horizontal narrow growth scars, faint vertical fibers, subtle pale lichen near the bottom. Flat evenly lit surface scan, no shadows, no cylindrical perspective, no foliage, no text. Tile both axes seamlessly.

**Jungle tree bark:** Create a seamless 2048 x 2048 base-color texture of weathered tropical tree bark, muted warm gray-brown, shallow irregular vertical fissures, restrained moss-green patches and pale lichen. Even diffuse illumination, no shadows or highlights, no trunk silhouette, no text. Tile seamlessly on all edges.
