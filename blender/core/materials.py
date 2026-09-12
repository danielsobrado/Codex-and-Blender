from __future__ import annotations

from typing import Any

import bpy


def create_principled_material(name: str, spec: dict[str, Any]) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    material.use_nodes = True

    node = material.node_tree.nodes.get("Principled BSDF")
    if node is None:
        raise RuntimeError(f"Material '{name}' has no Principled BSDF node.")

    node.inputs["Base Color"].default_value = spec["base_color"]
    node.inputs["Roughness"].default_value = float(spec["roughness"])
    node.inputs["Metallic"].default_value = float(spec["metallic"])
    return material
