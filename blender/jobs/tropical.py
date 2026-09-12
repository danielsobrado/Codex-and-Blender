"""Tropical plant silhouettes built from portable leaf and woody mesh surfaces."""
import math
from mathutils import Vector


def frond(mesh, origin, angle, length, rise, pairs, width, palette, rng):
    origin = Vector(origin)
    forward = Vector((math.cos(angle), math.sin(angle), 0))
    side = Vector((-math.sin(angle), math.cos(angle), 0))
    def point(t):
        return origin + forward*length*t + Vector((0, 0, length*(rise*t-.48*t*t)))
    previous = origin
    for j in range(1, pairs+1):
        t = j/pairs
        p = point(t)
        mesh.branch(previous, p, length*.006*(1-t*.8), 2, 5)
        leaflet = length*width*(math.sin(math.pi*t)**.65+.08)
        for sign in (-1, 1):
            direction = side*sign + forward*.28 + Vector((0,0,-.12))
            mesh.leaf(p, direction, leaflet, leaflet*.16, leaflet*.13, rng.choice(palette))
        previous = p


def trunk(mesh, height, radius, lean, segments, ringed):
    previous = Vector((0,0,0))
    for j in range(1, segments+1):
        t=j/segments
        p=Vector((lean*t*t, .08*math.sin(t*math.pi), height*t))
        mesh.branch(previous,p,radius*(1-.35*(j-1)/segments),6,12,end_radius=radius*(1-.35*t))
        if ringed:
            band=p.lerp(previous,.07)
            mesh.branch(band,p,radius*(1-.35*t)*1.025,8,12,end_radius=radius*(1-.35*t)*1.025)
        previous=p
    return previous


def add_tropical(mesh, spec, rng):
    kind, h = spec['kind'], spec['height']
    palette=spec['materials']
    if kind=='frond':
        frond(mesh,(0,0,0),0,h,spec['rise'],spec['pairs'],spec['leaflet_width'],palette,rng)
    elif kind=='leaf':
        mesh.leaf((0,0,0),(1,0,.3),h,spec['width'],h*.12,rng.choice(palette))
    elif kind=='fern':
        for i in range(spec['count']):
            frond(mesh,(0,0,.03),i*math.tau/spec['count']+rng.uniform(-.2,.2),h*rng.uniform(.8,1.15),.65,spec['pairs'],.22,palette,rng)
    elif kind=='broadleaf':
        for i in range(spec['count']):
            a=i*2.399
            p=Vector((math.cos(a)*.12,math.sin(a)*.12,h*rng.uniform(.25,.65)))
            mesh.branch((0,0,0),p,h*.012,2,6)
            length=h*rng.uniform(.5,.85)
            mesh.leaf(p,(math.cos(a),math.sin(a),.45),length,length*spec['leaf_width'],length*.3,rng.choice(palette))
    elif kind=='palm':
        crown=trunk(mesh,h,spec['trunk_radius'],spec['lean'],spec['segments'],True)
        for i in range(spec['count']):
            frond(mesh,crown,i*2.399,spec['crown_radius']*rng.uniform(.8,1.1),rng.uniform(.1,.65),spec['pairs'],.27,palette,rng)
    elif kind=='tree':
        crown=trunk(mesh,h*.72,spec['trunk_radius'],spec['lean'],spec['segments'],False)
        for i in range(spec['count']):
            angle=i*2.399
            end=crown+Vector((math.cos(angle)*spec['crown_radius']*rng.uniform(.35,1),math.sin(angle)*spec['crown_radius']*rng.uniform(.35,1),h*rng.uniform(-.06,.22)))
            origin=crown-Vector((0,0,h*rng.uniform(.05,.22)))
            mesh.branch(origin,end,spec['trunk_radius']*.32,6,8)
            for j in range(spec['twigs']):
                a=angle+j*2.399
                tip=end+Vector((math.cos(a)*.65,math.sin(a)*.65,rng.uniform(-.15,.5)))
                mesh.branch(end,tip,.018,6,5)
                for k in range(9):
                    p=end.lerp(tip,.2+k*.09)
                    la=a+(-1 if k%2 else 1)*1.1
                    mesh.leaf(p,(math.cos(la),math.sin(la),.5),rng.uniform(.25,.5),.13,.09,rng.choice(palette))
        for i in range(6):
            a=i*math.tau/6
            mesh.branch((math.cos(a)*spec['trunk_radius']*3,math.sin(a)*spec['trunk_radius']*3,.02),(0,0,h*.13),spec['trunk_radius']*.4,6,7)
    elif kind=='vine':
        for i in range(spec['count']):
            x=(i-(spec['count']-1)/2)*spec['width']
            previous=Vector((x,0,h))
            length=h*rng.uniform(.65,1)
            for j in range(1,spec['segments']+1):
                t=j/spec['segments']
                p=Vector((x+.12*math.sin(t*9+i),.08*math.cos(t*7+i),h-length*t))
                mesh.branch(previous,p,.012,6,5)
                mesh.leaf(p,((-1)**j,.2,-.25),.22,.13,.03,rng.choice(palette))
                previous=p
    else:
        raise ValueError(f'Unknown vegetation kind: {kind}')
