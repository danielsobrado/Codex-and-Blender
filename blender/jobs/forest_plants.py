"""Layered tropical plants with connected branches and bent leaf surfaces."""
import math
from mathutils import Vector


def populate(m,kind,rng,p):
    tau=math.tau
    if kind=='background_tree':
        kind='tree'
    if kind=='grass':
        for i in range(p['blades']):
            a=rng.uniform(0,tau)
            m.card((rng.uniform(-.28,.28),rng.uniform(-.28,.28),0),a,rng.uniform(*p['length']),rng.uniform(*p['width']),rng.uniform(1.4,2.7),.85,rng.randrange(12),(12,1),0,fold=.07,segments=3)
    elif kind=='groundcover':
        for i in range(p['leaves']):
            a=i*2.399
            r=rng.uniform(0,.5)
            m.card((math.cos(a)*r,math.sin(a)*r,.025),a,rng.uniform(.22,.38),.21,.3,.2,rng.choice([0,1,3,4,5,7,8,9,11,12,13,15]),(4,4),3,fold=.25,segments=2)
    elif kind=='fern':
        for i in range(p['leaves']):
            m.card((0,0,.04),i*2.399,rng.uniform(.65,1.05),.48,.85,.65,rng.randrange(4,8),(4,2),2,fold=.25)
    elif kind=='broadleaf':
        row=p['leaf_rows_by_variant'][p.get('variant',0)]
        for i in range(p['leaves']):
            a=i*2.399
            height=rng.uniform(*p['petiole_height'])
            start=Vector((math.cos(a)*.14,math.sin(a)*.14,height))
            m.tube([(0,0,0),start*.55,start],[.018,.014,.009],5)
            m.card(start,a,rng.uniform(*p['length']),rng.uniform(*p['width']),rng.uniform(*p['rise']),.55,row*4+rng.randrange(4),(4,2),1,fold=.26)
    elif kind=='shrub':
        for i in range(p['branches']):
            a=i*2.399
            tip=Vector((math.cos(a)*.55,math.sin(a)*.55,p['height']*rng.uniform(.45,.8)))
            m.tube([(0,0,0),tip],[.02,.004],4)
            for j in range(p['sprays']):
                a=j*2.399+i
                offset=Vector((math.cos(a)*.3,math.sin(a)*.3,rng.uniform(-.2,.3)))
                m.canopy_card(tip+offset,(math.cos(a),math.sin(a),rng.uniform(.1,1)),rng.uniform(*p['spray_size']),rng.randrange(4),tip)
    elif kind=='palm':
        h=p['height']
        points=[(.6*(j/14)**2,.14*math.sin(j/14*math.pi),h*j/14) for j in range(15)]
        m.tube(points,[.19*(1-.35*j/14) for j in range(15)],4)
        for i in range(p['fronds']):
            m.card(points[-1],i*2.399,rng.uniform(2,3.4),1.1,rng.uniform(.1,.7),.6,rng.randrange(4),(4,2),2,fold=.3)
    elif kind=='tree':
        h=p['height']
        lean=Vector((rng.uniform(-.6,.6),rng.uniform(-.5,.5),0))
        trunk=[Vector((.1*math.sin(j*1.4),.11*math.sin(j*.8),h*.61*j/6))+lean*(j/6)**1.5 for j in range(7)]
        top=trunk[-1]
        m.tube(trunk,[p['radius']*(1-.55*j/6) for j in range(7)],4)
        for i in range(5):
            a=i*tau/5
            m.tube([(math.cos(a)*p['radius']*2.3,math.sin(a)*p['radius']*2.3,0),(0,0,h*.12)],[p['radius']*.3,p['radius']*.13],4)
        for i in range(p['branches']):
            a=i*2.399+rng.uniform(-.25,.25)
            reach=p['crown_radius']*rng.uniform(.3,.78)
            level=.92-.2*(reach/p['crown_radius'])+rng.uniform(-.045,.045)
            end=lean+Vector((math.cos(a)*reach,math.sin(a)*reach,h*level))
            start=trunk[rng.choice([4,5,6])]
            mid=start.lerp(end,.52)+Vector((-.2*math.sin(a),.2*math.cos(a),.3))
            m.tube([start,mid,end],[p['radius']*.42,.055,.02],4)
            for j in range(p['twigs']):
                b=a+(j/(p['twigs']-1)-.5)*2.8
                tip=end+Vector((math.cos(b)*rng.uniform(.45,1.1),math.sin(b)*rng.uniform(.45,1.1),rng.uniform(-.1,.55)))
                m.tube([end,end.lerp(tip,.55)+Vector((0,0,.12)),tip],[.02,.012,.004],4)
                for k in range(p['sprays']):
                    longitude=k*2.399+rng.uniform(-.2,.2)
                    z=1-2*(k+.5)/p['sprays']
                    radial=math.sqrt(1-z*z)
                    normal=Vector((math.cos(longitude)*radial,math.sin(longitude)*radial,z))
                    offset=Vector((normal.x,normal.y,normal.z*.65))*p['spray_radius']
                    m.canopy_card(tip+offset,normal,rng.uniform(*p['spray_size']),rng.randrange(4),tip)
            if i<p['hanging_vines']:
                length=rng.uniform(*p['vine_length'])
                attachment=end+Vector((math.cos(a)*.4,math.sin(a)*.4,-.1))
                points=[attachment+Vector((.1*math.sin(k*.7+a),.08*math.cos(k*.9),-length*k/14)) for k in range(15)]
                m.tube(points,[.009]*15,4)
                for k,at in enumerate(points[2:]):
                    if k%3!=1:
                        m.card(at,a+k*2.399,.4,.42,-1.15,.1,rng.randrange(4),(2,2),6,fold=.08,segments=2)
    elif kind=='vine':
        for i in range(p['strands']):
            length=rng.uniform(*p['length'])
            points=[(i*.22+.09*math.sin(j*.6+i),.09*math.cos(j*.5+i),-length*j/18) for j in range(19)]
            m.tube(points,[.012]*19,4)
            for j,at in enumerate(points[1:]):
                m.card(at,j*2.399,rng.uniform(.22,.42),.22,-.3,.2,rng.randrange(16),(4,4),3,fold=.25)
    elif kind=='climber':
        points=[(math.cos(i*.6)*.25,math.sin(i*.6)*.25,i*p['height']/p['leaves']) for i in range(p['leaves']+1)]
        m.tube(points,[.012]*len(points),4)
        for i in range(p['leaves']):
            a=i*2.399
            z=i*p['height']/p['leaves']
            at=Vector((math.cos(a)*.24,math.sin(a)*.24,z))
            m.card(at,a,rng.uniform(.45,.8),.45,-.7,.15,rng.randrange(4),(4,2),1,fold=.32)
    elif kind=='split_leaf':
        for i in range(p['leaves']):
            a=i*2.399
            at=Vector((math.cos(a)*.12,math.sin(a)*.12,rng.uniform(.65,1.3)))
            m.tube([(0,0,0),at],[.02,.009],5)
            m.split_leaf(at,a,rng.uniform(.9,1.3),rng.uniform(.65,.9),rng.randrange(4))
    else:
        raise ValueError(f'Unknown forest asset: {kind}')
