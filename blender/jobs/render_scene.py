from __future__ import annotations

import logging

import bpy

from core.context import JobContext
from core.rendering import configure_render

LOGGER = logging.getLogger("render_scene")


def render_to(path, camera: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.camera = camera
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    LOGGER.info("Rendered %s with %s.", path, camera.name)


def render_scene(context: JobContext) -> None:
    configure_render(context)
    cameras = context.list_section("cameras")
    primary_spec = next((spec for spec in cameras if spec.get("primary", False)), None)
    if primary_spec is None:
        raise ValueError("No primary camera configured.")

    primary = bpy.data.objects.get(primary_spec["name"])
    if primary is None or primary.type != "CAMERA":
        raise ValueError(f"Primary camera is missing: {primary_spec['name']}")

    render_to(context.path("render_file"), primary)

    if not context.section("render").get("render_review_cameras", True):
        return

    review_dir = context.path("render_dir")
    for spec in cameras:
        if spec.get("primary", False):
            continue
        camera = bpy.data.objects.get(spec["name"])
        if camera is None or camera.type != "CAMERA":
            raise ValueError(f"Review camera is missing: {spec['name']}")
        render_to(review_dir / f"{spec['name']}.png", camera)

    bpy.context.scene.camera = primary
