from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageStat

LOGGER = logging.getLogger("visual_evaluator")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "config" / "workflow.yaml"
CODEX_EXECUTABLE = "codex"


class EvaluationError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise EvaluationError(f"Cannot read YAML: {path}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"YAML root must be a mapping: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"Cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"JSON root must be an object: {path}")
    return value


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def required_view_policy(acceptance: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if acceptance is None:
        return {}

    raw = acceptance.get("visual", {}).get("required_views", [])
    if not isinstance(raw, list):
        raise EvaluationError("visual.required_views must be a list.")

    policy: dict[str, dict[str, Any]] = {}
    for spec in raw:
        if not isinstance(spec, dict) or not spec.get("name"):
            raise EvaluationError("Each required visual view must have a name.")
        name = str(spec["name"])
        if name in policy:
            raise EvaluationError(f"Duplicate required visual view: {name}")
        policy[name] = spec
    return policy


def build_render_index(
    workflow: dict[str, Any], acceptance: dict[str, Any] | None = None
) -> dict[str, Any]:
    paths = workflow["paths"]
    cameras = workflow.get("cameras", [])
    if not cameras:
        raise EvaluationError("No cameras are configured.")

    primary_cameras = [camera for camera in cameras if camera.get("primary", False)]
    if len(primary_cameras) != 1:
        raise EvaluationError("Exactly one primary camera must be configured.")

    policy = required_view_policy(acceptance)
    camera_names = {str(camera.get("name")) for camera in cameras}
    missing_policy_views = sorted(set(policy) - camera_names)
    if missing_policy_views:
        raise EvaluationError(
            "Required visual cameras are missing: " + ", ".join(missing_policy_views)
        )

    render_primary = resolve(paths["render_file"])
    render_dir = resolve(paths["render_dir"])
    include_reviews = bool(workflow.get("render", {}).get("render_review_cameras", True))
    views: list[dict[str, Any]] = []

    for camera in cameras:
        name = str(camera["name"])
        is_primary = bool(camera.get("primary", False))
        policy_spec = policy.get(name)
        required = policy_spec is not None or bool(camera.get("required", True))

        if policy_spec is not None:
            expected_role = policy_spec.get("role")
            actual_role = camera.get("role", "unspecified")
            if expected_role is not None and actual_role != expected_role:
                raise EvaluationError(
                    f"Required view {name} has role {actual_role!r}; expected {expected_role!r}."
                )
            if "primary" in policy_spec and is_primary != bool(policy_spec["primary"]):
                raise EvaluationError(
                    f"Required view {name} has unexpected primary-camera status."
                )

        if not is_primary and not include_reviews:
            if required:
                raise EvaluationError(
                    f"Required review camera is disabled by render settings: {name}"
                )
            continue

        path = render_primary if is_primary else render_dir / f"{name}.png"
        views.append(
            {
                "name": name,
                "role": camera.get("role", "unspecified"),
                "primary": is_primary,
                "required": required,
                "path": str(path),
            }
        )

    result = {"version": 1, "views": views}
    index_path = resolve(paths.get("render_index_file", "output/render_index.json"))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def image_metrics(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            image.load()
            luminance = image.convert("L")
            stats = ImageStat.Stat(luminance)
            histogram = luminance.histogram()
            pixels = max(1, luminance.width * luminance.height)
    except (OSError, ValueError) as exc:
        raise EvaluationError(f"Cannot inspect render: {path}") from exc

    dark_threshold = int(config.get("dark_threshold", 4))
    bright_threshold = int(config.get("bright_threshold", 251))
    dark_fraction = sum(histogram[: dark_threshold + 1]) / pixels
    bright_fraction = sum(histogram[bright_threshold:]) / pixels

    return {
        "width": luminance.width,
        "height": luminance.height,
        "luminance_mean": round(float(stats.mean[0]), 4),
        "luminance_stddev": round(float(stats.stddev[0]), 4),
        "dark_fraction": round(dark_fraction, 6),
        "bright_fraction": round(bright_fraction, 6),
        "file_bytes": path.stat().st_size,
    }


def deterministic_review(
    render_index: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    views: list[dict[str, Any]] = []

    min_width = int(config.get("min_width", 1))
    min_height = int(config.get("min_height", 1))
    min_stddev = float(config.get("min_luminance_stddev", 0.0))
    max_dark = float(config.get("max_dark_fraction", 1.0))
    max_bright = float(config.get("max_bright_fraction", 1.0))

    for view in render_index["views"]:
        path = Path(view["path"])
        entry = {**view, "metrics": None}
        if not path.exists():
            if view["required"]:
                errors.append({"view": view["name"], "error": "Required render is missing."})
            views.append(entry)
            continue

        metrics = image_metrics(path, config)
        entry["metrics"] = metrics
        views.append(entry)

        checks = (
            (metrics["width"] < min_width, f"Width {metrics['width']} is below {min_width}."),
            (metrics["height"] < min_height, f"Height {metrics['height']} is below {min_height}."),
            (
                metrics["luminance_stddev"] < min_stddev,
                f"Luminance stddev {metrics['luminance_stddev']} is below {min_stddev}.",
            ),
            (
                metrics["dark_fraction"] > max_dark,
                f"Dark fraction {metrics['dark_fraction']} exceeds {max_dark}.",
            ),
            (
                metrics["bright_fraction"] > max_bright,
                f"Bright fraction {metrics['bright_fraction']} exceeds {max_bright}.",
            ),
        )
        for failed, message in checks:
            if failed:
                errors.append({"view": view["name"], "error": message})

    return {"passed": not errors, "errors": errors, "views": views}


def build_model_prompt(
    prompt_path: Path,
    render_index: dict[str, Any],
    state_path: Path,
    validation_path: Path,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    ordered_views = "\n".join(
        f"{index + 1}. {view['name']} ({view['role']})"
        for index, view in enumerate(render_index["views"])
        if Path(view["path"]).exists()
    )
    return (
        f"{prompt}\n\n"
        "Exact scene evidence is available in these files:\n"
        f"- {display_path(state_path)}\n"
        f"- {display_path(validation_path)}\n\n"
        "The attached images are in this exact order:\n"
        f"{ordered_views}\n\n"
        "Read the exact scene evidence before reviewing the images. Return only the "
        "schema-constrained evaluation."
    )


def run_model_review(
    config: dict[str, Any],
    render_index: dict[str, Any],
    state_path: Path,
    validation_path: Path,
) -> dict[str, Any]:
    if shutil.which(CODEX_EXECUTABLE) is None:
        raise EvaluationError("Codex CLI was not found on PATH.")

    prompt_path = resolve(config["prompt_file"])
    schema_path = resolve(config["output_schema_file"])
    if not prompt_path.exists() or not schema_path.exists():
        raise EvaluationError("Visual review prompt or output schema is missing.")

    image_paths = [
        Path(view["path"])
        for view in render_index["views"]
        if Path(view["path"]).exists()
    ]
    if not image_paths:
        raise EvaluationError("No render images are available for model review.")

    prompt = build_model_prompt(prompt_path, render_index, state_path, validation_path)
    command = [
        CODEX_EXECUTABLE,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--model",
        str(config.get("model", "gpt-6-astra")),
        "--config",
        f'model_reasoning_effort="{config.get("reasoning_effort", "high")}"',
        "--output-schema",
        str(schema_path),
    ]
    for image_path in image_paths:
        command.extend(["--image", str(image_path)])

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as handle:
        result_path = Path(handle.name)

    command.extend(["--output-last-message", str(result_path), "-"])
    try:
        subprocess.run(
            command,
            cwd=ROOT,
            input=prompt,
            text=True,
            check=True,
        )
        return load_json(result_path)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvaluationError("Codex visual review failed.") from exc
    finally:
        result_path.unlink(missing_ok=True)


def evaluate(workflow_path: Path, skip_model: bool = False) -> dict[str, Any]:
    workflow = load_yaml(workflow_path)
    paths = workflow["paths"]
    acceptance = load_yaml(resolve(paths["acceptance_file"]))
    evaluator = load_yaml(resolve(paths["evaluator_file"]))
    state_path = resolve(paths["state_file"])
    validation_path = resolve(paths["validation_file"])
    validation = load_json(validation_path)
    if not validation.get("passed", False):
        raise EvaluationError("Structural validation must pass before visual evaluation.")
    load_json(state_path)

    render_index = build_render_index(workflow, acceptance)
    deterministic = deterministic_review(render_index, evaluator.get("deterministic", {}))
    model_config = evaluator.get("model_review", {})
    model_review: dict[str, Any] | None = None

    configured_enabled = bool(model_config.get("enabled", True))
    configured_required = bool(model_config.get("required", True))
    if configured_required and not configured_enabled and not skip_model:
        raise EvaluationError("Model review cannot be required while disabled.")

    enabled = configured_enabled and not skip_model
    required = configured_required and not skip_model
    if deterministic["passed"] and enabled:
        try:
            model_review = run_model_review(
                model_config, render_index, state_path, validation_path
            )
        except EvaluationError:
            if required:
                raise
            LOGGER.exception("Optional model review failed.")

    passed = deterministic["passed"] and (
        model_review is None or bool(model_review.get("passed", False))
    )
    result = {
        "version": 1,
        "passed": passed,
        "score": model_review.get("score") if model_review else None,
        "deterministic": deterministic,
        "model_review": model_review,
    }

    output = resolve(paths["evaluation_file"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Blender render evidence.")
    parser.add_argument("--config", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--skip-model", action="store_true")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    try:
        result = evaluate(args.config.resolve(), skip_model=args.skip_model)
    except (EvaluationError, KeyError, TypeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2

    LOGGER.info("Visual evaluation passed=%s score=%s", result["passed"], result["score"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
