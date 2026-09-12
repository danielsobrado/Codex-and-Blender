from __future__ import annotations

import logging

import bpy

from core.context import JobContext

LOGGER = logging.getLogger("render_scene")


def configure_render(context: JobContext) -> None:
    spec = context.section("render")
    scene = bpy.context.scene

    scene.render.engine = spec["engine"]
    scene.render.resolution_x = int(spec["resolution_x"])
    scene.render.resolution_y = int(spec["resolution_y"])
    scene.render.resolution_percentage = int(spec["resolution_percentage"])
    scene.render.image_settings.file_format = spec["image_format"]
    scene.render.film_transparent = bool(spec["transparent"])


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
