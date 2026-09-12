"""Bake reusable small-leaf sprays from the supplied leaf atlas in Blender."""
import math
import random
import bpy
from mathutils import Vector


def bake_canopy_atlas(root, spec):
    from jobs.forest import Surface

    original = bpy.context.window.scene
    scene = bpy.data.scenes.new('CanopyAtlasBake')
    bpy.context.window.scene = scene
    created_materials = []
    try:
        texture = bpy.data.images.load(str(root / 'output/textures/shrub_leaf_atlas.png'), check_existing=True)
        for i, tint in enumerate(spec['tints']):
            mat = bpy.data.materials.new(f'AtlasLeaf_{i}')
            mat.use_nodes = True
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            nodes.clear()
            image = nodes.new('ShaderNodeTexImage')
            image.image = texture
            multiply = nodes.new('ShaderNodeMixRGB')
            multiply.blend_type = 'MULTIPLY'
            multiply.inputs[0].default_value = 1
            multiply.inputs[2].default_value = (*tint, 1)
            links.new(image.outputs['Color'], multiply.inputs[1])
            emission = nodes.new('ShaderNodeEmission')
            links.new(multiply.outputs[0], emission.inputs[0])
            transparent = nodes.new('ShaderNodeBsdfTransparent')
            mix = nodes.new('ShaderNodeMixShader')
            links.new(image.outputs['Alpha'], mix.inputs[0])
            links.new(transparent.outputs[0], mix.inputs[1])
            links.new(emission.outputs[0], mix.inputs[2])
            output = nodes.new('ShaderNodeOutputMaterial')
            links.new(mix.outputs[0], output.inputs[0])
            created_materials.append(mat)
        twig = bpy.data.materials.new('AtlasTwig')
        twig.use_nodes = True
        p = twig.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value = (*spec['twig_color'], 1)
        p.inputs['Emission Color'].default_value = (*spec['twig_color'], 1)
        p.inputs['Emission Strength'].default_value = 1
        created_materials.append(twig)
        rng = random.Random(spec['seed'])
        for cell in range(4):
            mesh = Surface(created_materials)
            root_point = Vector((0, -.7, -.025))
            for arm in range(spec['arms']):
                angle = math.pi * .5 + (arm / (spec['arms'] - 1) - .5) * 2.6
                end = root_point + Vector((math.cos(angle), math.sin(angle), 0)) * rng.uniform(.95, 1.35)
                mesh.tube([root_point, root_point.lerp(end, .55), end], [.012, .009, .002], len(created_materials) - 1)
                for leaf in range(spec['leaves_per_arm']):
                    t = .18 + .79 * leaf / (spec['leaves_per_arm'] - 1)
                    at = root_point.lerp(end, t) + Vector((0, 0, .015 + leaf * .003))
                    a = angle + (-1 if leaf % 2 else 1) * rng.uniform(.5, 1.25)
                    mesh.card(at, a, rng.uniform(*spec['leaf_length']), rng.uniform(*spec['leaf_width']), 0, 0,
                              rng.choice(spec['leaf_cells']), (4, 4), rng.randrange(len(spec['tints'])), fold=0, segments=1)
            obj = mesh.object(f'Spray_{cell}', scene.collection)
            points = [v.co for v in obj.data.vertices]
            lo = Vector(tuple(min(v[i] for v in points) for i in range(3)))
            hi = Vector(tuple(max(v[i] for v in points) for i in range(3)))
            factor = 1.82 / max(hi.x - lo.x, hi.y - lo.y)
            center = (lo + hi) * .5
            offset = Vector((-1 + 2 * (cell % 2), 1 - 2 * (cell // 2), 0))
            for v in obj.data.vertices:
                v.co = (v.co - center) * factor + offset
        camera_data = bpy.data.cameras.new('AtlasCamera')
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = 4
        camera = bpy.data.objects.new('AtlasCamera', camera_data)
        scene.collection.objects.link(camera)
        camera.location = (0, 0, 10)
        scene.camera = camera
        scene.render.engine = 'BLENDER_EEVEE'
        scene.render.resolution_x = scene.render.resolution_y = spec['resolution']
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.view_settings.view_transform = 'Standard'
        scene.render.filepath = str(root / 'output/textures/canopy_branch_atlas.png')
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.context.window.scene = original
        for obj in list(scene.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
        bpy.data.scenes.remove(scene)
        for mat in created_materials:
            bpy.data.materials.remove(mat)
