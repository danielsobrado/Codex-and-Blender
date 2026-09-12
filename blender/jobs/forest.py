"""Texture-atlas foliage, linked instances and portable jungle scene export."""
import json
import math
import random
from pathlib import Path
import bpy
from mathutils import Vector
from jobs.vegetation import Mesh


class Surface(Mesh):
    def __init__(self, materials):
        super().__init__(materials)
        self.uvs=[]
        self.normals=[]

    def polygon(self, points, uvs, material, normals=None):
        self.face(points,material)
        self.uvs.extend(uvs)
        normal=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0])).normalized()
        self.normals.extend(normals if normals is not None else [normal]*len(points))

    def canopy_card(self, center, normal, size, cell, crown_center):
        center,normal=Vector(center),Vector(normal).normalized()
        u=normal.cross(Vector((0,0,1)))
        if u.length<.01:
            u=Vector((1,0,0))
        u.normalize()
        v=normal.cross(u).normalized()
        for x0,x1 in [(-.5,0),(0,.5)]:
            for y0,y1 in [(-.5,0),(0,.5)]:
                points=[]
                uvs=[]
                normals=[]
                for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:
                    point=center+size*(u*x+v*y+normal*(.12-.24*(x*x+y*y)))
                    points.append(point)
                    uvs.append(((cell%2+.025+.95*(x+.5))/2,(1-cell//2+.025+.95*(y+.5))/2))
                    outward=(point-Vector(crown_center)).normalized()
                    normals.append((outward*.45+Vector((0,0,.75))).normalized())
                self.polygon(points,uvs,6,normals)

    def card(self, origin, angle, length, width, rise, bend, cell, grid, material, fold=0.12, segments=4):
        origin=Vector(origin)
        forward=Vector((math.cos(angle),math.sin(angle),0))
        side=Vector((-math.sin(angle),math.cos(angle),0))
        cols,rows=grid
        col,row=cell%cols,cell//cols
        u0,u1=(col+.015)/cols,(col+.985)/cols
        v0,v1=1-(row+.985)/rows,1-(row+.015)/rows
        for j in range(segments):
            a,b=j/segments,(j+1)/segments
            for left,right in [(-1,0),(0,1)]:
                points=[]
                uvs=[]
                for t,sign in [(a,left),(b,left),(b,right),(a,right)]:
                    ridge=width*fold*math.sin(math.pi*t)*(1-abs(sign))
                    p=origin+forward*length*t+Vector((0,0,length*(rise*t-bend*t*t)+ridge))+side*width*sign/2
                    points.append(p)
                    uvs.append((u0+(u1-u0)*(sign+1)/2,v0+(v1-v0)*t))
                self.polygon(points,uvs,material)

    def tube(self, points, radii, material):
        points=[Vector(p) for p in points]
        rings=[]
        for j,p in enumerate(points):
            tangent=(points[min(j+1,len(points)-1)]-points[max(j-1,0)]).normalized()
            ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
            u=tangent.cross(ref).normalized()
            v=tangent.cross(u).normalized()
            rings.append([p+radii[j]*(u*math.cos(i*math.tau/10)+v*math.sin(i*math.tau/10)) for i in range(10)])
        for j in range(len(points)-1):
            for i in range(10):
                k=(i+1)%10
                corners=[rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]]
                normals=[(rings[a][b]-points[a]).normalized() for a,b in [(j,i),(j,k),(j+1,k),(j+1,i)]]
                self.polygon(corners,[(i/10,j*.35),((i+1)/10,j*.35),((i+1)/10,(j+1)*.35),(i/10,(j+1)*.35)],material,normals)

    def split_leaf(self,origin,angle,length,width,cell):
        origin=Vector(origin)
        forward=Vector((math.cos(angle),math.sin(angle),0))
        side=Vector((-math.sin(angle),math.cos(angle),0))
        def point(t,s):
            return origin+forward*length*t+side*width*s*.5+Vector((0,0,length*(.4*t-.55*t*t)+width*.14*(1-abs(s))*math.sin(math.pi*t)))
        def quad(a,b,l,r):
            params=[(a,l),(b,l),(b,r),(a,r)]
            self.polygon([point(t,s) for t,s in params],[((cell+(s+1)*.5)/4,.5+.5*t) for t,s in params],1)
        for j in range(8):
            quad(j/8,(j+1)/8,-.18,.18)
        for a,b in [(.06,.21),(.24,.40),(.43,.59),(.62,.77),(.80,.96)]:
            quad(a,b,-1,-.18)
            quad(a,b,.18,1)

    def object(self,name,collection):
        obj=super().object(name,collection)
        for loop,uv in zip(obj.data.uv_layers.active.data,self.uvs):
            loop.uv=uv
        for polygon in obj.data.polygons:
            polygon.use_smooth=True
        obj.data.normals_split_custom_set(self.normals)
        return obj


def material(root,name,alpha,tint=None):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.use_backface_culling=False
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    p=nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value=.9
    tex=nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(root/'output/textures'/f'{name}.png'),check_existing=True)
    tex.image.pack()
    links.new(tex.outputs['Color'],p.inputs['Base Color'])
    if tint:
        multiply=nodes.new('ShaderNodeMix')
        multiply.data_type='RGBA'
        multiply.blend_type='MULTIPLY'
        multiply.inputs[0].default_value=1
        multiply.inputs[7].default_value=(*tint,1)
        links.new(tex.outputs['Color'],multiply.inputs[6])
        links.new(multiply.outputs[2],p.inputs['Base Color'])
    if alpha=='blend':
        links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
        mat.surface_render_method='BLENDED'
    elif alpha:
        cutoff=nodes.new('ShaderNodeMath')
        cutoff.operation='GREATER_THAN'
        cutoff.inputs[1].default_value=.4
        links.new(tex.outputs['Alpha'],cutoff.inputs[0])
        links.new(cutoff.outputs[0],p.inputs['Alpha'])
    return mat


def elevation(x,y):
    return .065*(y+10)+.36*math.sin(x*.15)*math.cos(y*.12)+.12*math.sin(y*.3)


def prototype(kind,materials,collection,rng,spec):
    from jobs.forest_plants import populate
    m=Surface(materials)
    populate(m,kind,rng,spec)
    return m.object(kind,collection)


def build_forest(context,collection):
    root=Path(context.config['_root'])
    spec=context.section('forest')
    rng=random.Random(spec['seed'])
    from jobs.forest_atlas import bake_canopy_atlas
    bake_canopy_atlas(root,spec['canopy_atlas'])
    mats=[material(root,n,alpha,spec['bark_tint'] if n=='palm_bark_basecolor' else None) for n,alpha in [(spec['surface_textures']['grass'],True),('tropical_leaf_atlas',True),('palm_fern_atlas',True),('shrub_leaf_atlas',True),('palm_bark_basecolor',False)]]
    stems=bpy.data.materials.new('Living_stems')
    stems.use_nodes=True
    stems.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*spec['stem_color'],1)
    stems.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.85
    mats.append(stems)
    mats.append(material(root,'canopy_branch_atlas',True))
    soil=material(root,spec['surface_textures']['ground'],False)
    terrain=Surface([soil])
    size=spec['extent']
    for x in range(-size,size):
        for y in range(-size,size):
            coords=[(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
            tile=spec['surface_textures']['tile_meters']
            terrain.polygon([(a,b,elevation(a,b)) for a,b in coords],[(a/tile,b/tile) for a,b in coords],0)
    backdrop=spec['distant_understory']
    for x in range(*backdrop['terrain_x'],2):
        for y in range(size,backdrop['terrain_end_y'],2):
            coords=[(x,y),(x+2,y),(x+2,y+2),(x,y+2)]
            terrain.polygon([(a,b,elevation(a,b)) for a,b in coords],[(a/tile,b/tile) for a,b in coords],0)
    terrain.object('ForestFloor',collection)
    path_material=material(root,spec['surface_textures']['path'],'blend')
    trail=Surface([path_material])
    step=spec['surface_textures']['path_step']
    half=spec['surface_textures']['path_half_width']
    for i in range(round(size*2/step)):
        a=-size+i*step
        b=a+step
        coords=[(1.8*math.sin(a*.11)-half,a),(1.8*math.sin(a*.11)+half,a),(1.8*math.sin(b*.11)+half,b),(1.8*math.sin(b*.11)-half,b)]
        trail.polygon([(x,y,elevation(x,y)+.025) for x,y in coords],[(0,a/tile),(1,a/tile),(1,b/tile),(0,b/tile)],0)
    trail.object('ForestPath',collection)
    counts={}
    asset_dir=context.path('output_dir')/'objects'
    asset_dir.mkdir(parents=True,exist_ok=True)
    assets=[]
    prototypes={}
    tree_positions=[]
    for kind,params in spec['plants'].items():
        variants=[]
        for variant in range(params['variants']):
            asset_name=f'{kind}_{variant+1:02}'
            group=bpy.data.objects.new(f'{asset_name}_instances',None)
            collection.objects.link(group)
            proto=prototype(kind,mats,collection,random.Random(spec['seed']+len(assets)*37),dict(params,variant=variant))
            proto.name=asset_name
            bpy.context.view_layer.update()
            bpy.ops.object.select_all(action='DESELECT')
            proto.select_set(True)
            bpy.context.view_layer.objects.active=proto
            proto.asset_mark()
            filename=asset_name+'.glb'
            bpy.ops.export_scene.gltf(filepath=str(asset_dir/filename),export_format='GLB',use_selection=True,export_yup=True,export_image_format='WEBP',export_image_quality=88)
            assets.append({'name':asset_name,'file':filename,'dimensions_m':list(proto.dimensions),'triangles':sum(len(p.vertices)-2 for p in proto.data.polygons)})
            variants.append((proto,group))
        prototypes[kind]=variants
        for i in range(params['count']):
            x,y=rng.uniform(-size+1,size-1),rng.uniform(-size+1,size-1)
            if kind=='background_tree':
                x,y=rng.uniform(*params['x_range']),rng.uniform(*params['y_range'])
            path=1.8*math.sin(y*.11)
            center=spec['clearing']['center']
            clear=math.hypot(x-center[0],y-center[1])<spec['clearing']['radius']
            if abs(x-path)<spec['path_width'] and y<19 and (kind!='groundcover' or rng.random()<.7):
                continue
            if clear and kind not in ('groundcover','grass') and rng.random()<.97:
                continue
            if kind in ('palm','tree') and (y< -3 or (y<10 and abs(x-path)<4)):
                continue
            if kind in ('tree','background_tree'):
                if any(math.hypot(x-a,y-b)<params['spacing'] for a,b in tree_positions):
                    continue
                if y<spec['canopy_opening']['end_y'] and abs(x-path)<spec['canopy_opening']['half_width']:
                    continue
            if kind in ('shrub','broadleaf') and (y<-9 or (y<4 and abs(x-path)<2.3)):
                continue
            if kind=='grass' and rng.random()>(.82+.17*math.sin(x*.7)*math.cos(y*.45)):
                continue
            if any(math.hypot(x-c['location'][0],y-c['location'][1])<(3 if kind in ('tree','palm') else 1.2) for c in context.config['cameras']):
                continue
            proto,group=rng.choice(variants)
            obj=bpy.data.objects.new(f'{kind}_{i:04}',proto.data)
            collection.objects.link(obj)
            obj.parent=group
            obj.location=(x,y,elevation(x,y))
            if kind in ('tree','background_tree'):
                tree_positions.append((x,y))
            if kind in ('vine','climber'):
                anchors=[a for a in collection.objects if a.name.startswith('tree_') and a.type=='MESH' and a.parent is not None]
                if not anchors:
                    raise ValueError('Vines require trees to be generated first.')
                anchor=rng.choice(anchors)
                obj.location=anchor.location+Vector((1.1,0,spec['plants']['tree']['height']*anchor.scale.z*.8)) if kind=='vine' else anchor.location.copy()
            s=rng.uniform(*params['scale'])
            obj.scale=(s,s,s)
            obj.rotation_euler.z=rng.uniform(0,math.tau)
            counts[kind]=counts.get(kind,0)+1
    for i,hero in enumerate(spec['hero_plants']):
        proto,group=prototypes[hero['kind']][0]
        obj=bpy.data.objects.new(f'Hero_{hero["kind"]}_{i}',proto.data)
        collection.objects.link(obj)
        obj.parent=group
        x,y=hero['location']
        obj.location=(x,y,elevation(x,y))
        obj.scale=(hero['scale'],)*3
    for i in range(backdrop['count']):
        proto,group=rng.choice(prototypes['shrub'])
        obj=bpy.data.objects.new(f'DistantUnderstory_{i:03}',proto.data)
        collection.objects.link(obj)
        obj.parent=group
        x,y=rng.uniform(*backdrop['x_range']),rng.uniform(*backdrop['y_range'])
        obj.location=(x,y,elevation(x,y))
        obj.scale=(rng.uniform(*backdrop['scale']),)*3
        obj.rotation_euler.z=rng.uniform(0,math.tau)
    counts['distant_understory']=backdrop['count']
    for variants in prototypes.values():
        for proto,group in variants:
            bpy.data.objects.remove(proto,do_unlink=True)
    (asset_dir/'manifest.json').write_text(json.dumps({'assets':assets,'units':'meters','vine_pivot':'top attachment; other plants at ground'},indent=2))
    # Deliberate foreground trunks frame the uphill clearing, as in the reference.
    for i,(x,y,h) in enumerate(spec['hero_palms']):
        params=dict(spec['plants']['palm'],height=h)
        obj=prototype('palm',mats,collection,rng,params)
        obj.name=f'ForegroundPalm_{i}'
        obj.location=(x,y,elevation(x,y))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        if obj.type in ('MESH','EMPTY'): obj.select_set(True)
    destination=context.path('output_dir')/'coastal_jungle.glb'
    destination.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format='GLB',use_selection=True,export_gpu_instances=True,export_yup=True,export_image_format='WEBP',export_image_quality=88)
    from jobs.forest_atlas import export_baked_texture
    export_baked_texture(destination,root,spec['canopy_atlas'])
    textures=[m.name for m in mats if any(n.type=='TEX_IMAGE' for n in m.node_tree.nodes)]+[soil.name,path_material.name]
    (destination.parent/'forest_manifest.json').write_text(json.dumps({'seed':spec['seed'],'instances':counts,'glb_bytes':destination.stat().st_size,'textures':textures,'units':'meters'},indent=2))
