"""Publish the optimized coastal-jungle browser package to origin/gh-pages."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
DIST = ROOT / 'output' / 'browser'
PAGES_URL = 'https://danielsobrado.github.io/Codex-and-Blender/'


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True)
    return (result.stdout or result.stderr).strip()


def git_config(key: str) -> str:
    return subprocess.check_output(['git', 'config', key], cwd=ROOT, text=True).strip()


def collect_runtime() -> set[Path]:
    if not (DIST / 'app.js').is_file() or not (DIST / 'index.html').is_file():
        raise SystemExit(f'Missing optimized browser package in {DIST}. Run npm run build --prefix web.')
    runtime = {DIST / 'index.html', DIST / 'app.js', DIST / 'assets' / 'world_config.json'}
    models = [DIST / 'assets' / 'coastal_jungle.gltf'] + [
        DIST / 'assets' / 'objects' / f'tree_lod_0{i}.gltf' for i in (1, 2, 3)
    ]
    for model in models:
        if not model.is_file():
            raise SystemExit(f'Missing {model}. Run npm run build --prefix web.')
        runtime.add(model)
        document = json.loads(model.read_text(encoding='utf-8'))
        for resource in document.get('buffers', []) + document.get('images', []):
            uri = resource.get('uri')
            if not uri:
                continue
            dependency = (model.parent / uri).resolve()
            if not dependency.is_relative_to(DIST.resolve()) or not dependency.is_file():
                raise SystemExit(f'Invalid package dependency: {dependency}')
            runtime.add(dependency)
    return runtime


def stage(destination: Path) -> None:
    for source in sorted(collect_runtime()):
        target = destination / source.relative_to(DIST)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    html = (destination / 'index.html').read_text(encoding='utf-8')
    html = html.replace('src="/app.js"', 'src="app.js"').replace("src='/app.js'", 'src="app.js"')
    (destination / 'index.html').write_text(html, encoding='utf-8')
    (destination / '.nojekyll').write_text('', encoding='utf-8')


def publish(staging: Path, push: bool) -> None:
    name = git_config('user.name')
    email = git_config('user.email')
    remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, text=True).strip()
    env = os.environ.copy()
    env.update({
        'GIT_AUTHOR_NAME': name,
        'GIT_AUTHOR_EMAIL': email,
        'GIT_COMMITTER_NAME': name,
        'GIT_COMMITTER_EMAIL': email,
    })
    run(['git', 'init', '-b', 'gh-pages'], staging, env)
    run(['git', 'add', '.'], staging, env)
    run(['git', 'commit', '-m', 'deploy: coastal jungle GitHub Pages demo'], staging, env)
    if not push:
        print(f'Staged {staging} (--no-push)')
        return
    run(['git', 'push', '--force', remote, 'HEAD:gh-pages'], staging, env)
    print(PAGES_URL)


def enable_pages() -> None:
    try:
        subprocess.run(
            ['gh', 'api', 'repos/danielsobrado/Codex-and-Blender/pages', '-X', 'POST',
             '-f', 'source[branch]=gh-pages', '-f', 'source[path]=/'],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = (error.stderr or error.stdout or '').lower()
        if 'already exists' not in message and '409' not in message:
            print('GitHub Pages may need enabling in repository settings.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-push', action='store_true', help='stage files without pushing')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='coastal-jungle-gh-pages-') as temp:
        staging = Path(temp)
        stage(staging)
        publish(staging, push=not args.no_push)
    if not args.no_push:
        enable_pages()


if __name__ == '__main__':
    main()
