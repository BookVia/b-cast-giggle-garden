import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'cast_anatomy_v37';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R));from png_validation import valid_png
def audit(ob):
 bm=bmesh.new();bm.from_mesh(ob.data)
 a={'vertices':len(bm.verts),'faces':len(bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
 bm.free();return a
def warp(q):
 if q.z<1.91:
  t=min(1,max(0,(1.91-q.z)/.125));t=t*t*(3-2*t);q.x*=1-.69*t;q.y=q.y*(1-t)+.025*t
 if q.y<-.12 and abs(q.x)<.20 and 1.84<q.z<2.02:
  w=math.exp(-((q.z-1.929)/.10)**4-(abs(q.x)/.185)**8)
  q.z+=w*(-.18*(q.z-1.929)+.045*(q.x/.15)**2)
 return q
allreports={}
for name in ['Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'cast_anatomy_v36'/(name+'_anatomy_candidate_UNAPPROVED.blend')))
 for ob in list(bpy.context.scene.objects):
  if ob.name.startswith('Fringe strand'):bpy.data.objects.remove(ob,do_unlink=True)
 head=next(o for o in bpy.context.scene.objects if 'anatomy refinement' in o.name)
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH' and (ob==head or 'mouth interior' in ob.name or 'curved upper teeth' in ob.name):
   inv=ob.matrix_world.inverted()
   for v in ob.data.vertices:v.co=inv@warp(ob.matrix_world@v.co)
   ob.data.update()
 # Reduce iris/pupil discs together around each seated eye; expose more whites.
 for side in [-1,1]:
  eye=next(o for o in bpy.context.scene.objects if 'seated eyeball' in o.name and (sum((o.matrix_world@Vector(v)).x for v in o.bound_box)<0)==(side<0))
  cen=sum([eye.matrix_world@Vector(v) for v in eye.bound_box],Vector())/8
  for ob in bpy.context.scene.objects:
   if ob.type=='MESH' and any(k in ob.name for k in ['brown iris','pupil','eye reflection','secondary reflection']):
    bb=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    if (sum(v.x for v in bb)<0)!=(side<0):continue
    inv=ob.matrix_world.inverted()
    for v in ob.data.vertices:
     q=ob.matrix_world@v.co;q.x=cen.x+(q.x-cen.x)*.86;q.z=cen.z+(q.z-cen.z)*.86;v.co=inv@q
    ob.data.update()
 if name in ['Kiki','Luma']:
  for v in head.data.vertices:
   q=head.matrix_world@v.co
   if q.y<-.22 and 1.99<q.z<2.15:
    w=math.exp(-((q.z-2.075)/.052)**2-(abs(q.x)/.14)**6);q.x*=1-.22*w;q.y+=.014*w;v.co=head.matrix_world.inverted()@q
  head.data.update()
 # Relax the reshaped low neck to remove the inherited cut-edge corrugation.
 bm=bmesh.new();bm.from_mesh(head.data)
 low=[v for v in bm.verts if (head.matrix_world@v.co).z<1.85]
 for _ in range(4):bmesh.ops.smooth_vert(bm,verts=low,factor=.40,use_axis_x=True,use_axis_y=True,use_axis_z=False)
 bm.to_mesh(head.data);bm.free();head.data.update()
 sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False
 report=json.loads((R/'cast_anatomy_v36'/(name+'_audit.json')).read_text());report.update(revision='V37 integrated head/body candidate',new_head_mesh=audit(head),changes=['Tapered and relaxed the inherited flat neck cut to overlap retained neck','Raised mouth corners and reduced mouth height','Reduced iris/pupil groups together','Removed old Kiki fringe strands','Further individualized Kiki/Luma nose proportions'])
 assert report['new_head_mesh']['finite'] and report['new_head_mesh']['overused_edges']==0 and report['new_head_mesh']['zero_area_faces']==0
 bpy.ops.wm.save_as_mainfile(filepath=str(O/(name+'_anatomy_candidate_UNAPPROVED.blend')))
 for view,loc,target,scale,size in [('front',(0,-7,1.65),(0,0,1.4),3.05,(600,820)),('face',(0,-7,2.2),(0,0,2.2),1.3,(640,640)),('three_quarter',(3,-6,2.2),(0,0,2.2),1.3,(640,640)),('profile',(6,-1,2.2),(0,0,2.2),1.3,(640,640))]:
  cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
  sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),*size);print('V37_RENDER_PASS',name,view,flush=True)
 report['png_validation_passed']=True;allreports[name]=report;(O/(name+'_audit.json')).write_text(json.dumps(report,indent=2))
(O/'cast_audit.json').write_text(json.dumps(allreports,indent=2));print('CAST_V37_COMPLETE',flush=True)
