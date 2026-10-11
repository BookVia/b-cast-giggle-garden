"""Amina anatomy branch: custom fitted openings, scalp and expression. Unapproved."""
import bpy,bmesh,math,json,array,random,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'amina_reconstruction_v31';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'tool_experiments/mpfb_head_refit/Amina_anatomy_refit_UNAPPROVED.blend'))
head=bpy.data.objects['Amina new anatomy head experiment UNAPPROVED'];head.name='Amina anatomy refinement V31 UNAPPROVED'
for o in list(bpy.context.scene.objects):
 if o.name.startswith(('Amina fitted scalp','Amina swept scalp')):bpy.data.objects.remove(o,do_unlink=True)
for v in head.data.vertices:
 p=v.co
 if p.z>2.32:p.z=2.32+(p.z-2.32)*.84
 p.x*=1+.045*math.exp(-((p.z-2.02)/.15)**2)
 # Raise lip corners through the surrounding quad surface.
 p.z+=.025*min((abs(p.x)/.12)**2,1)*math.exp(-((p.z-1.99)/.055)**2)*math.exp(-((p.y+.30)/.10)**2)
head.data.update()
skin=head.data.materials[0]
def material(name,color,rough=.55):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough;return m
hair=material('V31 dark warm scalp',(.022,.006,.002),.65)
lip=material('V31 lip warm brown',(.22,.039,.016),.55)
cavity=material('V31 inner mouth',(.045,.004,.006),.75)
teeth=material('V31 warm ivory teeth',(.84,.77,.64),.35)
# Match all eye components together in world space, preserving their relative depths.
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.name.startswith(('Amina seated eyeball','Amina brown iris','Amina pupil','Amina main eye reflection','Amina secondary reflection')):
  xs=[(o.matrix_world@v.co).x for v in o.data.vertices];side=-1 if sum(xs)<0 else 1
  old=Vector((side*.208,-.23,2.175));new=Vector((side*.185,-.185,2.175))
  inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   q=o.matrix_world@v.co-old;q=Vector((q.x*.74,q.y*.86,q.z*.70));v.co=inv@(new+q)
  o.data.update()
# Evaluate the anatomical surface before cutting smooth, closed cavity pockets.
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
for mod in list(head.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
head.data.materials.append(cavity);removed={}
for name,cx,cz,rx,ry,rz,smile in [('left',-.185,2.175,.088,.18,.066,False),('right',.185,2.175,.088,.18,.066,False),('mouth',0,1.895,.145,.16,.067,True)]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=(cx,-.26 if not smile else -.275,cz))
 cutter=bpy.context.object;cutter.name='Temporary socket tool '+name
 for v in cutter.data.vertices:
  v.co.x*=rx;v.co.y*=ry;v.co.z*=rz
  if smile:v.co.z+=.030*(v.co.x/rx)**2
 cutter.data.materials.append(skin);cutter.data.materials.append(cavity)
 for p in cutter.data.polygons:p.material_index=1 if smile else 0
 bpy.context.view_layer.objects.active=head;head.select_set(True);cutter.select_set(False)
 mod=head.modifiers.new('Socket cavity '+name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 before=len(head.data.polygons);bpy.ops.object.modifier_apply(modifier=mod.name);removed[name]=before-len(head.data.polygons)
 bpy.data.objects.remove(cutter,do_unlink=True)
for p in head.data.polygons:p.use_smooth=True
# Interior mouth surface and a single curved upper tooth strip.
def mesh_object(name,vs,fs,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
 for p in me.polygons:p.use_smooth=True
 return ob
vs=[(0,-.211,1.895)]+[(.148*math.cos(i*math.tau/64),-.211,1.895+.069*math.sin(i*math.tau/64)+.030*math.cos(i*math.tau/64)**2) for i in range(64)]
mesh_object('V31 mouth interior',vs,[(0,i+1,(i+1)%64+1) for i in range(64)],cavity)
vs=[];fs=[]
for i in range(33):
 x=-.116+.232*i/32;z=1.937-.020*(x/.116)**2
 vs.extend([(x,-.256+.012*(x/.099)**2,z),(x,-.252+.012*(x/.099)**2,z-.020)])
 if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
mesh_object('V31 curved upper teeth',vs,fs,teeth)
# Build the cap directly from the evaluated head surface; no generic floating scalp strips.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=head.evaluated_get(deps);me=ev.to_mesh()
verts=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons]
bvh=BVHTree.FromPolygons(verts,faces)
keep=[]
for p in me.polygons:
 c=p.center;line=2.445-.14*(abs(c.x)/.36)**1.4 if c.y<.025 else 2.22
 if c.z>line:keep.append(tuple(p.vertices))
indices=sorted({i for f in keep for i in f});mapping={old:i for i,old in enumerate(indices)}
capvs=[tuple(me.vertices[i].co+me.vertices[i].normal*.0025) for i in indices]
cap=mesh_object('V31 scalp fitted to anatomy',capvs,[tuple(mapping[i] for i in f) for f in keep],hair)
capbm=bmesh.new();capbm.from_mesh(cap.data)
for v in {v for e in capbm.edges if e.is_boundary for v in e.verts}:
 if v.co.y<.025:
  z=2.445-.14*(abs(v.co.x)/.36)**1.4
  hit=bvh.ray_cast(Vector((v.co.x,-1,z)),Vector((0,1,0)))
  if hit[0] is not None:v.co=hit[0]+hit[1]*.0025
capbm.to_mesh(cap.data);capbm.free()
strandmat=bpy.data.materials.new('V31 natural fibre shader');strandmat.use_nodes=True
nodes=strandmat.node_tree.nodes;nodes.clear();shader=nodes.new('ShaderNodeBsdfHairPrincipled');shader.parametrization='COLOR';shader.inputs['Color'].default_value=(.025,.008,.0025,1);shader.inputs['Roughness'].default_value=.48
out=nodes.new('ShaderNodeOutputMaterial');strandmat.node_tree.links.new(shader.outputs[0],out.inputs['Surface'])
for puff in bpy.context.scene.objects:
 if puff.type=='CURVES' and 'detailed puff' in puff.name:
  puff.data.materials.clear();puff.data.materials.append(strandmat)

# Fine swept strands follow the head surface toward the rear gathering point.
random.seed(24);paths=[]
for i in range(1800):
 x=random.uniform(-.32,.32);z=2.447-.13*(abs(x)/.36)**1.4+random.uniform(0,.10)
 hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if hit[0] is None:continue
 start=hit[0];target=Vector((x*.70,.13,2.62));path=[]
 for j in range(25):
  t=j/24;q=start.lerp(target,t);q.z+=.11*math.sin(math.pi*t)
  nearest=bvh.find_nearest(q)
  if nearest[0] is None:continue
  pos=nearest[0]+nearest[1]*(.0035+.0012*math.sin(t*math.tau*6+i));pos.x+=.0012*math.sin(t*math.tau*8+i);path.append(tuple(pos))
 if len(path)>2:paths.append(path)
data=bpy.data.hair_curves.new('V31 swept scalp fibres');data.add_curves([len(p) for p in paths]);pos=array.array('f');rad=array.array('f')
for path in paths:
 for i,p in enumerate(path):pos.extend(p);rad.append(.0005*(1-.5*i/(len(path)-1)))
data.attributes['position'].data.foreach_set('vector',pos)
att=data.attributes.get('radius') or data.attributes.new(name='radius',type='FLOAT',domain='POINT');att.data.foreach_set('value',rad)
ob=bpy.data.objects.new('V31 swept scalp fibres',data);bpy.context.scene.collection.objects.link(ob);data.materials.append(hair)
# Eyebrows are fitted to the actual forehead rather than placed at a fixed depth.
for side in [-1,1]:
 pts=[]
 for i in range(17):
  t=i/16;x=side*(.105+.15*t);z=2.302+.024*math.sin(math.pi*t)-.022*t
  hit=bvh.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
  if hit[0] is not None:pts.append(tuple(hit[0]+hit[1]*.003))
 curve=bpy.data.curves.new('V31 brow','CURVE');curve.dimensions='3D';curve.bevel_depth=.010;curve.bevel_resolution=3
 spl=curve.splines.new('POLY');spl.points.add(len(pts)-1)
 for i,(point,co) in enumerate(zip(spl.points,pts)):point.co=(*co,1);point.radius=.25+.75*math.sin(math.pi*(i+.5)/len(pts))
 ob=bpy.data.objects.new('V31 fitted eyebrow '+str(side),curve);bpy.context.scene.collection.objects.link(ob);curve.materials.append(hair)
ev.to_mesh_clear()
sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Amina_anatomy_refinement_UNAPPROVED.blend'))
print('V31_GEOMETRY_REBUILT',removed,flush=True)
