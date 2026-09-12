from __future__ import annotations

from typing import Any

import bpy

from core.context import JobContext


def configured_render_state(context: JobContext) -> dict[str, Any]:
    spec = context.section("render")
    return {
        "engine": str(spec["engine"]),
        "resolution_x": int(spec["resolution_x"]),
        "resolution_y": int(spec["resolution_y"]),
        "resolution_percentage": int(spec["resolution_percentage"]),
        "image_format": str(spec["image_format"]),
        "transparent": bool(spec["transparent"]),
    }


def current_render_state() -> dict[str, Any]:
    render = bpy.context.scene.render
    return {
        "engine": render.engine,
        "resolution_x": int(render.resolution_x),
        "resolution_y": int(render.resolution_y),
        "resolution_percentage": int(render.resolution_percentage),
        "image_format": render.image_settings.file_format,
        "transparent": bool(render.film_transparent),
    }


def configure_render(context: JobContext) -> None:
    expected = configured_render_state(context)
    render = bpy.context.scene.render
    render.engine = expected["engine"]
    render.resolution_x = expected["resolution_x"]
    render.resolution_y = expected["resolution_y"]
    render.resolution_percentage = expected["resolution_percentage"]
    render.image_settings.file_format = expected["image_format"]
    render.film_transparent = expected["transparent"]


def render_setting_errors(context: JobContext) -> list[str]:
    expected = configured_render_state(context)
    current = current_render_state()
    return [
        f"Render setting mismatch for {key}: expected {expected[key]!r}, got {current[key]!r}."
        for key in expected
        if current[key] != expected[key]
    ]
