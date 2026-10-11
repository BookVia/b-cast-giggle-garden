import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'cast_anatomy_v39';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R));from png_validation import valid_png
def audit(ob):
 bm=bmesh.new();bm.from_mesh(ob.data)
 a={'vertices':len(bm.verts),'faces':len(bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
 bm.free();return a
def warp(q):
 if q.z<1.82:
  t=min(1,max(0,(1.82-q.z)/.080));t=t*t*(3-2*t);q.x*=1-.69*t;q.y=q.y*(1-t)+.025*t
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
 low=[v for v in bm.verts if (head.matrix_world@v.co).z<1.79]
 for _ in range(4):bmesh.ops.smooth_vert(bm,verts=low,factor=.40,use_axis_x=True,use_axis_y=True,use_axis_z=False)
 bm.to_mesh(head.data);bm.free();head.data.update()


 if name=='Kiki':
  from mathutils.bvhtree import BVHTree
  from array import array
  for ob in list(bpy.context.scene.objects):
   if any(t in ob.name for t in ['scalp fitted','fitted curved bangs','silky bob fibres']):
    bpy.data.objects.remove(ob,do_unlink=True)
  hair=bpy.data.materials['Kiki V36 shaped hair'];fibre=bpy.data.materials['Kiki V36 hair fibre']
  for m in [hair,fibre]:
   shader=m.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.72
   if shader.inputs.get('Specular IOR Level'):shader.inputs['Specular IOR Level'].default_value=.18
  bvh=BVHTree.FromPolygons([head.matrix_world@v.co for v in head.data.vertices],[tuple(p.vertices) for p in head.data.polygons])
  vs=[];fs=[];paths=[]
  for i in range(121):
   x=-.345+.69*i/120;path=[]
   for j in range(33):
    t=j/32;xx=x*(.08+.92*t);z=2.715-(.30+.025*math.cos(x*16))*t
    fallback=.025-.375*math.sin(t*math.pi/2)
    hit=bvh.ray_cast(Vector((xx,-1,z)),Vector((0,1,0)))
    y=min(fallback,hit[0].y-.025) if hit[0] else fallback
    v=(xx,y,z);vs.append(v);path.append(v)
   paths.append(path)
  for i in range(120):
   for j in range(32):k=i*33+j;fs.append((k,k+1,k+34,k+33))
  d=bpy.data.meshes.new('Kiki V39 curved bob bangs');d.from_pydata(vs,[],fs);d.update();d.materials.append(hair)
  bangs=bpy.data.objects.new('Kiki V39 continuous curved bangs',d);bpy.context.scene.collection.objects.link(bangs)
  for f in d.polygons:f.use_smooth=True
  bangs.modifiers.new('Bangs refinement','SUBSURF').levels=1;bangs.modifiers.new('Bangs thickness','SOLIDIFY').thickness=.005
  # Closely spaced swept strands follow the exact newly built surface.
  strandpaths=[]
  for i in range(120):
   for child in range(8):
    f=(child+.5)/8;strandpaths.append([Vector(paths[i][j]).lerp(Vector(paths[i+1][j]),f)+Vector((0,-.0012,0)) for j in range(33)])
  for i in range(1000):
   a=math.tau*i/1000;path=[]
   for j in range(33):
    t=j/32
    rad=.415*math.sin(min(1,t*1.8)*math.pi/2)
    path.append((rad*math.cos(a),.04+.845*rad*math.sin(a),2.72-.735*t))
   if math.sin(a)>-.48:strandpaths.append(path)
  d=bpy.data.hair_curves.new('Kiki V39 silk bob fibres');d.add_curves([33]*len(strandpaths))
  co=array('f');radii=array('f')
  for path in strandpaths:
   for j,q in enumerate(path):co.extend(q);radii.append(.0009*(1-.85*j/32))
  d.attributes['position'].data.foreach_set('vector',co);d.attributes.new(name='radius',type='FLOAT',domain='POINT').data.foreach_set('value',radii);d.materials.append(fibre)
  ob=bpy.data.objects.new('Kiki V39 surface following bob fibres',d);bpy.context.scene.collection.objects.link(ob)



 if name=='Kiki':
  bob=next(o for o in bpy.context.scene.objects if 'continuous bob shell' in o.name)
  N=128;vs=[];fs=[];rings=[(1.98,.41),(2.05,.425),(2.23,.43),(2.40,.42),(2.52,.37),(2.62,.29),(2.69,.19),(2.76,.005)]
  for z,rad in rings:
   for i in range(N):
    a=math.tau*i/N;vs.append((rad*math.cos(a),.04+.93*rad*math.sin(a),z))
  for j in range(7):
   for i in range(N):
    a=math.tau*(i+.5)/N
    if math.sin(a)<-.48 and j<3:continue
    k=j*N+i;l=j*N+(i+1)%N;fs.append((k,l,l+N,k+N))
  d=bpy.data.meshes.new('Kiki V39 fitted full bob shell');d.from_pydata(vs,[],fs);d.update();d.materials.append(bpy.data.materials['Kiki V36 shaped hair'])
  bob.data=d
  for f in d.polygons:f.use_smooth=True

 # Lower the complete head assembly together to restore childlike neck length.
 for ob in bpy.context.scene.objects:
  if ob.name.startswith(name+' V36 ') or name=='Kiki' and ob.name.startswith(('Kiki V39 continuous','Kiki V39 surface','Hair clip centre','Clip petal')):
   ob.location.z-=.12

 # Upgrade the retained V10 body and footwear to Amina's newer connected surfaces.
 for ob in list(bpy.context.scene.objects):
  if ob.name.startswith(('Neck','Shirt','Sleeve','Arm','Palm','Finger','Thumb','Leg','Sneaker','Shorts leg','Overalls waist','Long hoodie','Hoodie cuff','Blue hood','Hood drawstring')):
   bpy.data.objects.remove(ob,do_unlink=True)
 with bpy.data.libraries.load(str(R/'amina_reconstruction_v22/Amina_likeness_candidate_UNAPPROVED.blend'),link=False) as (a,b):
  b.objects=[n for n in a.objects if n.startswith(('Amina V18 connected body','Amina V18 connected cotton tee','Amina V18 shaped overall shorts','V19 sneaker','V19 shaped canvas','V19 padded ankle','V19 toe bumper','V19 eyelet','V19 crossed cotton','V19 bow lace','V19 upper side','V19 anatomical fingernail')) and (name!='Kiki' or not n.startswith('Amina V18 shaped overall shorts'))]
 skin=head.data.materials[0];body=None;tee=None;shorts=None
 clothing={'Tebo':(.025,.24,.68),'Kiki':(.82,.48,.04),'Luma':(.075,.28,.055)}
 for ob in b.objects:
  if not ob:continue
  bpy.context.scene.collection.objects.link(ob);original=ob.name;ob.name=name+' V39 '+original
  if 'connected body' in original:
   body=ob;ob.data.materials.clear();ob.data.materials.append(skin)
   ob.data.update()
  elif 'connected cotton tee' in original:tee=ob
  elif 'shaped overall shorts' in original:shorts=ob
  for i,m in enumerate(ob.data.materials):
   if ob==body:continue
   if any(t in original for t in ['cotton tee','canvas sneaker','shaped overall']):
    m=m.copy();m.name=name+' V39 '+m.name
    c=clothing[name] if 'cotton' in original else ({'Tebo':(.25,.235,.14),'Luma':(.48,.34,.17)}[name] if 'shaped overall' in original else {'Tebo':(.02,.14,.42),'Kiki':(.70,.07,.30),'Luma':(.045,.20,.08)}[name])
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*c,1);ob.data.materials[i]=m

 if True:
  helper=(R/'reconstruct_amina_v18.py').read_text();helper=helper[helper.index('def mat('):helper.index('# Preserve existing files;')];exec(compile(helper,'local_surface_helpers','exec'),globals())
 cotton=tee.data.materials[0];parts=[tee]
 for side in [-1,1]:
  parts.append(loft(name+' V39 fitted shoulder bridge',[(side*.105,0,1.495,.040,.108),(side*.17,0,1.480,.046,.128),(side*.24,0,1.452,.055,.133)],cotton,n=32))
 tee=unite(name+' V39 connected shoulder and collar garment',parts,.007,3)

 if name=='Tebo':
  # Keep the already connected shoulder and collar surface.
  helper=(R/'reconstruct_amina_v18.py').read_text();helper=helper[helper.index('def mat('):helper.index('# Preserve existing files;')]
  exec(compile(helper,'local_surface_helpers','exec'),globals())
  cotton=mat('Tebo V39 blue hoodie cotton',clothing[name],.75)
  parts=[tee]
  for side in [-1,1]:
   parts.append(loft('Tebo fitted long hoodie sleeve',[(side*.34,-.003,1.32,.112,.116),(side*.40,-.01,1.24,.10,.107),(side*.445,-.02,1.11,.09,.091),(side*.47,-.03,.985,.07,.075)],cotton,n=36))
  hoodie=unite('Tebo V39 connected tailored hoodie',parts,.007,3)
  # Open hood rim follows the raised neckline instead of a separate padded lump.
  for side in [-1,1]:
   curve('Tebo V39 hood rim',[(side*(.115+.10*math.sin(math.pi*t)),.10+.11*math.sin(math.pi*t),1.50+.075*math.sin(math.pi*t)) for t in [j/40 for j in range(41)]],.021,cotton)
   curve('Tebo V39 hood drawstring',[(side*.10,-.12,1.49),(side*.085,-.188,1.31)],.004,bpy.data.materials.get('V19 warm white rubber and laces'))
 # New body topology and wardrobe remain unrigged; retain each original motif/dress.
 report_body={'body':audit(body),'garment':audit(hoodie if name=='Tebo' else tee),'shorts':audit(shorts) if shorts else None}
 assert report_body['body']['finite'] and report_body['body']['boundary_edges']==0 and report_body['body']['overused_edges']==0
 print('V39_BODY_GEOMETRY_PASS',name,flush=True)

 sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False
 report=json.loads((R/'cast_anatomy_v36'/(name+'_audit.json')).read_text());report.update(revision='V39 integrated head/body candidate',new_head_mesh=audit(head),body_geometry=report_body,source_body='Amina V22 connected body/garment/footwear surfaces, matched to individual wardrobe; Tebo hoodie rebuilt',changes=['Corrected neck taper below mouth cavity and shortened head/body neck transition','Raised mouth corners and reduced mouth height','Reduced iris/pupil groups together','Removed old Kiki fringe strands','Further individualized Kiki/Luma nose proportions'])
 report['retained_objects']=[n for n in report['retained_objects'] if bpy.context.scene.objects.get(n) is not None]
 report['groom_strands']=sum(len(o.data.attributes['position'].data)//33 for o in bpy.context.scene.objects if o.type=='CURVES')
 report['native_groom_points']=sum(len(o.data.attributes['position'].data) for o in bpy.context.scene.objects if o.type=='CURVES')
 report['armatures']=sum(o.type=='ARMATURE' for o in bpy.context.scene.objects)
 report['all_meshes_finite']=all(math.isfinite(c) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)
 assert report['all_meshes_finite'] and report['armatures']==0
 assert report['new_head_mesh']['finite'] and report['new_head_mesh']['overused_edges']==0 and report['new_head_mesh']['zero_area_faces']==0
 bpy.ops.wm.save_as_mainfile(filepath=str(O/(name+'_anatomy_candidate_UNAPPROVED.blend')))
 for view,loc,target,scale,size in [('front',(0,-7,1.65),(0,0,1.4),3.05,(600,820)),('face',(0,-7,2.2),(0,0,2.2),1.3,(640,640)),('three_quarter',(3,-6,2.2),(0,0,2.2),1.3,(640,640)),('profile',(6,-1,2.2),(0,0,2.2),1.3,(640,640))]:
  cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
  sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),*size);print('V39_RENDER_PASS',name,view,flush=True)
 report['png_validation_passed']=True;allreports[name]=report;(O/(name+'_audit.json')).write_text(json.dumps(report,indent=2))
(O/'cast_audit.json').write_text(json.dumps(allreports,indent=2));print('CAST_V39_COMPLETE',flush=True)
