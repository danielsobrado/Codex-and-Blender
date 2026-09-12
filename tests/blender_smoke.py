from __future__ import annotations

import json
from pathlib import Path

import yaml

REQUIRED_ARTIFACTS = (
    Path("output/scene.blend"),
    Path("output/render.png"),
    Path("output/renders/FrontReviewCamera.png"),
    Path("output/renders/SideReviewCamera.png"),
    Path("output/render_index.json"),
    Path("output/scene_state.json"),
    Path("output/validation.json"),
    Path("output/visual_evaluation.json"),
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_blender_version() -> str:
    config = yaml.safe_load(Path("config/toolchain.yaml").read_text(encoding="utf-8"))
    return str(config["blender"]["version"])


def main() -> None:
    missing = [str(path) for path in REQUIRED_ARTIFACTS if not path.exists()]
    if missing:
        raise SystemExit(f"Missing artifacts: {missing}")

    validation = load_json(Path("output/validation.json"))
    if not validation.get("passed"):
        raise SystemExit(f"Structural validation failed: {validation.get('errors', [])}")

    evaluation = load_json(Path("output/visual_evaluation.json"))
    if not evaluation.get("passed"):
        errors = evaluation.get("deterministic", {}).get("errors", [])
        raise SystemExit(f"Deterministic visual evaluation failed: {errors}")

    state = load_json(Path("output/scene_state.json"))
    expected = expected_blender_version()
    actual = str(state.get("blender_version", ""))
    if not actual.startswith(expected):
        raise SystemExit(f"Expected Blender {expected}, got {actual or '<missing>'}")

    render_index = load_json(Path("output/render_index.json"))
    required_views = {
        view["name"]
        for view in render_index.get("views", [])
        if view.get("required", False)
    }
    expected_views = {"HeroCamera", "FrontReviewCamera", "SideReviewCamera"}
    if required_views != expected_views:
        raise SystemExit(
            f"Unexpected required render views: {sorted(required_views)}; "
            f"expected {sorted(expected_views)}"
        )


if __name__ == "__main__":
    main()
