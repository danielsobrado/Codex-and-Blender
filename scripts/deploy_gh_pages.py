"""Publish only the coastal-jungle web demo to origin/gh-pages."""
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
FOREST_GLB = ROOT / 'output' / 'forest' / 'coastal_jungle.glb'
PAGES_URL = 'https://danielsobrado.github.io/Codex-and-Blender/'


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True)
    return (result.stdout or result.stderr).strip()


def git_config(key: str) -> str:
    return subprocess.check_output(['git', 'config', key], cwd=ROOT, text=True).strip()


def three_version() -> str:
    package = json.loads((WEB / 'package.json').read_text(encoding='utf-8'))
    return package['dependencies']['three'].lstrip('^~')


def stage(destination: Path) -> None:
    if not FOREST_GLB.is_file():
        raise SystemExit(f'Missing {FOREST_GLB}. Build the forest scene first.')
    version = three_version()
    html = (WEB / 'index.html').read_text(encoding='utf-8')
    html = html.replace(
        '"three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"',
        f'"three":"https://cdn.jsdelivr.net/npm/three@{version}/build/three.module.js",'
        f'"three/addons/":"https://cdn.jsdelivr.net/npm/three@{version}/examples/jsm/"',
    )
    html = html.replace('src="/main.js"', 'src="./main.js"')
    js = (WEB / 'main.js').read_text(encoding='utf-8')
    js = js.replace(
        "loadAsync('/assets/coastal_jungle.glb')",
        "loadAsync(new URL('./assets/coastal_jungle.glb', import.meta.url).href)",
    )
    (destination / 'index.html').write_text(html, encoding='utf-8')
    (destination / 'main.js').write_text(js, encoding='utf-8')
    shutil.copy2(WEB / 'sky.js', destination / 'sky.js')
    (destination / '.nojekyll').write_text('', encoding='utf-8')
    assets = destination / 'assets'
    assets.mkdir()
    shutil.copy2(FOREST_GLB, assets / 'coastal_jungle.glb')


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
    run(['git', 'add', 'index.html', 'main.js', 'sky.js', '.nojekyll', 'assets/coastal_jungle.glb'], staging, env)
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
