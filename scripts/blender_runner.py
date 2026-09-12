from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger("blender_runner")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "workflow.yaml"
VALID_ACTIONS = ("build", "render", "inspect", "validate", "all")


class WorkflowError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise WorkflowError(f"Cannot read config: {path}") from exc
    except yaml.YAMLError as exc:
        raise WorkflowError(f"Invalid YAML: {path}") from exc

    if not isinstance(data, dict):
        raise WorkflowError(f"Config root must be a mapping: {path}")
    return data


def resolve_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else (ROOT / path).resolve()


def resolve_executable(config: dict[str, Any]) -> str:
    blender = config.get("blender", {})
    env_name = blender.get("executable_env", "BLENDER_BIN")
    return os.getenv(env_name) or blender.get("executable_default", "blender")


def prepare_runtime_config(config: dict[str, Any]) -> Path:
    paths = config["paths"]
    output_dir = resolve_path(paths["output_dir"])
    if output_dir is None:
        raise WorkflowError("paths.output_dir must be configured.")
    output_dir.mkdir(parents=True, exist_ok=True)

    runtime = json.loads(json.dumps(config))
    runtime["_root"] = str(ROOT)

    for key in (
        "output_dir",
        "blend_file",
        "render_file",
        "render_dir",
        "state_file",
        "validation_file",
        "resolved_config",
    ):
        resolved = resolve_path(paths[key])
        if resolved is None:
            raise WorkflowError(f"paths.{key} must be configured.")
        runtime["paths"][key] = str(resolved)

    acceptance_path = resolve_path(paths["acceptance_file"])
    if acceptance_path is None:
        raise WorkflowError("paths.acceptance_file must be configured.")
    runtime["acceptance"] = load_yaml(acceptance_path)
    runtime["paths"]["acceptance_file"] = str(acceptance_path)

    startup_file = resolve_path(runtime["blender"].get("startup_file"))
    runtime["blender"]["startup_file"] = str(startup_file) if startup_file else None

    entrypoint = resolve_path(runtime["blender"]["python_entrypoint"])
    if entrypoint is None or not entrypoint.exists():
        raise WorkflowError(f"Blender entrypoint does not exist: {entrypoint}")
    runtime["blender"]["python_entrypoint"] = str(entrypoint)

    resolved_config = Path(runtime["paths"]["resolved_config"])
    resolved_config.write_text(json.dumps(runtime, indent=2), encoding="utf-8")
    return resolved_config


def select_input_blend(config: dict[str, Any], action: str) -> Path | None:
    if action in ("render", "inspect", "validate"):
        generated = resolve_path(config["paths"]["blend_file"])
        if generated and generated.exists():
            return generated
    return resolve_path(config["blender"].get("startup_file"))


def build_command(config: dict[str, Any], runtime_config: Path, action: str) -> list[str]:
    blender = config["blender"]
    command = [resolve_executable(config), "--background"]

    input_blend = select_input_blend(config, action)
    if input_blend:
        if not input_blend.exists():
            raise WorkflowError(f"Input .blend does not exist: {input_blend}")
        command.append(str(input_blend))
    else:
        command.append("--factory-startup")

    entrypoint = resolve_path(blender["python_entrypoint"])
    if entrypoint is None:
        raise WorkflowError("blender.python_entrypoint must be configured.")

    command.extend(
        [
            "--python-exit-code",
            str(blender.get("python_exit_code", 1)),
            "--python",
            str(entrypoint),
            "--",
            "--action",
            action,
            "--config",
            str(runtime_config),
        ]
    )
    return command


def run_blender(config: dict[str, Any], action: str) -> None:
    runtime_config = prepare_runtime_config(config)
    command = build_command(config, runtime_config, action)
    LOGGER.info("Running Blender action '%s'.", action)

    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise WorkflowError(
            f"Blender executable was not found: {command[0]}. "
            "Set BLENDER_BIN or update config/workflow.yaml."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise WorkflowError(
            f"Blender action '{action}' failed with exit code {exc.returncode}."
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Blender agent workflow.")
    parser.add_argument("action", choices=VALID_ACTIONS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    try:
        config = load_yaml(args.config.resolve())
        run_blender(config, args.action)
    except (WorkflowError, KeyError, TypeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
