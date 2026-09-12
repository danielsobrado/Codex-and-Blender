from __future__ import annotations

import json

import bpy

from core.context import JobContext
from core.external_files import missing_external_files


def vector(values) -> list[float]:
    return [round(float(value), 6) for value in values]


def object_state(obj: bpy.types.Object) -> dict:
    state = {
        "name": obj.name,
        "type": obj.type,
        "location": vector(obj.location),
        "rotation_euler": vector(obj.rotation_euler),
        "scale": vector(obj.scale),
        "dimensions": vector(obj.dimensions),
        "visible_render": not obj.hide_render,
        "collections": sorted(collection.name for collection in obj.users_collection),
    }

    if obj.type == "MESH":
        state["mesh"] = {
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "polygons": len(obj.data.polygons),
            "materials": [material.name for material in obj.data.materials if material],
        }
    return state


def inspect_scene(context: JobContext) -> None:
    scene = bpy.context.scene
    objects = [object_state(obj) for obj in sorted(scene.objects, key=lambda item: item.name)]

    state = {
        "scene": scene.name,
        "blender_version": bpy.app.version_string,
        "render_engine": scene.render.engine,
        "active_camera": scene.camera.name if scene.camera else None,
        "object_count": len(objects),
        "objects": objects,
        "missing_external_files": missing_external_files(),
    }

    output = context.path("state_file")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(state, indent=2), encoding="utf-8")
