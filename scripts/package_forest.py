"""Package the current verified GLBs, textures and local Three.js viewer."""
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FOREST = ROOT / 'output/forest'


def main():
    evidence = {}
    for name in ('validation', 'glb_validation', 'browser_validation'):
        path = FOREST / f'{name}.json'
        evidence[name] = json.loads(path.read_text())
        if evidence[name].get('passed') is not True:
            raise RuntimeError(f'{path} has not passed.')
    glb = FOREST / 'coastal_jungle.glb'
    for path in [FOREST / 'validation.json', FOREST / 'glb_validation.json', FOREST / 'browser_validation.json',
                 FOREST / 'render.png', FOREST / 'threejs_preview.png', FOREST / 'threejs_interior.png', FOREST / 'threejs_overview.png']:
        if path.stat().st_mtime < glb.stat().st_mtime:
            raise RuntimeError(f'Rebuild current evidence before packaging: {path}')
    data = glb.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + length])
    bark = next(m for m in document['materials'] if m['name'] == 'palm_bark_basecolor')
    if not bark['pbrMetallicRoughness'].get('baseColorFactor'):
        raise RuntimeError('Bark tint was lost in the GLB export.')
    report = {'glb_sha256': hashlib.sha256(data).hexdigest(), 'glb_bytes': len(data),
              'assets': len(evidence['glb_validation']['assets']),
              'browser': evidence['browser_validation'], 'extensions': document['extensionsUsed']}
    (FOREST / 'delivery_report.json').write_text(json.dumps(report, indent=2))
    objects = sorted((FOREST / 'objects').glob('*'))
    with ZipFile(ROOT / 'output/coastal_jungle_objects.zip', 'w', ZIP_DEFLATED) as archive:
        for path in objects:
            if path.is_file():
                archive.write(path, f'objects/{path.name}')
    files = [p for p in (ROOT / 'web').rglob('*') if p.is_file() and 'node_modules' not in p.parts]
    files += [ROOT / 'docs/COASTAL_JUNGLE.md', ROOT / 'docs/NEXT_TEXTURE_PROMPTS.md']
    files += [p for p in FOREST.rglob('*') if p.is_file() and p.suffix in ('.glb', '.blend', '.png', '.json')
              and p.parent in (FOREST, FOREST / 'objects', FOREST / 'renders') and not p.name.startswith('_')]
    files += list((ROOT / 'output/textures').glob('*.webp'))
    files += list((ROOT / 'output/textures').glob('*.json'))
    with ZipFile(ROOT / 'output/coastal_jungle_web_pack.zip', 'w', ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
