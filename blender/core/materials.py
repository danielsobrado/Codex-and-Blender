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

    noise_scale = spec.get("noise_scale")
    if noise_scale is not None:
        tree = material.node_tree
        noise = tree.nodes.new("ShaderNodeTexNoise")
        noise.location = (-400, 200)
        noise.inputs["Scale"].default_value = float(noise_scale)
        noise.inputs["Detail"].default_value = float(spec.get("noise_detail", 4.0))
        mix = tree.nodes.new("ShaderNodeMix")
        mix.location = (-180, 180)
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = float(spec.get("noise_strength", 0.22))
        mix.inputs["A"].default_value = spec["base_color"]
        mix.inputs["B"].default_value = (
            spec["base_color"][0] * 0.72,
            spec["base_color"][1] * 0.72,
            spec["base_color"][2] * 0.72,
            1.0,
        )
        tree.links.new(noise.outputs["Fac"], mix.inputs["Factor"])
        tree.links.new(mix.outputs["Result"], node.inputs["Base Color"])
    return material
