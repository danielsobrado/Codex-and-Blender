from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CODEX_EXECUTABLE = "codex"


class ModelReviewError(RuntimeError):
    pass


def resolve_path(value: str, root: Path = ROOT) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def display_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def collect_image_paths(
    render_index: dict[str, Any],
    reference_regression: dict[str, Any],
) -> list[Path]:
    current = [
        Path(str(view["path"]))
        for view in render_index.get("views", [])
        if Path(str(view["path"])).exists()
    ]
    if not current:
        raise ModelReviewError("No current render images are available for model review.")

    references: list[Path] = []
    if reference_regression.get("enabled", False):
        for view in reference_regression.get("views", []):
            path = Path(str(view["reference"]))
            if not path.exists():
                raise ModelReviewError(f"Approved reference image is missing: {path}")
            references.append(path)

    return [*current, *references]


def build_model_prompt(
    prompt_path: Path,
    render_index: dict[str, Any],
    state_path: Path,
    validation_path: Path,
    reference_regression: dict[str, Any],
    root: Path = ROOT,
) -> str:
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ModelReviewError(f"Cannot read visual review prompt: {prompt_path}") from exc

    current_lines = "\n".join(
        f"{index + 1}. {view['name']} ({view['role']})"
        for index, view in enumerate(render_index.get("views", []))
        if Path(str(view["path"])).exists()
    )

    reference_views = reference_regression.get("views", []) if reference_regression.get("enabled") else []
    reference_section = ""
    if reference_views:
        reference_lines = "\n".join(
            f"{index + 1}. approved reference for {view['name']} "
            f"(SSIM={view['ssim']}, threshold={view['ssim_min']})"
            for index, view in enumerate(reference_views)
        )
        reference_section = (
            "\nApproved reference images are attached after all current images in this exact order:\n"
            f"{reference_lines}\n"
            "Compare each current view with its named approved reference. Report meaningful visual "
            "regressions, but do not treat tiny renderer noise as a defect.\n"
        )

    return (
        f"{prompt}\n\n"
        "Exact scene evidence is available in these files:\n"
        f"- {display_path(state_path, root)}\n"
        f"- {display_path(validation_path, root)}\n\n"
        "Current render images are attached first in this exact order:\n"
        f"{current_lines}\n"
        f"{reference_section}\n"
        "Read the exact scene evidence before reviewing the images. Return only the "
        "schema-constrained evaluation."
    )


def load_result(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelReviewError("Codex did not produce valid model-review JSON.") from exc
    if not isinstance(value, dict):
        raise ModelReviewError("Codex model-review result must be a JSON object.")
    return value


def run_model_review(
    config: dict[str, Any],
    render_index: dict[str, Any],
    state_path: Path,
    validation_path: Path,
    reference_regression: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any]:
    if shutil.which(CODEX_EXECUTABLE) is None:
        raise ModelReviewError("Codex CLI was not found on PATH.")

    prompt_path = resolve_path(str(config["prompt_file"]), root)
    schema_path = resolve_path(str(config["output_schema_file"]), root)
    if not prompt_path.exists() or not schema_path.exists():
        raise ModelReviewError("Visual review prompt or output schema is missing.")

    image_paths = collect_image_paths(render_index, reference_regression)
    prompt = build_model_prompt(
        prompt_path,
        render_index,
        state_path,
        validation_path,
        reference_regression,
        root,
    )

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
            cwd=root,
            input=prompt,
            text=True,
            check=True,
        )
        return load_result(result_path)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ModelReviewError("Codex visual review failed.") from exc
    finally:
        result_path.unlink(missing_ok=True)
