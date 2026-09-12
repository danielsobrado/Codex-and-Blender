from __future__ import annotations

import json

import bpy

from core.context import JobContext
from core.external_files import missing_external_files


def validate_scene(context: JobContext) -> None:
    acceptance = context.section("acceptance")
    structural = acceptance.get("structural", {})
    errors: list[str] = []
    warnings: list[str] = []

    required_objects = structural.get("required_objects", [])
    for name in required_objects:
        if bpy.data.objects.get(name) is None:
            errors.append(f"Required object is missing: {name}")

    if structural.get("require_active_camera", True) and bpy.context.scene.camera is None:
        errors.append("Scene has no active camera.")

    if structural.get("require_managed_collection", True):
        managed_name = context.section("scene")["managed_collection"]
        if bpy.data.collections.get(managed_name) is None:
            errors.append(f"Managed collection is missing: {managed_name}")

    missing = missing_external_files()
    max_missing = int(structural.get("max_missing_external_files", 0))
    if len(missing) > max_missing:
        errors.append(
            f"Missing external files: {len(missing)} exceeds configured maximum {max_missing}."
        )

    visual = acceptance.get("visual", {})
    if any(value is not None for value in visual.values()):
        warnings.append("Visual thresholds are configured but are not evaluated by the structural validator.")

    result = {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "required_objects": required_objects,
            "active_camera": bpy.context.scene.camera.name if bpy.context.scene.camera else None,
            "missing_external_files": missing,
        },
    }

    output = context.path("validation_file")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if errors:
        raise RuntimeError("Structural validation failed: " + "; ".join(errors))
