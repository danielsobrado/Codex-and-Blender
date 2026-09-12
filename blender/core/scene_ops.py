from __future__ import annotations

from typing import Iterable

import bpy
from mathutils import Vector


def replace_collection(name: str) -> bpy.types.Collection:
    existing = bpy.data.collections.get(name)
    if existing:
        for obj in list(existing.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(existing)

    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def look_at(obj: bpy.types.Object, target: Iterable[float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_mesh_object(kind: str, name: str) -> bpy.types.Object:
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add()
    elif kind == "uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32)
    else:
        raise ValueError(f"Unsupported object type: {kind}")

    obj = bpy.context.active_object
    obj.name = name
    return obj


def configure_transform(
    obj: bpy.types.Object,
    location: Iterable[float],
    scale: Iterable[float],
) -> None:
    obj.location = tuple(float(value) for value in location)
    obj.scale = tuple(float(value) for value in scale)


def create_light(spec: dict, collection: bpy.types.Collection) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name=f"{spec['name']}_Data", type=spec["type"])
    light_data.energy = float(spec["energy"])
    if spec["type"] == "AREA":
        light_data.shape = "DISK"
        light_data.size = float(spec["size"])

    obj = bpy.data.objects.new(spec["name"], light_data)
    obj.location = tuple(float(value) for value in spec["location"])
    collection.objects.link(obj)

    target = spec.get("target")
    if target is not None:
        look_at(obj, target)
    return obj
