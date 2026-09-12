from __future__ import annotations

import json
from pathlib import Path


REQUIRED_ARTIFACTS = (
    Path("output/scene.blend"),
    Path("output/render.png"),
    Path("output/scene_state.json"),
    Path("output/validation.json"),
)


def main() -> None:
    missing = [str(path) for path in REQUIRED_ARTIFACTS if not path.exists()]
    if missing:
        raise SystemExit(f"Missing artifacts: {missing}")

    validation = json.loads(Path("output/validation.json").read_text(encoding="utf-8"))
    if not validation.get("passed"):
        raise SystemExit(f"Validation failed: {validation.get('errors', [])}")


if __name__ == "__main__":
    main()
