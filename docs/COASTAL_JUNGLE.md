# Textured coastal jungle

The combined scene follows the latest tropical reference: an uphill clearing, dense green grass, ferns and broad leaves, foreground palms, taller canopy trees and hanging vines. The earlier dry hillside kit is preserved. Dry grass, cactus skin and agave textures are optimized but intentionally not scattered into the tropical biome.

## Files

- `output/forest/coastal_jungle.blend`: editable Blender scene with packed textures and linked mesh instances.
- `output/forest/coastal_jungle.glb`: combined scene with embedded WebP textures and `EXT_mesh_gpu_instancing`.
- `output/textures/`: eleven semantically named optimized PNGs and WebPs, a derived feathered path texture, and the filename/size/hash manifest.
- `assets/textures/`: full-resolution source copies, preserved byte-for-byte under descriptive names.
- `web/`: local Three.js viewer, pinned dependencies and browser verification.
- `output/forest/objects/`: 24 improved individually exported plant variants and their dimensions/triangle-count manifest.
- `output/forest_previous/`: saved scene and render snapshot from before the asset improvements.

The refined kit includes three grass variants, two ground-cover patches, two ferns, three broad-leaf plants, two palms, three canopy trees, two shrubs, two hanging vines, two trunk climbers, a simpler background tree and two split-leaf plants. Branch cross sections follow their direction, leaves have a folded midrib and curvature, and tree crowns use connected secondary twigs. Split-leaf silhouettes are modeled in the mesh. Vines export with a top attachment pivot; the other assets use ground origins.

The scene uses clustered grass, low leaf cover, a central clearing, placed foreground plants and a distant tree layer. Parameters and variant counts live in `config/forest_workflow.yaml`; the plant builders are in `blender/jobs/forest_plants.py`. The original supplied color textures are reused. The scene remains an approximation of the reference, with no character or logo.

Square textures are 1024 x 1024; the agave leaf is 512 x 1024 to preserve its aspect ratio. Transparent images retain alpha. PNG copies are available for broad tool compatibility. WebP reduces download size but is not GPU texture compression; mipmapped RGBA texture memory is still approximately 5.33 MiB per 1024-square texture. The forest uses seven maps. KTX2 and mobile-specific LODs are not included.

The latest uploads are named `jungle_ground_basecolor`, `jungle_path_basecolor`, and `jungle_grass_reference_atlas`. The original `jungle_grass_atlas` remains available. Ground and path textures repeat at a two-meter scale. `ForestPath` is a terrain-following ribbon using a derived irregular feathered alpha edge, so its soil fades into the surrounding forest floor in both Blender and the GLB. Surface filenames, texture scale and path width are configured under `forest.surface_textures`.

## Run

```powershell
cd web
npm ci
npm run dev
```

Open http://127.0.0.1:4173. Drag to orbit, scroll to move closer, and use Reference view or Forest interior to reset the camera. Wind changes vertex positions only in the Three.js viewer. Lighting, fog and shadows are configured by the viewer because scene GLB exports do not transfer the entire Blender rendering setup.

For another Three.js application, load the GLB with `GLTFLoader`. It must support `EXT_texture_webp` and `EXT_mesh_gpu_instancing` (the pinned Three.js version does). Retain alphaTest 0.4, double-sided foliage, sRGB color textures, mipmaps and anisotropic filtering. Avoid converting the instances into thousands of independent Mesh draw calls. The complete viewer implementation is in `web/main.js`.

## Rebuild

Activate `.venv` and set `BLENDER_BIN`, then:

```powershell
python scripts/prepare_textures.py
python scripts/blender_runner.py all --config config/forest_workflow.yaml
```

Texture names, source mapping and target sizes are controlled by `config/textures.yaml`. Scene parameters, seeds, cameras and densities are in `config/forest_workflow.yaml`; atlas meshes, UVs and scatter generation are in `blender/jobs/forest.py`. Generated output is not the source of truth.

## Validation and limits

Structural checks and exact object state are recorded in `output/forest/validation.json` and `scene_state.json`. Three Blender views and two browser screenshots provide visual evidence. `npm test` in `web/` checks loading, runtime exceptions, view switching, the wind toggle and a draw-call budget; results are saved in `output/forest/browser_validation.json`.

This is a textured procedural approximation, not a pixel-identical recreation. Surface detail comes from the supplied generated color images; there are no calibrated normal/roughness maps or scanned tree models. The scene uses a finite terrain patch, and free camera movement can reveal its edges. Headless browser timing in this environment is slow and is not a certified interactive frame-rate target; profile on the intended device before using the full density in production. Mobile LODs, collision and first-person navigation are not implemented.

Technical references: [Three.js InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html), [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), and [texture color management](https://threejs.org/manual/en/color-management.html).
