from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VALID_MODES = {"report_only", "gate"}


class ReferenceRegressionError(RuntimeError):
    pass


def resolve_path(value: str, root: Path = ROOT) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def load_backend():
    try:
        import numpy as np
        from skimage.metrics import structural_similarity
    except ImportError as exc:
        raise ReferenceRegressionError(
            "Reference regression requires requirements-reference.txt."
        ) from exc
    return np, structural_similarity


def ssim_score(current_path: Path, reference_path: Path) -> float:
    if not current_path.exists():
        raise ReferenceRegressionError(f"Current render is missing: {current_path}")
    if not reference_path.exists():
        raise ReferenceRegressionError(f"Reference render is missing: {reference_path}")

    try:
        with Image.open(current_path) as current_image, Image.open(reference_path) as reference_image:
            current = current_image.convert("RGB")
            reference = reference_image.convert("RGB")
            if current.size != reference.size:
                raise ReferenceRegressionError(
                    f"Reference dimensions {reference.size} do not match current render {current.size}."
                )

            np, structural_similarity = load_backend()
            current_array = np.asarray(current, dtype=np.uint8)
            reference_array = np.asarray(reference, dtype=np.uint8)
    except ReferenceRegressionError:
        raise
    except (OSError, ValueError) as exc:
        raise ReferenceRegressionError("Cannot read current/reference render pair.") from exc

    score = structural_similarity(
        reference_array,
        current_array,
        channel_axis=-1,
        data_range=255,
    )
    return float(score)


def validate_threshold(value: Any, view_name: str) -> float | None:
    if value is None:
        return None
    try:
        threshold = float(value)
    except (TypeError, ValueError) as exc:
        raise ReferenceRegressionError(
            f"Invalid SSIM threshold for {view_name}: {value!r}"
        ) from exc
    if not -1.0 <= threshold <= 1.0:
        raise ReferenceRegressionError(
            f"SSIM threshold for {view_name} must be between -1 and 1."
        )
    return threshold


def evaluate_reference_regression(
    render_index: dict[str, Any],
    config: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any]:
    enabled = bool(config.get("enabled", False))
    mode = str(config.get("mode", "report_only"))
    if mode not in VALID_MODES:
        raise ReferenceRegressionError(
            f"reference_regression.mode must be one of {sorted(VALID_MODES)}."
        )

    if not enabled:
        return {
            "enabled": False,
            "mode": mode,
            "passed": True,
            "thresholds_passed": None,
            "views": [],
        }

    configured_views = config.get("views", [])
    if not isinstance(configured_views, list) or not configured_views:
        raise ReferenceRegressionError(
            "Enabled reference regression requires at least one configured view."
        )

    current_views = {str(view["name"]): view for view in render_index.get("views", [])}
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    thresholds_passed = True

    for spec in configured_views:
        if not isinstance(spec, dict) or not spec.get("name") or not spec.get("reference"):
            raise ReferenceRegressionError(
                "Each reference regression view requires name and reference."
            )

        name = str(spec["name"])
        if name in seen:
            raise ReferenceRegressionError(f"Duplicate reference regression view: {name}")
        seen.add(name)

        current_view = current_views.get(name)
        if current_view is None:
            raise ReferenceRegressionError(
                f"Reference regression view is not in the render index: {name}"
            )

        threshold = validate_threshold(spec.get("ssim_min"), name)
        if mode == "gate" and threshold is None:
            raise ReferenceRegressionError(
                f"Gate mode requires ssim_min for reference view {name}."
            )

        current_path = Path(str(current_view["path"]))
        reference_path = resolve_path(str(spec["reference"]), root)
        score = ssim_score(current_path, reference_path)
        meets_threshold = None if threshold is None else score >= threshold
        if meets_threshold is False:
            thresholds_passed = False

        results.append(
            {
                "name": name,
                "current": str(current_path),
                "reference": str(reference_path),
                "ssim": round(score, 6),
                "ssim_min": threshold,
                "meets_threshold": meets_threshold,
            }
        )

    return {
        "enabled": True,
        "mode": mode,
        "passed": thresholds_passed if mode == "gate" else True,
        "thresholds_passed": thresholds_passed,
        "views": results,
    }
