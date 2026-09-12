from __future__ import annotations

import random
from typing import Any, Iterable

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


def _rock_lobe_specs(spec: dict[str, Any]) -> list[dict[str, Any]]:
    lobes = spec.get("lobes", 2)
    if isinstance(lobes, list):
        return lobes

    rng = random.Random(int(spec.get("seed", 1)))
    items = [{"radius": 1.0, "location": [0.0, 0.0, 0.0], "scale": [1.2, 1.05, 0.95]}]
    for _ in range(max(1, int(lobes) - 1)):
        items.append(
            {
                "radius": rng.uniform(0.75, 0.95),
                "location": [
                    rng.uniform(0.55, 0.9),
                    rng.uniform(-0.2, 0.35),
                    rng.uniform(-0.08, 0.12),
                ],
                "scale": [
                    rng.uniform(0.9, 1.1),
                    rng.uniform(0.85, 1.05),
                    rng.uniform(0.75, 0.95),
                ],
            }
        )
    return items


def _add_rock_lobe(spec: dict[str, Any], subdivisions: int) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=subdivisions,
        radius=float(spec.get("radius", 1.0)),
        location=tuple(float(value) for value in spec.get("location", (0.0, 0.0, 0.0))),
    )
    obj = bpy.context.active_object
    obj.scale = tuple(float(value) for value in spec.get("scale", (1.0, 1.0, 1.0)))
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    return obj


def create_rock_object(spec: dict[str, Any]) -> bpy.types.Object:
    subdivisions = int(spec.get("subdivisions", 3))
    lobes = _rock_lobe_specs(spec)
    if not lobes:
        raise ValueError("Rock objects need at least one lobe.")

    base = _add_rock_lobe(lobes[0], subdivisions)
    base.name = spec["name"]
    extras = [_add_rock_lobe(lobe, subdivisions) for lobe in lobes[1:]]

    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    for extra in extras:
        extra.select_set(False)
        modifier = base.modifiers.new(name=f"Union_{extra.name}", type="BOOLEAN")
        modifier.operation = "UNION"
        modifier.solver = "EXACT"
        modifier.object = extra
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(extra, do_unlink=True)

    remesh = base.modifiers.new(name="RockRemesh", type="REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = float(spec.get("voxel_size", 0.06))
    bpy.ops.object.modifier_apply(modifier=remesh.name)

    flatten = float(spec.get("flatten", 1.0))
    mesh = base.data
    if flatten != 1.0:
        for vertex in mesh.vertices:
            vertex.co.z *= flatten
        mesh.update()

    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return base


def create_mesh_object(spec: dict[str, Any]) -> bpy.types.Object:
    kind = spec["type"]
    if kind == "rock":
        return create_rock_object(spec)
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add()
    elif kind == "uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
    else:
        raise ValueError(f"Unsupported object type: {kind}")

    obj = bpy.context.active_object
    obj.name = spec["name"]
    return obj


def configure_transform(obj: bpy.types.Object, spec: dict[str, Any]) -> None:
    obj.location = tuple(float(value) for value in spec["location"])
    obj.scale = tuple(float(value) for value in spec["scale"])
    rotation = spec.get("rotation_euler")
    if rotation is not None:
        obj.rotation_euler = tuple(float(value) for value in rotation)
    if spec.get("sit_on_ground"):
        sit_on_ground(obj, float(spec.get("ground_z", 0.0)))


def sit_on_ground(obj: bpy.types.Object, ground_z: float = 0.0) -> None:
    bpy.context.view_layer.update()
    lowest = min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices)
    obj.location.z += ground_z - lowest


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
