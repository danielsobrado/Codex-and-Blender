from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.context import JobContext
from jobs.build_scene import build_scene
from jobs.inspect_scene import inspect_scene
from jobs.render_scene import render_scene
from jobs.validate_scene import validate_scene

LOGGER = logging.getLogger("blender_entrypoint")
VALID_ACTIONS = ("build", "render", "inspect", "validate", "all")


def script_args() -> list[str]:
    argv = sys.argv
    return argv[argv.index("--") + 1 :] if "--" in argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=VALID_ACTIONS, required=True)
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args(script_args())


def load_context(config_path: Path) -> JobContext:
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    return JobContext(config)


def save_blend(context: JobContext) -> None:
    path = context.path("blend_file")
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    LOGGER.info("Saved blend file: %s", path)


def run(action: str, context: JobContext) -> None:
    if action in ("build", "all"):
        build_scene(context)
        save_blend(context)

    if action in ("render", "all"):
        render_scene(context)

    if action in ("inspect", "all"):
        inspect_scene(context)

    if action in ("validate", "all"):
        validate_scene(context)

    if action == "all":
        save_blend(context)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    context = load_context(args.config)
    run(args.action, context)


if __name__ == "__main__":
    main()
