import numpy as np, trimesh, manifold3d as m3, math, sys
# inches, Z up, X along top rail, Y across
P=dict(rail_L=29.0, rail_T=1.125, rail_H=2.125, top=29.25,
 leg_T=0.875, leg_W=2.375, inner=22.75, slot_D=1.375, cham_x=0.25,
 foot_L=12.0, foot_W=1.125, foot_H=1.75, foot_end_H=1.0, foot_flat=0.5, relief_D=0.25, pad_L=2.5,
 lt_T=0.375, lt_W=1.75, lt_D=1.125,
 st_H=2.875, st_T=0.75, st_z0=10.25, stt_T=0.25, stt_H=2.375,
 cu_W=4.25, cu_above=2.25)
def box(x0,x1,y0,y1,z0,z1):
    return m3.Manifold.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def prof_x(pts, x0, x1):
    # pts in (y,z), extrude along +x
    cs=m3.CrossSection([pts])
    s=m3.Manifold.extrude(cs, x1-x0)          # along z: (y,z)->(x',y'), extrude z
    # map (a,b,c)->(x=c+x0, y=a, z=b)
    return s.warp(lambda v: [v[2]+x0, v[0], v[1]]) if False else s.transform([[0,0,1,x0],[1,0,0,0],[0,1,0,0]])
def build(P):
    p=type('',(),P)
    rail_z0=p.top-p.rail_H; leg_top=rail_z0+p.slot_D
    xo=p.inner/2+p.leg_T; xi=p.inner/2
    parts={}
    parts['Top_Rail']=box(-p.rail_L/2,p.rail_L/2,-p.rail_T/2,p.rail_T/2,rail_z0,p.top)
    w=p.leg_W/2; c=p.cham_x
    legprof=[(-w,p.foot_H),(w,p.foot_H),(w,rail_z0),(w-c,leg_top),(p.rail_T/2,leg_top),(p.rail_T/2,rail_z0),
             (-p.rail_T/2,rail_z0),(-p.rail_T/2,leg_top),(-w+c,leg_top),(-w,rail_z0)]
    zc=(p.st_z0+p.st_H/2)
    for side,s in (('L',-1),('R',1)):
        x0,x1=sorted([s*xi,s*xo])
        leg=prof_x(legprof,x0,x1)
        ten=box(x0+(p.leg_T-p.lt_T)/2,x1-(p.leg_T-p.lt_T)/2,-p.lt_W/2,p.lt_W/2,p.foot_H-p.lt_D+1/32,p.foot_H)
        leg=leg+ten
        # through mortise for stretcher tenon
        mort=box(x0,x1,-p.stt_T/2,p.stt_T/2,zc-p.stt_H/2,zc+p.stt_H/2)
        leg=leg-mort
        parts[f'Leg_{side}']=leg
        L=p.foot_L/2; fx=p.foot_W/2; cx=(x0+x1)/2
        a=p.leg_W/2+p.foot_flat; r=L-p.pad_L
        fp=[(-L,0),(-r,0),(-r,p.relief_D),(r,p.relief_D),(r,0),(L,0),(L,p.foot_end_H),(a,p.foot_H),(-a,p.foot_H),(-L,p.foot_end_H)]
        foot=prof_x(fp,cx-fx,cx+fx)
        foot=foot-box(cx-p.lt_T/2,cx+p.lt_T/2,-p.lt_W/2,p.lt_W/2,p.foot_H-p.lt_D,p.foot_H+0.01)
        parts[f'Foot_{side}']=foot
    st=box(-xi,xi,-p.st_T/2,p.st_T/2,p.st_z0,p.st_z0+p.st_H)
    st=st+box(-xo,-xi,-p.stt_T/2,p.stt_T/2,zc-p.stt_H/2,zc+p.stt_H/2)+box(xi,xo,-p.stt_T/2,p.stt_T/2,zc-p.stt_H/2,zc+p.stt_H/2)
    parts['Stretcher']=st
    # cushion profile (y,z) relative to bottom at leg_top
    z0=leg_top; sw=p.rail_T/2; H=(p.top-leg_top)+p.cu_above; W=p.cu_W/2
    pts=[]
    # outer mushroom: param around from right lip to left lip
    n=48
    for i in range(n+1):
        t=-math.pi/2+ (math.pi+math.pi*0.0)*i/n   # -90..90 deg, right side bottom->top
        # superellipse centred at zc_, half widths W, hz
        pass
    zc_=z0+H*0.40; hz_up=H-H*0.40; hz_dn=H*0.40*1.15
    def side(sgn):
        out=[]
        for i in range(n+1):
            t=-math.pi/2+math.pi*i/n
            ct,st_=math.cos(t),math.sin(t)
            e=0.8
            y=W*np.sign(ct)*abs(ct)**e
            hz=hz_up if st_>0 else hz_dn
            z=zc_+hz*np.sign(st_)*abs(st_)**e
            out.append((sgn*y,z))
        return out
    R=side(1)  # bottom (y~0) to top (y~0)
    R=[(y,z) for (y,z) in R if z>=z0+1e-3]
    R=[(y,z) for (y,z) in R if y>=sw+0.12 or z>zc_]  # trim lower inner part to lip
    R=[(sw,z0),(R[0][0],z0)]+R
    Lft=[(-y,z) for (y,z) in reversed(R)]
    prof=R[:-1]+Lft[1:]
    prof=prof+[(-sw,z0),( -sw,p.top),(sw,p.top)]
    # remove duplicate top point
    clean=[]
    for q in prof:
        if not clean or (abs(q[0]-clean[-1][0])>1e-6 or abs(q[1]-clean[-1][1])>1e-6): clean.append(q)
    cs=m3.CrossSection([clean])
    parts['Cushion']=prof_x(clean,-p.rail_L/2,p.rail_L/2)
    return parts
if __name__=='__main__':
    parts=build(P)
    sc=trimesh.Scene()
    for k,v in parts.items():
        mm=v.to_mesh(); t=trimesh.Trimesh(mm.vert_properties[:,:3],mm.tri_verts)
        print(k, t.is_watertight, round(t.volume,2), np.round(t.bounds,3).tolist())
        sc.add_geometry(t,node_name=k,geom_name=k)
    sc.export(sys.argv[1] if len(sys.argv)>1 else 'sawhorse_local.glb')
