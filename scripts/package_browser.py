"""Package only reachable runtime files; keep reusable GLBs in a separate archive."""
import json
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'output/browser'


def main():
    report = json.loads((DIST / 'optimization_report.json').read_text())
    validation = json.loads((DIST / 'browser_validation.json').read_text())
    assets = json.loads((DIST / 'asset_validation.json').read_text())
    for record in assets['assets']:
        source = ROOT / 'output/forest' / (record['name'] if record['name'] == 'coastal_jungle.glb' else 'objects/' + record['name'])
        if hashlib.sha256(source.read_bytes()).hexdigest() != record['sourceSHA256']:
            raise RuntimeError(f'Source changed after validation: {source}')
    if not report['passed'] or not validation['passed']:
        raise RuntimeError('Optimization and browser validation must pass before packaging.')
    if (DIST / 'browser_validation.json').stat().st_mtime < (DIST / 'app.js').stat().st_mtime:
        raise RuntimeError('Browser evidence is older than the build.')
    runtime = {DIST / name for name in ('index.html', 'app.js', 'serve.mjs', 'assets/world_config.json')}
    models = [DIST / 'assets/coastal_jungle.gltf'] + [DIST / f'assets/objects/tree_lod_0{i}.gltf' for i in (1, 2, 3)]
    for model in models:
        runtime.add(model)
        document = json.loads(model.read_text())
        for resource in document.get('buffers', []) + document.get('images', []):
            if 'uri' in resource:
                dependency = (model.parent / resource['uri']).resolve()
                if not dependency.is_relative_to(DIST.resolve()) or not dependency.is_file():
                    raise RuntimeError(f'Invalid dependency: {dependency}')
                runtime.add(dependency)
    transferred = sum((p.with_name(p.name + '.br') if p.with_name(p.name + '.br').exists() else p).stat().st_size for p in runtime if p.name != 'serve.mjs')
    runtime |= {p.with_name(p.name + '.br') for p in runtime if p.with_name(p.name + '.br').exists()}
    with ZipFile(ROOT / 'output/coastal_jungle_browser.zip', 'w', ZIP_DEFLATED) as archive:
        for file in sorted(runtime):
            archive.write(file, file.relative_to(DIST))
        archive.write(ROOT / 'LICENSE', 'LICENSE')
        archive.write(ROOT / 'web/node_modules/three/LICENSE', 'licenses/three.txt')
        archive.write(ROOT / 'web/node_modules/meshoptimizer/LICENSE.md', 'licenses/meshoptimizer.txt')
        archive.write(ROOT / 'docs/BROWSER_PACKAGE.md', 'README.md')
    with ZipFile(ROOT / 'output/coastal_jungle_objects_optimized.zip', 'w', ZIP_DEFLATED) as archive:
        for file in sorted((DIST / 'objects').glob('*')):
            archive.write(file, file.relative_to(DIST))
        archive.write(ROOT / 'docs/BROWSER_PACKAGE.md', 'README.md')
        archive.write(ROOT / 'LICENSE', 'LICENSE')
    report['runtimeEncodedBytes'] = transferred
    report['browserZipBytes'] = (ROOT / 'output/coastal_jungle_browser.zip').stat().st_size
    report['objectsZipBytes'] = (ROOT / 'output/coastal_jungle_objects_optimized.zip').stat().st_size
    report['browserValidation'] = validation
    (DIST / 'delivery_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ('assets', 'browserValidation')}, indent=2))


if __name__ == '__main__':
    main()
