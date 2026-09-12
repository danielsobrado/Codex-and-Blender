from __future__ import annotations

import bpy

from core.context import JobContext
from core.materials import create_principled_material
from core.scene_ops import (
    configure_transform,
    create_light,
    create_mesh_object,
    look_at,
    move_to_collection,
    replace_collection,
)


def configure_world(context: JobContext) -> None:
    color = context.section("scene")["world_color"]
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = color[:3]


def build_objects(context: JobContext, collection: bpy.types.Collection) -> None:
    for spec in context.section("scene")["objects"]:
        obj = create_mesh_object(spec["type"], spec["name"])
        configure_transform(obj, spec["location"], spec["scale"])
        move_to_collection(obj, collection)

        material = create_principled_material(f"{spec['name']}_Material", spec["material"])
        obj.data.materials.clear()
        obj.data.materials.append(material)


def build_cameras(context: JobContext, collection: bpy.types.Collection) -> None:
    primary = None

    for spec in context.list_section("cameras"):
        camera_data = bpy.data.cameras.new(f"{spec['name']}_Data")
        camera_data.lens = float(spec["focal_length_mm"])

        camera = bpy.data.objects.new(spec["name"], camera_data)
        camera.location = tuple(float(value) for value in spec["location"])
        collection.objects.link(camera)
        look_at(camera, spec["target"])

        if spec.get("primary", False):
            if primary is not None:
                raise ValueError("Only one camera may be configured as primary.")
            primary = camera

    if primary is None:
        raise ValueError("One camera must be configured as primary.")
    bpy.context.scene.camera = primary


def build_lights(context: JobContext, collection: bpy.types.Collection) -> None:
    for spec in context.config.get("lights", []):
        create_light(spec, collection)


def build_scene(context: JobContext) -> None:
    scene_spec = context.section("scene")
    collection = replace_collection(scene_spec["managed_collection"])
    configure_world(context)
    build_objects(context, collection)
    build_cameras(context, collection)
    build_lights(context, collection)
