"""Deterministic, texture-independent foliage meshes and isolated glTF exports."""
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


class Mesh:
    def __init__(self, materials):
        self.vertices, self.faces, self.indices = [], [], []
        self.materials = materials

    def face(self, points, material):
        start = len(self.vertices)
        self.vertices.extend(points)
        self.faces.append(tuple(range(start, start + len(points))))
        self.indices.append(material)

    def leaf(self, base, direction, length, width, bend, material):
        base, direction = Vector(base), Vector(direction).normalized()
        side = direction.cross(Vector((0, 0, 1)))
        if side.length < .01:
            side = Vector((1, 0, 0))
        side.normalize()
        rows = []
        for t, w in [(0, .12), (.25, .85), (.55, 1), (.8, .6), (1, 0)]:
            center = base + direction * length * t + Vector((0, 0, -bend * t*t))
            rows.append((center-side*width*w/2, center+Vector((0,0,width*.13*w)), center+side*width*w/2))
        for a, b in zip(rows, rows[1:]):
            self.face([a[0], b[0], b[1], a[1]], material)
            self.face([a[1], b[1], b[2], a[2]], material)

    def branch(self, start, end, radius, material, sides=7, end_radius=None):
        start, end = Vector(start), Vector(end)
        axis = (end-start).normalized()
        u = axis.cross(Vector((0,1,0))).normalized()
        v = axis.cross(u)
        rings = [[p + r*(u*math.cos(i*math.tau/sides)+v*math.sin(i*math.tau/sides)) for i in range(sides)] for p,r in [(start,radius),(end,radius*.55 if end_radius is None else end_radius)]]
        for i in range(sides):
            j = (i+1)%sides
            self.face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]],material)
        self.face(list(reversed(rings[0])),material)
        self.face(rings[1],material)

    def pad(self, center, size, angle, material):
        c = Vector(center)
        u, v = Vector((math.cos(angle),math.sin(angle),0)), Vector((-math.sin(angle),math.cos(angle),0))
        rings = []
        for j in range(9):
            lat = math.pi*j/8
            rings.append([c + u*(size*.42*math.sin(lat)*math.cos(i*math.tau/12)) + v*(size*.12*math.sin(lat)*math.sin(i*math.tau/12)) + Vector((0,0,size*.5*math.cos(lat))) for i in range(12)])
        for a,b in zip(rings,rings[1:]):
            for i in range(12):
                k=(i+1)%12
                self.face([a[i],b[i],b[k],a[k]],material)
        for z in [-.25,0,.25]:
            for x in [-.22,0,.22]:
                p=c+u*(x*size)+Vector((0,0,z*size))+v*(size*.113)
                self.branch(p,p+v*size*.055+Vector((0,0,size*.025)),size*.007,8,4)

    def object(self, name, collection):
        mesh=bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices,[],self.faces)
        mesh.update()
        obj=bpy.data.objects.new(name,mesh)
        collection.objects.link(obj)
        for mat in self.materials:
            mesh.materials.append(mat)
        for poly,idx in zip(mesh.polygons,self.indices):
            poly.material_index=idx
        uv=mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            for n,loop in enumerate(poly.loop_indices):
                uv.data[loop].uv=((0,0),(0,1),(1,1),(1,0))[n%4]
        return obj


def make_asset(spec, materials, collection):
    rng=random.Random(spec['seed'])
    m=Mesh(materials)
    kind, height=spec['kind'],spec['height']
    if kind in ('grass','rosette'):
        for i in range(spec['count']):
            angle=rng.uniform(0,math.tau)
            r=rng.uniform(0,spec['radius']) if kind=='grass' else .025
            length=height*rng.uniform(.55,1.15)
            tilt=rng.uniform(.3,1.3) if kind=='grass' else rng.uniform(.55,1.8)
            m.leaf((r*math.cos(angle),r*math.sin(angle),0),(math.cos(angle)*tilt,math.sin(angle)*tilt,1),length,spec['width']*rng.uniform(.7,1.3),length*.18,rng.choice(spec['materials']))
    elif kind=='bush':
        for i in range(spec['count']):
            angle=rng.uniform(0,math.tau)
            end=Vector((math.cos(angle)*spec['radius']*rng.uniform(.35,1),math.sin(angle)*spec['radius']*rng.uniform(.35,1),height*rng.uniform(.48,.92)))
            start=Vector((0,0,.02))
            m.branch(start,end,height*.016,6)
            for j in range(6):
                t=.35+j*.11
                origin=start.lerp(end,t)
                a=angle+j*2.4
                tip=origin+Vector((math.cos(a)*height*.23,math.sin(a)*height*.23,height*.14))
                m.branch(origin,tip,height*.004,6,5)
                for k in range(7):
                    p=origin.lerp(tip,.2+k*.12)
                    la=a+(-1 if k%2 else 1)*.9
                    m.leaf(p,(math.cos(la),math.sin(la),rng.uniform(.1,.7)),height*rng.uniform(.12,.21),height*.037,height*.025,rng.choice(spec['materials']))
    elif kind=='cactus':
        m.branch((0,0,0),(0,0,height*.3),height*.07,6)
        for i in range(spec['count']):
            a=i*2.399+rng.uniform(-.3,.3)
            p=Vector((0,0,height*.18))
            for j in range(rng.randint(2,4)):
                size=height*rng.uniform(.22,.29)
                q=p+Vector((math.cos(a)*size*.35,math.sin(a)*size*.35,size*.65))
                m.pad(q,size,a,rng.choice(spec['materials']))
                p=q+Vector((0,0,size*.25))
    else:
        from jobs.tropical import add_tropical
        add_tropical(m, spec, rng)
    return m.object(spec['name'],collection)


def build_vegetation(context, collection):
    config=context.section('vegetation')
    materials=[]
    for name,color in config['palette'].items():
        mat=bpy.data.materials.new(name)
        mat.diffuse_color=(*color,1)
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*color,1)
        bsdf.inputs['Roughness'].default_value=.83
        mat.use_backface_culling=False
        materials.append(mat)
    directory=context.path('output_dir')/'objects'
    directory.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for i,spec in enumerate(config['assets']):
        obj=make_asset(spec,materials,collection)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active=obj
        bpy.context.view_layer.update()
        obj.asset_mark()
        obj.asset_data.description=f"Reference-inspired {spec['kind']}; meters; ground-centered pivot"
        path=directory/(obj.name+'.glb')
        bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_extras=True)
        manifest.append({'name':obj.name,'file':path.name,'dimensions_m':list(obj.dimensions),'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'bytes':path.stat().st_size,'seed':spec['seed']})
        obj.location=spec.get('display_location', ((i%4-1.5)*config['spacing'],(i//4-1)*config['spacing'],0))
        font=bpy.data.curves.new(obj.name+'_Label','FONT')
        font.body=spec['name'].replace('_',' ').upper()
        font.size=config.get('label_size', .115)
        font.align_x='CENTER'
        label=bpy.data.objects.new(obj.name+'_Label',font)
        collection.objects.link(label)
        label.location=(obj.location.x,obj.location.y-spec.get('label_offset', .97),.013)
    (directory/'manifest.json').write_text(json.dumps({'units':'meters','pivot':'ground center','materials':'embedded glTF PBR, double sided; no external textures','assets':manifest},indent=2),encoding='utf-8')
