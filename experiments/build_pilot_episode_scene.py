import bpy,math,json,hashlib,time,sys
import numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
R=Path(__file__).parent;E=R/'episodes/pilot-episode-01';O=E/'cgi';O.mkdir(exist_ok=True)
tim=json.loads((E/'timing.json').read_text());fps=tim['fps'];N=tim['total_frames']
bpy.ops.wm.open_mainfile(filepath=str(R/'artwork_refinement_v10/garden_candidate.blend'));sc=bpy.context.scene
# Preserve detailed environment geometry while reducing draw calls.
for ob in list(sc.objects):
 if ob.type in ['LIGHT','CAMERA'] or ob.name.startswith(('Watering can','Watering spout')):bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.view_layer.update()
groups={};dg=bpy.context.evaluated_depsgraph_get();original_count=len(sc.objects)
for ob in list(sc.objects):
 if ob.type not in ['MESH','CURVE','FONT','SURFACE']:continue
 ev=ob.evaluated_get(dg);me=ev.to_mesh()
 if me is None:continue
 coords=[tuple(ev.matrix_world@v.co) for v in me.vertices]
 local={}
 for poly in me.polygons:
  mat=me.materials[poly.material_index] if len(me.materials)>poly.material_index else None
  mat=bpy.data.materials.get(mat.name) if mat else None
  key=mat.name if mat else 'Unassigned'
  if key not in groups:groups[key]={'material':mat,'vertices':[],'faces':[],'smooth':[]}
  g=groups[key];mapping=local.setdefault(key,{})
  face=[]
  for vi in poly.vertices:
   if vi not in mapping:mapping[vi]=len(g['vertices']);g['vertices'].append(coords[vi])
   face.append(mapping[vi])
  g['faces'].append(face);g['smooth'].append(poly.use_smooth)
 ev.to_mesh_clear()
environment_collection=bpy.data.collections.new('Reusable Giggle Garden environment');sc.collection.children.link(environment_collection)
for ob in list(sc.objects):
 if ob.type in ['MESH','CURVE','FONT','SURFACE']:bpy.data.objects.remove(ob,do_unlink=True)
for key,g in groups.items():
 me=bpy.data.meshes.new('Garden baked '+key);me.from_pydata(g['vertices'],[],g['faces']);me.update()
 if g['material']:me.materials.append(g['material'])
 ob=bpy.data.objects.new('Garden '+key,me);environment_collection.objects.link(ob)
 for p,smooth in zip(me.polygons,g['smooth']):p.use_smooth=smooth
print('ENVIRONMENT_DRAW_CALL_BATCHING',original_count,len(groups),flush=True)
bpy.context.view_layer.update()
inputs=json.loads((R/'pilot_rig_inputs.json').read_text())
actors={};sources={};actor_objects={}
order=['Tebo','Kiki','Luma','Amina'];positions={n:Vector((-2.1+1.4*i,-3.1,-.033)) for i,n in enumerate(order)}
for name in order:
 path=R/'pilot_rigs_v3'/(name+'_pilot_rig.blend');sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
 allowed={ob['name'] for ob in inputs[name]}|{name+'_PilotRig'}
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):
  dst.objects=[n for n in src.objects if n in allowed or n.startswith(name+' Blink lid') or n.startswith(name+' blink crease')]
 col=bpy.data.collections.new(name+' pilot character');sc.collection.children.link(col);objects=[]
 for ob in dst.objects:
  if not ob or ob.type in ['CAMERA','LIGHT']:continue
  col.objects.link(ob);objects.append(ob)
 print('ACTOR_LINKED',name,len(objects),flush=True);bpy.context.view_layer.update()
 rig=next(o for o in objects if o.type=='ARMATURE');rig.location=positions[name];actors[name]=rig;actor_objects[name]=objects
 for ob in objects:ob['pilot_character']=name
 # Render-only groom reduction; source character and rig files unchanged.
 for ob in objects:
  if ob.type!='CURVES':continue
  old=ob.data;attr=old.attributes.get('position');npts=len(attr.data) if attr else 0
  if 'detailed puff' in ob.name and npts%33==0:
   p=np.empty(npts*3,dtype=np.float32);attr.data.foreach_get('vector',p);p=p.reshape(-1,33,3)[::5].copy()
   rr=np.empty(npts,dtype=np.float32);old.attributes['radius'].data.foreach_get('value',rr);rr=rr.reshape(-1,33)[::5].copy()*1.5
   d=bpy.data.hair_curves.new(name+' pilot distance groom');d.add_curves([33]*len(p));d.attributes['position'].data.foreach_set('vector',p.reshape(-1));d.attributes.new(name='radius',type='FLOAT',domain='POINT').data.foreach_set('value',rr.reshape(-1))
   for m in old.materials:d.materials.append(m)
   ob.data=d
  for i,m in enumerate(ob.data.materials):
   if not m or not m.use_nodes:continue
   hair=next((nd for nd in m.node_tree.nodes if nd.bl_idname=='ShaderNodeBsdfHairPrincipled'),None)
   if hair:
    c=bpy.data.materials.new(name+' pilot EEVEE fibres');c.use_nodes=True;sh=c.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=hair.inputs['Color'].default_value;sh.inputs['Roughness'].default_value=.48;sh.inputs['Specular IOR Level'].default_value=.22;ob.data.materials[i]=c
 for pb in rig.pose.bones:pb.rotation_mode='XYZ'
 for side in ['L','R']:rig.pose.bones['forearm.'+side].constraints['Pilot hand IK'].influence=1
 bpy.context.view_layer.update();print('ACTOR_UPDATED',name,flush=True)
print('FOUR_CURRENT_PILOT_RIGS_APPENDED',flush=True)
def material(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
wood=material('Pilot seedling tray warm cedar',(.38,.20,.095));soil=material('Pilot rich garden soil',(.10,.045,.022));green=material('Pilot seedling leaves',(.15,.40,.07));stemmat=material('Pilot tender stems',(.20,.42,.08));pink=material('Pilot enamel pink can',(.66,.055,.28),.28,.05);rim=material('Pilot pale pink can trim',(.90,.26,.49),.32);watermat=material('Pilot water glints',(.32,.70,.90),.18)
def mesh(name,verts,faces,mat,parent=None):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);sc.collection.objects.link(ob)
 if mat:me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if parent:ob.parent=parent
 return ob
def box(name,loc,scale,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(mat);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=ob.modifiers.new('Soft crafted edges','BEVEL');b.width=.025;b.segments=3;ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');return ob
def tube(name,points,radius,mat,parent=None):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3;sp=c.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,c);sc.collection.objects.link(ob);c.materials.append(mat)
 if parent:ob.parent=parent
 return ob
box('Four little seedlings soil',(0,-4.04,.10),(5.95,.76,.16),soil)
for y in [-4.47,-3.61]:box('Cedar seedling tray long rail',(0,y,.16),(6.10,.08,.26),wood)
for x in [-3.04,3.04]:box('Cedar seedling tray end',(x,-4.04,.16),(.08,.9,.26),wood)
for name in order:
 x=positions[name].x+.28
 tube(name+' tender seedling stem',[(x,-4.01,.18),(x-.012,-4.01,.35),(x+.015,-4.01,.52)],.017,stemmat)
 for side in [-1,1]:
  for h,length in [(.31,.22),(.42,.18)]:
   verts=[];faces=[]
   for k in range(13):
    t=k/12;xx=x+side*length*t;yy=-4.01+.03*math.sin(t*math.pi);zz=h+.14*math.sin(t*math.pi/2)
    width=.067*math.sin(math.pi*t)
    verts.extend([(xx,yy-width,zz),(xx,yy+width,zz)])
   for k in range(12):i=2*k;faces.append((i,i+1,i+3,i+2))
   leaf=mesh(name+' curved seedling leaf',verts,faces,green);s=leaf.modifiers.new('Leaf thickness','SOLIDIFY');s.thickness=.004
# Two small potting stands give the can a reachable resting surface.
for x in [-2.1,2.1]:
 box('Potting stand cedar top',(x,-3.52,.64),(.53,.48,.06),wood)
 for dx in [-.20,.20]:
  for dy in [-.17,.17]:box('Potting stand wooden leg',(x+dx,-3.52+dy,.315),(.055,.055,.63),wood)
can=bpy.data.objects.new('One shared pink watering can',None);sc.collection.objects.link(can)
# Hollow lathed vessel with a rolled lip, rather than a solid primitive.
rings=[(0,.115),(.018,.155),(.07,.18),(.24,.18),(.30,.155),(.312,.153),(.31,.14),(.295,.139),(.075,.166),(.035,.14)]
verts=[];faces=[];segments=48
for z,r in rings:
 for i in range(segments):a=2*math.pi*i/segments;verts.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(rings)-1):
 for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;faces.append((a,b,b+segments,a+segments))
faces.append(tuple(reversed(range(segments))));faces.append(tuple(range((len(rings)-1)*segments,len(rings)*segments)))
mesh('Crafted hollow pink watering vessel',verts,faces,pink,can)
tube('Arch handle on pink can',[(-.155,0,.24),(-.22,0,.36),(-.15,0,.46),(0,0,.50),(.15,0,.46),(.22,0,.36),(.155,0,.24)],.019,rim,can)
tube('Pink can tapered spout',[(0,-.13,.13),(0,-.23,.14),(0,-.34,.21),(0,-.43,.26)],.032,pink,can)
tube('Rolled watering can lip',[(.151*math.cos(i*math.pi/8),.151*math.sin(i*math.pi/8),.31) for i in range(17)],.007,rim,can)
# Daisy medallion on front-facing vessel side.
for i in range(5):
 a=i*2*math.pi/5;bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(.052*math.cos(a),-.179,.16+.052*math.sin(a)));ob=bpy.context.object;ob.name='Pink can daisy petal';ob.scale=(.030,.006,.019);ob.parent=can;ob.data.materials.append(rim)
stream=tube('Gentle animated watering stream',[(0,0,0),(0,0,-.25),(0,0,-.70)],.009,watermat)
# Add falling drops animated independently of the can.
drops=[]
for i in range(12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.014);ob=bpy.context.object;ob.name='Water drop '+str(i);ob.scale=(.7,.7,1.45);ob.data.materials.append(watermat);drops.append(ob)
def smooth(v):
 v=max(0,min(1,v));return v*v*(3-2*v)
def lerp(a,b,u):return Vector(a).lerp(Vector(b),u)
def scene_at(t):
 for s in reversed(tim['scenes']):
  if t>=s['start']-1e-6:return s,t-s['start']
 return tim['scenes'][0],0
def can_state(s,local):
 idx=s['index'];owner=order[max(0,min(3,idx-3))]
 if idx<3:return Vector((-2.1,-3.52,.67)),0,None,None,0
 if idx>6:return Vector((2.1,-3.52,.67)),0,None,None,0
 if idx==3:
  lift=smooth((local-1)/2);pos=Vector((positions[owner].x,-3.52,.67+.11*lift));prev=None;u=1
 else:
  prev=order[idx-4];u=smooth((local-.25)/2.75)
  pos=lerp((positions[prev].x,-3.52,.78),(positions[owner].x,-3.52,.78),u)
  pos.y+=.17*math.sin(math.pi*u);pos.z+=.18*math.sin(math.pi*u)
 tip=.32*smooth((local-5.5)/.5)*(1-smooth((local-8.8)/.5))
 if idx==6:
  down=smooth((local-10)/2);pos.z-=.11*down
 return pos,tip,owner,prev,u
rest={'L':Vector((.475,-.043,.94)),'R':Vector((-.475,-.043,.94))}
def pose_key(rig,side,target,frame):
 pb=rig.pose.bones['hand_ik.'+side];pb.location=target-rig.data.bones[pb.name].head_local;pb.keyframe_insert('location',frame=frame,group='Hands')
for frame in sorted(set(range(1,N+1,6))|{N}|{round(s['start']*fps)+1 for s in tim['scenes']}):
 t=(frame-1)/fps;s,local=scene_at(t);pos,tip,owner,prev,u=can_state(s,local)
 can.location=pos;can.rotation_euler=(tip,0,0);can.keyframe_insert('location',frame=frame);can.keyframe_insert('rotation_euler',frame=frame)
 rot=can.rotation_euler.to_matrix()
 for k,name in enumerate(order):
  rig=actors[name];targets={side:p.copy() for side,p in rest.items()}
  if owner==name:
   target={side:pos+rot@Vector((.19 if side=='L' else -.19,.02,.31))-positions[name] for side in ['L','R']}
   hold=smooth((local-1)/2) if s['index']==3 else smooth((u-.38)/.12) if prev else 1
   if prev and u<.80:
    target['R']=pos+Vector((.19,.02,.31))-positions[name]
    targets['R']=lerp(rest['R'],target['R'],hold)
    targets['L']=lerp(rest['L'],target['L'],smooth((u-.75)/.20))
   else:
    for side in ['L','R']:targets[side]=lerp(rest[side],target[side],hold)
   if s['index']==6 and local>12:
    release=1-smooth((local-12)/1.2)
    for side in ['L','R']:targets[side]=lerp(rest[side],targets[side],release)
  elif prev==name and u<.65:
   for side in ['L','R']:
    xedge=.19 if side=='L' else -.19
    if side=='L':xedge=.19-.38*smooth(u/.23)
    target=pos+Vector((xedge,.02,.31))-positions[name]
    fade=1-smooth((u-.54)/.10) if side=='L' else 1-smooth(u/.25)
    targets[side]=lerp(rest[side],target,fade)
  if s['index']==0:
   start=1.5+k*.75;w=smooth((local-start)/.65)*(1-smooth((local-start-3.2)/.75))
   wave=Vector((.48+.015*math.sin(local*6),-.30,1.50+.015*math.sin(local*6)))
   targets['L']=lerp(targets['L'],wave,w)
  elif s['index']==1 and name in ['Tebo','Kiki']:
   side='L' if name=='Tebo' else 'R';sgn=1 if side=='L' else -1
   w=smooth((local-2)/1.2)*(1-smooth((local-9)/1.4))
   targets[side]=lerp(targets[side],(sgn*.35,-.30,1.16),w)
  elif s['index']==2 and name=='Amina':
   w=smooth((local-1)/.8)*(1-smooth((local-7)/1.2));targets['R']=lerp(targets['R'],(-.48,-.30,1.50),w)
  elif s['index']==8:
   w=smooth((local-6)/1)*(1-smooth((local-13)/1))
   targets['L']=lerp(targets['L'],(.48+.018*math.sin(local*7+k),-.30,1.50+.018*math.cos(local*7+k)),w)
  for side in ['L','R']:pose_key(rig,side,targets[side],frame)
  pb=rig.pose.bones['spine'];pb.rotation_euler.x=.012*math.sin(t*1.6+k)+(tip*.15 if owner==name else 0);pb.keyframe_insert('rotation_euler',frame=frame,group='Body')
  pb=rig.pose.bones['head'];pb.rotation_euler=(.025*math.sin(t*2+k)+(.075 if owner==name and tip else 0),.045*math.sin(t*.8+k),.025*math.sin(t*1.1+k));pb.keyframe_insert('rotation_euler',frame=frame,group='Expression')
  if s['index']==2 and local>7 and local<11:pb.rotation_euler.x+=.075*math.sin((local-7)*5);pb.keyframe_insert('rotation_euler',frame=frame,group='Expression')
 # Stream endpoint follows spout; water only during the three-second pour.
 flowing=owner is not None and 6<=local<=9 and 3<=s['index']<=6
 mouth=pos+rot@Vector((0,-.43,.26));stream.location=mouth;stream.scale=(1,1,max(.01,(mouth.z-.19)/.70));stream.keyframe_insert('location',frame=frame);stream.keyframe_insert('scale',frame=frame);stream.hide_render=not flowing;stream.keyframe_insert('hide_render',frame=frame)
 for i,ob in enumerate(drops):
  phase=(t*2.2+i/12)%1;ob.location=(mouth.x+.014*math.sin(i*3),mouth.y+.014*math.cos(i*2),mouth.z-(mouth.z-.19)*phase)
  ob.keyframe_insert('location',frame=frame);ob.hide_render=not flowing;ob.keyframe_insert('hide_render',frame=frame)
# Staggered, brief blinks; eyes are fully open between them.
for k,name in enumerate(order):
 for ob in actor_objects[name]:
  if 'Blink lid' in ob.name:
   key=ob.data.shape_keys.key_blocks['Blink'];key.value=0;key.keyframe_insert('value',frame=1)
   for b in range(70+k*21,N-8,102+k*7):
    for f,v in [(b,0),(b+2,1),(b+4,1),(b+7,0)]:key.value=v;key.keyframe_insert('value',frame=f)
   key.value=0;key.keyframe_insert('value',frame=N)
  if 'blink crease' in ob.name:
   ob.hide_viewport=False;ob.hide_render=True;ob.keyframe_insert('hide_render',frame=1)
   for b in range(70+k*21,N-8,102+k*7):
    for f,v in [(b,True),(b+2,False),(b+5,True)]:ob.hide_render=v;ob.keyframe_insert('hide_render',frame=f)
   ob.hide_render=True;ob.keyframe_insert('hide_render',frame=N)
cameras=[]
for s in tim['scenes']:
 i=s['index'];start=round(s['start']*fps)+1;end=start+s['frames']-1
 if 3<=i<=6:
  x=positions[order[i-3]].x;loc=Vector((x+1.25,-9.3,3.2));target=Vector((x,-3.63,1.18));lens=39
 elif i==0:loc=Vector((3.3,-13.4,6.7));target=Vector((0,-.25,1.65));lens=43
 elif i==7:loc=Vector((-2.6,-12.2,5.7));target=Vector((0,-2.0,1.15));lens=44
 else:loc=Vector((.65,-12,3.7));target=Vector((0,-3.13,1.3));lens=44
 d=bpy.data.cameras.new('Pilot shot '+str(i+1));cam=bpy.data.objects.new('Pilot shot '+str(i+1),d);sc.collection.objects.link(cam);d.lens=lens;d.clip_end=100
 cam.location=loc;cam.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=start);cam.keyframe_insert('rotation_euler',frame=start)
 cam.location=loc+Vector((-.10,-.18,-.02));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert('location',frame=end);cam.keyframe_insert('rotation_euler',frame=end)
 marker=sc.timeline_markers.new(s['action'],frame=start);marker.camera=cam;cameras.append(cam)
sc.camera=cameras[0]
def area(name,loc,energy,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
 ob=bpy.data.objects.new(name,d);sc.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Warm garden key',(-4,-8,9),700,7,(0,-2,1))
area('Soft face fill',(4,-7,5),400,6,(0,-3,1.5))
d=bpy.data.lights.new('Gentle sun','SUN');d.energy=1.0;d.angle=.14;ob=bpy.data.objects.new('Gentle sun',d);sc.collection.objects.link(ob);ob.rotation_euler=(.4,-.4,-.3)
world=bpy.data.worlds.new('Pilot pale blue sky');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.36,.57,.75,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.35;sc.world=world
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True;sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.view_settings.look='None'
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.fps=fps
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=15
sc.render.film_transparent=False;sc.frame_start=1;sc.frame_end=N
sc['pilot_style_authorized']=True;sc['original_reference_passed']=False;sc['production_ready']=False;sc['title']='Everyone Gets a Turn'
sc.frame_set(1);bpy.context.view_layer.update()
path=O/'Everyone_Gets_a_Turn_pilot.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
report={'blend':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cast_source_rig_sha256':sources,'fps':fps,'total_frames':N,'duration':N/fps,'static_environment_objects_before':original_count,'static_environment_material_batches':len(groups),'real_character_animation':True,'narrator_lipsync_required':False,'visual_qa_passed':False,'production_ready':False,'shots':[{'index':s['index'],'action':s['action'],'start_frame':round(s['start']*fps)+1,'frames':s['frames']} for s in tim['scenes']]}
(O/'scene_build_report.json').write_text(json.dumps(report,indent=2))
print('PILOT_SCENE_ANIMATED_AND_SAVED',N,'frames',flush=True)
