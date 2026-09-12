from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from numbers import Real
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger("reproducibility_check")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "config" / "workflow.yaml"
DEFAULT_CONFIG = ROOT / "config" / "reproducibility.yaml"
RUNNER = ROOT / "scripts" / "blender_runner.py"


class ReproducibilityError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise ReproducibilityError(f"Cannot read YAML: {path}") from exc
    if not isinstance(value, dict):
        raise ReproducibilityError(f"YAML root must be a mapping: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReproducibilityError(f"Cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ReproducibilityError(f"JSON root must be an object: {path}")
    return value


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def run_stage(action: str, workflow_path: Path) -> None:
    command = [
        sys.executable,
        str(RUNNER),
        action,
        "--config",
        str(workflow_path),
    ]
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        raise ReproducibilityError(
            f"Blender stage '{action}' failed with exit code {exc.returncode}."
        ) from exc


def is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def compare_manifests(
    left: Any,
    right: Any,
    tolerance: float,
    max_differences: int,
) -> tuple[list[dict[str, Any]], bool]:
    differences: list[dict[str, Any]] = []
    truncated = False

    def add(path: str, left_value: Any, right_value: Any, reason: str) -> None:
        nonlocal truncated
        if len(differences) >= max_differences:
            truncated = True
            return
        differences.append(
            {
                "path": path,
                "left": left_value,
                "right": right_value,
                "reason": reason,
            }
        )

    def compare(left_value: Any, right_value: Any, path: str) -> None:
        nonlocal truncated
        if truncated:
            return

        if is_number(left_value) and is_number(right_value):
            delta = abs(float(left_value) - float(right_value))
            if delta > tolerance:
                add(path, left_value, right_value, f"numeric delta {delta} exceeds {tolerance}")
            return

        if isinstance(left_value, dict) and isinstance(right_value, dict):
            left_keys = set(left_value)
            right_keys = set(right_value)
            for key in sorted(left_keys - right_keys):
                add(f"{path}.{key}", left_value[key], None, "missing from right manifest")
            for key in sorted(right_keys - left_keys):
                add(f"{path}.{key}", None, right_value[key], "missing from left manifest")
            for key in sorted(left_keys & right_keys):
                compare(left_value[key], right_value[key], f"{path}.{key}")
            return

        if isinstance(left_value, list) and isinstance(right_value, list):
            if len(left_value) != len(right_value):
                add(path, len(left_value), len(right_value), "list length differs")
                return
            for index, (left_item, right_item) in enumerate(zip(left_value, right_value)):
                compare(left_item, right_item, f"{path}[{index}]")
            return

        if type(left_value) is not type(right_value):
            add(path, left_value, right_value, "value type differs")
            return

        if left_value != right_value:
            add(path, left_value, right_value, "value differs")

    compare(left, right, "$")
    return differences, truncated


def capture_manifest(
    workflow_path: Path,
    workflow: dict[str, Any],
    snapshot_dir: Path,
    run_number: int,
) -> tuple[dict[str, Any], Path]:
    run_stage("build", workflow_path)
    run_stage("inspect", workflow_path)
    run_stage("validate", workflow_path)

    state_path = resolve(workflow["paths"]["state_file"])
    validation_path = resolve(workflow["paths"]["validation_file"])
    state = load_json(state_path)
    validation = load_json(validation_path)
    if not validation.get("passed", False):
        raise ReproducibilityError(f"Structural validation failed in run {run_number}.")

    run_dir = snapshot_dir / f"run_{run_number:02d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    state_snapshot = run_dir / "scene_state.json"
    validation_snapshot = run_dir / "validation.json"
    state_snapshot.write_text(json.dumps(state, indent=2), encoding="utf-8")
    validation_snapshot.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    return state, state_snapshot


def check_reproducibility(
    workflow_path: Path,
    config_path: Path,
) -> dict[str, Any]:
    workflow = load_yaml(workflow_path)
    config = load_yaml(config_path)

    runs = int(config.get("runs", 2))
    tolerance = float(config.get("numeric_tolerance", 0.0))
    max_differences = int(config.get("max_reported_differences", 100))
    if runs < 2:
        raise ReproducibilityError("At least two clean builds are required.")
    if tolerance < 0:
        raise ReproducibilityError("numeric_tolerance cannot be negative.")
    if max_differences < 1:
        raise ReproducibilityError("max_reported_differences must be at least one.")

    snapshot_dir = resolve(str(config["snapshot_dir"]))
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    manifests: list[dict[str, Any]] = []
    manifest_paths: list[str] = []
    for run_number in range(1, runs + 1):
        LOGGER.info("Capturing clean build %d/%d.", run_number, runs)
        manifest, snapshot = capture_manifest(
            workflow_path,
            workflow,
            snapshot_dir,
            run_number,
        )
        manifests.append(manifest)
        manifest_paths.append(str(snapshot.relative_to(ROOT)))

    baseline = manifests[0]
    comparisons: list[dict[str, Any]] = []
    passed = True
    for index, manifest in enumerate(manifests[1:], start=2):
        differences, truncated = compare_manifests(
            baseline,
            manifest,
            tolerance,
            max_differences,
        )
        comparisons.append(
            {
                "baseline_run": 1,
                "compared_run": index,
                "passed": not differences,
                "differences": differences,
                "truncated": truncated,
            }
        )
        passed = passed and not differences

    result = {
        "version": 1,
        "passed": passed,
        "runs": runs,
        "numeric_tolerance": tolerance,
        "manifests": manifest_paths,
        "comparisons": comparisons,
    }

    output = resolve(str(config["output_file"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two or more clean Blender builds.")
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    try:
        result = check_reproducibility(
            args.workflow.resolve(),
            args.config.resolve(),
        )
    except (ReproducibilityError, KeyError, TypeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 2

    LOGGER.info("Reproducibility passed=%s", result["passed"])
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
