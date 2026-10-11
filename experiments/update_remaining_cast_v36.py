import bpy,bmesh,math,random,json,array,sys,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'cast_anatomy_v36';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R));from png_validation import valid_png
random.seed(3601)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
def curves(name,paths,m,r=.0012):
 d=bpy.data.hair_curves.new(name);d.add_curves([len(p) for p in paths]);co=array.array('f');ra=array.array('f')
 for path in paths:
  for j,p in enumerate(path):co.extend(p);ra.append(r*(1-.92*j/max(1,len(path)-1)))
 d.attributes['position'].data.foreach_set('vector',co)
 att=d.attributes.get('radius') or d.attributes.new(name='radius',type='FLOAT',domain='POINT');att.data.foreach_set('value',ra)
 ob=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(ob);d.materials.append(m);return ob
def mesh(name,vs,fs,m,sub=0):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();d.materials.append(m)
 o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o)
 for p in d.polygons:p.use_smooth=True
 if sub:o.modifiers.new('Smooth designed surface','SUBSURF').levels=sub
 return o
def audit(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
 a={'vertices':len(bm.verts),'faces':len(bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
 bm.free();return a
def transform(p,name):
 q=p.copy();z=q.z
 if name=='Tebo':q.x*=1.025;q.z=2.175+(z-2.175)*1.025
 if name=='Kiki':
  q.x*=1.025;q.z=2.175+(z-2.175)*.96
  if q.y<-.23 and 1.99<z<2.14:q.x*=1-.12*math.exp(-((z-2.075)/.05)**2);q.y+=.015*math.exp(-((q.x/.13)**4)-((z-2.075)/.06)**2)
 if name=='Luma':
  q.x*=.975;q.z=2.175+(z-2.175)*1.01
  if q.y<-.23 and 1.99<z<2.14:q.x*=1-.14*math.exp(-((z-2.075)/.05)**2);q.y+=.019*math.exp(-((q.x/.13)**4)-((z-2.075)/.06)**2)
 return q
reports={}
for name in ['Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'artwork_refinement_v10'/(name+'_candidate.blend')))
 retained=[]
 remove=('Ear','Eye','Iris','Pupil','Upper eyelid','Lower eyelid','Upper lash','Arched eyebrow','Brow','Smile','Upper smile','Nostril','Natural short','Soft tight','Tight short','Short curl','Rounded bob','Sculpted curved fringe','Silky bob','Kiki bob','Glossy fringe','Bob hair','Wavy hair','Tousled swept')
 for ob in list(bpy.context.scene.objects):
  if 'sculpted_head' in ob.name or ob.name.startswith(remove):bpy.data.objects.remove(ob,do_unlink=True)
  elif ob.type not in ['CAMERA','LIGHT']:retained.append(ob.name)
 with bpy.data.libraries.load(str(R/'amina_reconstruction_v35/Amina_anatomy_refinement_UNAPPROVED.blend'),link=False) as (a,b):
  b.objects=[n for n in a.objects if n.startswith(('Amina anatomy refinement','Amina seated eyeball','Amina brown iris','Amina pupil','Amina main eye reflection','Amina secondary reflection','V33 mouth interior','V33 curved upper teeth','V33 fitted eyebrow','V33 scalp fitted'))]
 imported=[]
 for ob in b.objects:
  if not ob:continue
  bpy.context.scene.collection.objects.link(ob);imported.append(ob)
  inv=ob.matrix_world.inverted()
  if ob.type=='MESH':
   for v in ob.data.vertices:v.co=inv@transform(ob.matrix_world@v.co,name)
   ob.data.update()
  elif ob.type=='CURVE':
   for sp in ob.data.splines:
    for p in sp.bezier_points:
     p.co=inv@transform(ob.matrix_world@p.co,name);p.handle_left=inv@transform(ob.matrix_world@p.handle_left,name);p.handle_right=inv@transform(ob.matrix_world@p.handle_right,name)
    for p in sp.points:p.co=(*tuple(inv@transform(ob.matrix_world@Vector(p.co[:3]),name)),p.co[3])
  ob.name=name+' V36 '+ob.name
 head=next(o for o in imported if 'anatomy refinement' in o.name)
 skin=mat(name+' V36 skin',{'Tebo':(.34,.10,.035),'Kiki':(.64,.33,.17),'Luma':(.67,.36,.20)}[name],.52)
 head.data.materials[0]=skin
 # Match retained exposed skin to the new face; preserve clothes, motifs and shoes.
 for ob in bpy.context.scene.objects:
  if ob not in imported and ob.type in ['MESH','CURVE']:
   for i,m in enumerate(ob.data.materials):
    if m and m.name=='Skin':ob.data.materials[i]=skin
 haircolor={'Tebo':(.025,.009,.003),'Kiki':(.014,.006,.003),'Luma':(.18,.064,.018)}[name]
 hair=mat(name+' V36 shaped hair',haircolor,.43)
 fibre=mat(name+' V36 hair fibre',haircolor,.44)
 for ob in imported:
  if 'scalp fitted' in ob.name or 'fitted eyebrow' in ob.name:
   ob.data.materials.clear();ob.data.materials.append(hair)
 bpy.context.view_layer.update()
 bvh=BVHTree.FromPolygons([head.matrix_world@v.co for v in head.data.vertices],[tuple(p.vertices) for p in head.data.polygons])
 centre=Vector((0,.025,2.3));paths=[]
 if name in ['Tebo','Luma']:
  for i in range(650 if name=='Tebo' else 400):
   a=random.uniform(0,math.tau);u=random.uniform(.18,1);rr=math.sqrt(1-u*u)
   direction=Vector((rr*math.cos(a),rr*math.sin(a),u));hit=bvh.ray_cast(centre,direction)
   if hit[0] is None:continue
   root,norm=hit[:2]
   if root.z<(2.38 if name=='Tebo' else 2.40):continue
   tangent=norm.cross(Vector((0,0,1)))
   if tangent.length<.01:tangent=Vector((1,0,0))
   tangent.normalize();bit=norm.cross(tangent).normalized()
   for child in range(18 if name=='Tebo' else 20):
    phase=random.random()*math.tau;off=tangent*random.uniform(-.013,.013)+bit*random.uniform(-.013,.013)
    path=[]
    for j in range(33):
     t=j/32
     if name=='Tebo':
      rad=.011+.008*math.sin(math.pi*t);p=root+off+norm*(.006+.067*t)+tangent*(rad*math.cos(t*math.tau*2.1+phase))+bit*(rad*math.sin(t*math.tau*2.1+phase))
     else:
      p=root+off+norm*(.012+.07*math.sin(math.pi*t))+Vector((-.16*t,.025*math.sin(t*math.pi),.04*math.sin(t*math.pi)-.016*t))+bit*(.014*math.sin(t*math.tau+phase))
     path.append(p)
    paths.append(path)
  curves(name+' V36 individual groom fibres',paths,fibre,.0014 if name=='Tebo' else .0013)
 else:
  # Continuous bob shell, curved front bangs and native strand paths.
  vs=[];fs=[];N=128
  rings=[(1.98,.385),(2.05,.40),(2.23,.40),(2.40,.39),(2.52,.345),(2.62,.26),(2.69,.14),(2.72,.006)]
  for z,rad in rings:
   for i in range(N):
    a=math.tau*i/N;vs.append((rad*math.cos(a),.04+.84*rad*math.sin(a),z))
  for j in range(len(rings)-1):
   for i in range(N):
    a=math.tau*(i+.5)/N
    if math.sin(a)<-.48 and j<4:continue
    k=j*N+i;l=j*N+(i+1)%N;fs.append((k,l,l+N,k+N))
  bob=mesh('Kiki V36 continuous bob shell',vs,fs,hair,2);bob.modifiers.new('Bob thickness','SOLIDIFY').thickness=.008
  vs=[];fs=[];bangpaths=[]
  for i in range(101):
   x=-.33+.66*i/100;path=[]
   for j in range(25):
    t=j/24;xx=x*(.3+.7*t);z=2.66-(.27+.025*math.sin(x*15))*t
    hit=bvh.ray_cast(Vector((xx,-1,z)),Vector((0,1,0)))
    y=hit[0].y-.018 if hit[0] else -.20
    p=(xx,y-.018*math.sin(math.pi*t),z);vs.append(p);path.append(p)
   bangpaths.append(path)
  for i in range(100):
   for j in range(24):k=i*25+j;fs.append((k,k+25,k+26,k+1))
  fringe=mesh('Kiki V36 fitted curved bangs',vs,fs,hair,1);fringe.modifiers.new('Bangs thickness','SOLIDIFY').thickness=.004
  for i in range(1100):
   a=random.uniform(-.48,math.pi+.48);side=-1 if i%2 else 1;path=[]
   for j in range(33):
    t=j/32;rad=.405*math.sin(math.pi*.5*min(1,t*1.9));x=side*rad*math.sin(a);y=.04+rad*.84*math.cos(a);z=2.724-.71*t
    path.append((x,y,z))
   paths.append(path)
  curves('Kiki V36 silky bob fibres',paths+bangpaths,fibre,.0009)
  # Fit the flower clip as a group, retaining its approved identity.
  clip=[o for o in bpy.context.scene.objects if o.name.startswith(('Hair clip centre','Clip petal'))]
  if clip:
   anchor=next((o for o in clip if o.name.startswith('Hair clip centre')),clip[0]);bb=[anchor.matrix_world@Vector(v) for v in anchor.bound_box];old=sum(bb,Vector())/8
   delta=Vector((-.337,-.195,2.42))-old
   for ob in clip:ob.location+=delta
 sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False;sc['character']=name;sc['status']='V36 anatomy-based modelling candidate'
 sc.cycles.samples=16;sc.cycles.device='CPU';sc.cycles.use_denoising=True;sc.render.image_settings.file_format='PNG';sc.render.resolution_percentage=100
 report={'production_ready':False,'visual_reference_passed':False,'rigged':False,'source_head':'Amina V35 anatomy topology with distinct per-character proportion adjustments','source_body':'V10 retained, exposed skin matched','retained_objects':retained,'new_head_mesh':audit(head),'groom_strands':len(paths),'limitations':['Shared anatomy base requires further character likeness refinement','V10 hands and clothes remain modelling candidates','No rig or deformation validation']}
 assert report['new_head_mesh']['finite'] and report['new_head_mesh']['overused_edges']==0 and report['new_head_mesh']['zero_area_faces']==0
 bpy.ops.wm.save_as_mainfile(filepath=str(O/(name+'_anatomy_candidate_UNAPPROVED.blend')))
 for view,loc,target,scale,size in [('front',(0,-7,1.65),(0,0,1.4),3.05,(600,820)),('face',(0,-7,2.2),(0,0,2.2),1.3,(640,640)),('three_quarter',(3,-6,2.2),(0,0,2.2),1.3,(640,640)),('profile',(6,-1,2.2),(0,0,2.2),1.3,(640,640))]:
  cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
  sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),*size);print('V36_RENDER_PASS',name,view,flush=True)
 report['png_validation_passed']=True;reports[name]=report;(O/(name+'_audit.json')).write_text(json.dumps(report,indent=2))
(O/'cast_audit.json').write_text(json.dumps(reports,indent=2));print('CAST_V36_COMPLETE',flush=True)
