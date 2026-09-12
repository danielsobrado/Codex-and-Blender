"""Round-trip every GLB in a disposable factory-startup Blender process."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
directory = ROOT/args[0] if args else ROOT/'output/objects'
manifest = json.loads((directory/'manifest.json').read_text())
checks = []
for asset in manifest['assets']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(directory/asset['file']))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    assert len(meshes) == 1, asset['name']
    obj = meshes[0]
    bpy.context.view_layer.update()
    assert all(abs(a-b) < .0001 for a,b in zip(obj.dimensions,asset['dimensions_m'])), asset['name']
    assert obj.location.length < .0001, asset['name']
    assert len(obj.data.uv_layers) > 0, asset['name']
    triangles = sum(len(p.vertices)-2 for p in obj.data.polygons)
    assert triangles == asset['triangles'], asset['name']
    assert obj.data.materials and all(m.use_nodes for m in obj.data.materials), asset['name']
    checks.append({'name':asset['name'],'passed':True,'triangles':triangles,'dimensions_m':list(obj.dimensions)})
(directory.parent/'glb_validation.json').write_text(json.dumps({'passed':True,'assets':checks},indent=2))
print('PASS: all GLBs re-import with geometry, UVs, materials, dimensions and origin intact.')
