from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CODEX_EXECUTABLE = "codex"
SUPPORTED_PROVIDERS = {"codex", "grok"}
REVIEW_ISSUE_KEYS = (
    "view",
    "category",
    "severity",
    "confidence",
    "description",
    "evidence",
    "source_hint",
)


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


def attachment_plan(
    render_index: dict[str, Any],
    reference_regression: dict[str, Any],
) -> dict[str, Any]:
    current: list[dict[str, Any]] = []
    for view in render_index.get("views", []):
        path = Path(str(view["path"]))
        if not path.exists():
            continue
        current.append(
            {
                "kind": "current",
                "name": str(view["name"]),
                "role": str(view.get("role", "unspecified")),
                "path": path,
            }
        )
    if not current:
        raise ModelReviewError("No current render images are available for model review.")

    references: list[dict[str, Any]] = []
    if reference_regression.get("enabled", False):
        for view in reference_regression.get("views", []):
            path = Path(str(view["reference"]))
            if not path.exists():
                raise ModelReviewError(f"Approved reference image is missing: {path}")
            references.append(
                {
                    "kind": "reference",
                    "name": str(view["name"]),
                    "path": path,
                    "ssim": view.get("ssim"),
                    "ssim_min": view.get("ssim_min"),
                }
            )

    attachments = [*current, *references]
    for index, item in enumerate(attachments, start=1):
        item["index"] = index

    reference_by_name = {item["name"]: item for item in references}
    pairings: list[dict[str, Any]] = []
    for current_item in current:
        reference_item = reference_by_name.get(current_item["name"])
        if reference_item is None:
            continue
        pairings.append(
            {
                "name": current_item["name"],
                "current_index": current_item["index"],
                "reference_index": reference_item["index"],
            }
        )

    return {
        "current": current,
        "references": references,
        "attachments": attachments,
        "pairings": pairings,
    }


def collect_image_paths(
    render_index: dict[str, Any],
    reference_regression: dict[str, Any],
) -> list[Path]:
    plan = attachment_plan(render_index, reference_regression)
    return [item["path"] for item in plan["attachments"]]


def format_attachment_prompt(plan: dict[str, Any]) -> str:
    current_lines = "\n".join(
        f"{item['index']}. {item['name']} ({item['role']})" for item in plan["current"]
    )
    sections = [
        "CURRENT images are attached in this exact order:",
        current_lines,
    ]
    if plan["references"]:
        reference_lines = "\n".join(
            f"{item['index']}. {item['name']} "
            f"(SSIM={item['ssim']}, threshold={item['ssim_min']})"
            for item in plan["references"]
        )
        pairing_lines = "\n".join(
            f"{item['current_index']} ↔ {item['reference_index']} {item['name']}"
            for item in plan["pairings"]
        )
        sections.extend(
            [
                "",
                "REFERENCE images are attached after all current images in this exact order:",
                reference_lines,
                "",
                "Pairings:",
                pairing_lines,
                "",
                "Compare each current view only with its paired approved reference. Report "
                "meaningful visual regressions, but do not treat tiny renderer noise as a defect.",
            ]
        )
    return "\n".join(sections)


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

    plan = attachment_plan(render_index, reference_regression)
    evidence = [
        f"- {display_path(state_path, root)}",
        f"- {display_path(validation_path, root)}",
    ]
    if reference_regression.get("enabled"):
        evidence.append("- reference_regression results in the evaluation payload")

    return (
        f"{prompt}\n\n"
        "Exact scene evidence is available in these files:\n"
        + "\n".join(evidence)
        + "\n\n"
        + format_attachment_prompt(plan)
        + "\n\n"
        "Do not infer the image mapping. Use the numbered attachments and pairings above. "
        "Read the exact scene evidence before reviewing the images. Return only the "
        "schema-constrained evaluation."
    )


def validate_model_review_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelReviewError("Model-review result must be a JSON object.")

    required = ("passed", "score", "summary", "issues", "strengths")
    missing = [key for key in required if key not in value]
    if missing:
        raise ModelReviewError(
            "Model-review JSON is missing required keys: " + ", ".join(missing)
        )
    if not isinstance(value["passed"], bool):
        raise ModelReviewError("Model-review field 'passed' must be a boolean.")
    if not isinstance(value["score"], int) or not 0 <= value["score"] <= 100:
        raise ModelReviewError("Model-review field 'score' must be an integer from 0 to 100.")
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        raise ModelReviewError("Model-review field 'summary' must be a non-empty string.")
    if not isinstance(value["issues"], list):
        raise ModelReviewError("Model-review field 'issues' must be an array.")
    if not isinstance(value["strengths"], list):
        raise ModelReviewError("Model-review field 'strengths' must be an array.")

    for issue in value["issues"]:
        if not isinstance(issue, dict):
            raise ModelReviewError("Each model-review issue must be an object.")
        missing_issue = [key for key in REVIEW_ISSUE_KEYS if key not in issue]
        if missing_issue:
            raise ModelReviewError(
                "Model-review issue is missing required keys: " + ", ".join(missing_issue)
            )

    extra = sorted(set(value) - set(required))
    if extra:
        raise ModelReviewError(
            "Model-review JSON has unsupported keys: " + ", ".join(extra)
        )
    return value


def load_result(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelReviewError("Model review did not produce valid JSON.") from exc
    return validate_model_review_result(value)


def configured_provider(config: dict[str, Any]) -> str:
    provider = str(config.get("provider", "codex"))
    if provider not in SUPPORTED_PROVIDERS:
        raise ModelReviewError(
            f"Unknown model_review.provider {provider!r}; "
            f"supported: {sorted(SUPPORTED_PROVIDERS)}"
        )
    return provider


def run_codex_cli_review(
    config: dict[str, Any],
    image_paths: list[Path],
    prompt: str,
    schema_path: Path,
    root: Path,
) -> dict[str, Any]:
    executable = str(config.get("cli_executable") or CODEX_EXECUTABLE)
    if shutil.which(executable) is None and not Path(executable).exists():
        raise ModelReviewError(f"Review CLI was not found: {executable}")

    command = [
        executable,
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
        raise ModelReviewError("CLI visual review failed.") from exc
    finally:
        result_path.unlink(missing_ok=True)


def run_model_review(
    config: dict[str, Any],
    render_index: dict[str, Any],
    state_path: Path,
    validation_path: Path,
    reference_regression: dict[str, Any],
    root: Path = ROOT,
    review_json_path: Path | None = None,
) -> dict[str, Any]:
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

    if review_json_path is not None:
        return load_result(review_json_path)

    provider = configured_provider(config)
    if provider == "codex":
        return run_codex_cli_review(config, image_paths, prompt, schema_path, root)
    if provider == "grok":
        if config.get("cli_executable"):
            return run_codex_cli_review(config, image_paths, prompt, schema_path, root)
        raise ModelReviewError(
            "Grok provider does not use HTTP APIs or API keys. Pass --model-review-json "
            "from the Codex/Cursor console, or set model_review.cli_executable for a local CLI."
        )
    raise ModelReviewError(f"Unknown model_review.provider: {provider}")
