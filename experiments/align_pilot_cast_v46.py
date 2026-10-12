import bpy,bmesh,math,json,array,sys,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'cast_pilot_v46';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from png_validation import valid_png
def audit(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);unseen=set(bm.verts);parts=[]
 while unseen:
  seed=unseen.pop();stack=[seed];n=0
  while stack:
   v=stack.pop();n+=1
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);stack.append(q)
  parts.append(n)
 a={'vertices':len(bm.verts),'faces':len(bm.faces),'components':parts,'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co)};bm.free();return a
def close_body(body):
 bm=bmesh.new();bm.from_mesh(body.data)
 for v in bm.verts:v.co=body.matrix_world@v.co
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,1.55),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
 bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.matrix_world=Matrix.Identity(4)
 for m in list(body.modifiers):body.modifiers.remove(m)
def rebuild_neck(head):
 plane={'Tebo':1.691125,'Kiki':1.7142,'Luma':1.69645}[name]
 bm=bmesh.new();bm.from_mesh(head.data)
 for v in bm.verts:v.co=head.matrix_world@v.co
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,plane),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
 adj={}
 for e in bm.edges:
  if e.is_boundary:
   for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
 assert adj and all(len(v)==2 for v in adj.values())
 start=next(iter(adj));ring=[start];prev=None;cur=start
 while True:
  nxt=next(v for v in adj[cur] if v!=prev)
  if nxt==start:break
  assert nxt not in ring;ring.append(nxt);prev,cur=cur,nxt
 if len(ring)!=len(adj):
  remaining=set(adj);loops=[]
  while remaining:
   seed=remaining.pop();todo=[seed];vs=[seed]
   while todo:
    v=todo.pop()
    for q in adj[v]:
     if q in remaining:remaining.remove(q);todo.append(q);vs.append(q)
   loops.append({'vertices':len(vs),'center':[sum(v.co[i] for v in vs)/len(vs) for i in range(3)]})
  (O/(name+'_cut_diagnostic.json')).write_text(json.dumps(loops,indent=2));print('CUT_LOOP_DIAGNOSTIC',name,json.dumps(loops),flush=True)
 assert len(ring)==len(adj)
 original=[v.co.copy() for v in ring];last=ring
 for t,z in [(0.28,plane-.008),(0.62,plane-.020),(1.,plane-.045),(1.,1.60),(1.,1.54),(1.,1.48)]:
  new=[]
  for p in original:
   a=math.atan2((p.y-.015)/.085,p.x/.09);cy=.09*max(0,min(1,(z-1.48)/.195));q=p.lerp(Vector((.09*math.cos(a),cy+.085*math.sin(a),z)),t);q.z=z;new.append(bm.verts.new(q))
  for i in range(len(ring)):bm.faces.new((last[i],last[(i+1)%len(ring)],new[(i+1)%len(ring)],new[i])).material_index=0
  last=new
 bm.faces.new(tuple(reversed(last))).material_index=0
 safe=[v for v in bm.verts if 1.72<v.co.z<1.92 and all(f.material_index==0 for f in v.link_faces)]
 for _ in range(5):bmesh.ops.smooth_vert(bm,verts=safe,factor=.20,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free();head.matrix_world=Matrix.Identity(4);head.data.update()
def smooth_cap(head,old,name):
 bm=bmesh.new();bm.from_mesh(head.data)
 def edge(q):
  s=(q.y-.01)/max(1e-6,math.hypot(q.x,q.y-.01));return 2.16+(.12 if name=='Tebo' else .14)*(math.sqrt(s*s+.01)-s)/2
 for v in bm.verts:v.co.z-=edge(v.co)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,0),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
 for v in bm.verts:v.co.z+=edge(v.co)
 unseen=set(bm.verts);groups=[]
 while unseen:
  seed=unseen.pop();g={seed};stack=[seed]
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);g.add(q);stack.append(q)
  groups.append(g)
 keep=max(groups,key=len);discard=[v for g in groups if g is not keep for v in g]
 if discard:bmesh.ops.delete(bm,geom=discard,context='VERTS')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
 for v in bm.verts:v.co+=v.normal*.005
 m=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
 d=bpy.data.meshes.new(name+' fitted scalp');bm.to_mesh(d);bm.free();d.update();d.materials.append(m)
 for p in d.polygons:p.material_index=0;p.use_smooth=True
 ob=bpy.data.objects.new(name+' V46 smooth fitted scalp',d);bpy.context.scene.collection.objects.link(ob)
def project_kiki():
 objects=[o for o in bpy.context.scene.objects if any(t in o.name for t in ['continuous bob shell','continuous curved bangs'])]
 vs=[];fs=[];deps=bpy.context.evaluated_depsgraph_get()
 for ob in objects:
  ev=ob.evaluated_get(deps);me=ev.to_mesh();offset=len(vs);vs.extend([ob.matrix_world@v.co for v in me.vertices]);fs.extend([tuple(i+offset for i in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
 bvh=BVHTree.FromPolygons(vs,fs);count=0
 for ob in bpy.context.scene.objects:
  if ob.type!='CURVES' or 'surface following bob fibres' not in ob.name:continue
  att=ob.data.attributes['position'];raw=array.array('f',[0])*(len(att.data)*3);att.data.foreach_get('vector',raw);new=array.array('f');inv=ob.matrix_world.inverted()
  for i in range(0,len(raw),3):
   q=ob.matrix_world@Vector(raw[i:i+3]);hit=bvh.find_nearest(q);new.extend(inv@(hit[0]+hit[1]*.0017))
  att.data.foreach_set('vector',new);count+=len(att.data)
 return count
reports={}
for name in ['Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'cast_anatomy_v39'/(name+'_anatomy_candidate_UNAPPROVED.blend')))
 head=next(o for o in bpy.context.scene.objects if 'anatomy refinement' in o.name);body=next(o for o in bpy.context.scene.objects if 'connected body with shaped hands' in o.name)
 rebuild_neck(head);close_body(body)
 bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head;bpy.context.view_layer.update()
 mod=head.modifiers.new('Pilot continuous skin union','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(body,do_unlink=True)
 head.name=name+' V46 continuous pilot character skin'
 bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
 seam=[v for v in bm.verts if 1.49<v.co.z<1.60]
 for _ in range(5):bmesh.ops.smooth_vert(bm,verts=seam,factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free();head.data.update()
 for p in head.data.polygons:p.use_smooth=True
 # Match Amina's readable happy expression, retaining individual nose/head proportions.
 for ob in bpy.context.scene.objects:
  if ob.type=='CURVE' and 'fitted eyebrow' in ob.name:ob.data.bevel_depth*=1.6
  if ob.type=='MESH' and (ob==head or 'mouth interior' in ob.name or 'curved upper teeth' in ob.name):
   inv=ob.matrix_world.inverted()
   for v in ob.data.vertices:
    q=ob.matrix_world@v.co;dz=q.z-1.8086
    if q.y<-.13 and abs(q.x)<.23 and abs(dz)<.12:
     w=math.exp(-(dz/.09)**4-(abs(q.x)/.20)**8);q.x+=q.x*.10*w;q.z-=.08*max(0,dz)*w
    v.co=inv@q
   ob.data.update()
 shader=head.data.materials[0].node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.49
 if shader.inputs.get('Subsurface Weight'):shader.inputs['Subsurface Weight'].default_value=.06
 if shader.inputs.get('Subsurface Scale'):shader.inputs['Subsurface Scale'].default_value=.02
 m=bpy.data.materials.new(name+' pilot tongue');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.46,.065,.09,1);p.inputs['Roughness'].default_value=.48
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=(0,-.245,1.767));tongue=bpy.context.object;tongue.name=name+' V46 tongue'
 for v in tongue.data.vertices:v.co.x*=.070;v.co.y*=.033;v.co.z*=.014
 tongue.data.materials.append(m)
 for p in tongue.data.polygons:p.use_smooth=True
 projected=0
 if name!='Kiki':
  old=next(o for o in bpy.context.scene.objects if 'scalp fitted' in o.name);smooth_cap(head,old,name)
 else:projected=project_kiki()
 # Native groom shading matches Amina's physical fibre treatment.
 m=bpy.data.materials.new(name+' V46 physical hair');m.use_nodes=True;m.node_tree.nodes.clear();out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');hair=m.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled');hair.parametrization='COLOR';hair.inputs['Color'].default_value={'Tebo':(.025,.009,.003),'Kiki':(.022,.011,.006),'Luma':(.18,.064,.018)}[name]+(1,);hair.inputs['Roughness'].default_value=.42;m.node_tree.links.new(hair.outputs[0],out.inputs['Surface'])
 for ob in bpy.context.scene.objects:
  if ob.type=='CURVES':ob.data.materials.clear();ob.data.materials.append(m)
  if ob.type=='MESH' and any(t in ob.name for t in ['hoodie','garment']):
   subs=[a for a in ob.modifiers if a.type=='SUBSURF']
   for a in subs[:-1]:ob.modifiers.remove(a)
   if subs:subs[-1].levels=1;subs[-1].render_levels=1
 a=audit(head);assert a['finite'] and a['boundary_edges']==0 and a['overused_edges']==0 and a['zero_area_faces']==0 and len(a['components'])==1,(name,a)
 sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['pilot_style_authorized']=True;sc['rigged']=False;sc.cycles.samples=16;sc.cycles.device='CPU';sc.cycles.use_denoising=True
 path=O/(name+'_pilot_character.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path))
 for view,loc,target,scale,size in [('front',(0,-7,1.65),(0,0,1.4),3.05,(600,820)),('face',(0,-7,2.1),(0,0,2.1),1.3,(640,640)),('three_quarter',(3,-6,2.1),(0,0,2.1),1.3,(640,640)),('profile',(6,-1,2.1),(0,0,2.1),1.3,(640,640))]:
  cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),*size);print('V46_REVIEW_PASS',name,view,flush=True)
 bpy.ops.wm.open_mainfile(filepath=str(path))
 reports[name]={'skin':a,'pilot_style_authorized':True,'production_ready':False,'visual_reference_passed':False,'rigged':False,'blend_reopen_passed':True,'png_validation_passed':True,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'projected_bob_hair_points':projected,'changes':['Continuous head/body skin and reconstructed neck','Matched happy expression, tongue and skin/fibre shading to Amina current standard','Preserved individual hair, clothes and motifs'],'remaining':['Pilot rigging and deformation checks','Episode animation, audio and final-video verification']}
 (O/(name+'_audit.json')).write_text(json.dumps(reports[name],indent=2))
(O/'cast_audit.json').write_text(json.dumps(reports,indent=2));print('PILOT_CAST_V46_COMPLETE',flush=True)
