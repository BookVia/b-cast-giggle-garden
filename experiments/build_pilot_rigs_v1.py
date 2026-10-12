import bpy, math, json, hashlib, sys, time
from pathlib import Path
from collections import defaultdict
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
R=Path(__file__).parent
O=R/'pilot_rigs_v1'; O.mkdir(exist_ok=True)
reg=json.loads((R/'CURRENT_PRODUCTION_ASSETS.json').read_text())
sys.path.insert(0,str(R))
from png_validation import valid_png
def mix(a,b,t):
 t=max(0.,min(1.,t));t=t*t*(3-2*t)
 return {a:1-t,b:t} if a!=b else {a:1.}
def weights(p,skirt=False):
 x,y,z=p; ax=abs(x);side='L' if x>=0 else 'R'
 if z>=1.72:return {'head':1.}
 if z>=1.50:return mix('neck','head',(z-1.50)/.22)
 if skirt and ax<.42 and z<1.1:return {'hips':1.}
 if ax>.285 and .70<z<1.50:
  if z>1.25:
   arm={'upper_arm.'+side:1.}
  elif z>1.07:arm=mix('forearm.'+side,'upper_arm.'+side,(z-1.07)/.17)
  elif z>.96:arm={'forearm.'+side:1.}
  elif z>.90:arm=mix('hand.'+side,'forearm.'+side,(z-.90)/.08)
  else:arm={'hand.'+side:1.}
  if ax<.36 and z>1.20:
   w=(ax-.285)/.075;w=max(0.,min(1.,w));arm={k:v*w for k,v in arm.items()};arm['chest']=1-w
  return arm
 if z<.96:
  if z>.82:return mix('thigh.'+side,'hips',(z-.82)/.14)
  if z>.56:return {'thigh.'+side:1.}
  if z>.44:return mix('shin.'+side,'thigh.'+side,(z-.44)/.12)
  if z>.28:return {'shin.'+side:1.}
  return mix('foot.'+side,'shin.'+side,(z-.18)/.10)
 if z<1.14:return mix('hips','spine',(z-.96)/.18)
 if z<1.35:return mix('spine','chest',(z-1.14)/.21)
 return {'chest':1.}
def apply_weights(ob,records,rig):
 for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
 buckets=defaultdict(list)
 for i,ws in enumerate(records):
  assert abs(sum(ws.values())-1)<1e-6,(ob.name,i,ws)
  for bn,w in ws.items():
   if w>1e-8:buckets[(bn,round(w,4))].append(i)
 groups={}
 for (bn,w),ids in buckets.items():
  if bn not in groups:groups[bn]=ob.vertex_groups.new(name=bn)
  groups[bn].add(ids,w,'REPLACE')
 world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_parent_inverse=rig.matrix_world.inverted();ob.matrix_world=world
 mod=ob.modifiers.new('Pilot anatomical skin deformation','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
def rigid_parent(ob,rig,bone):
 old=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone
 bpy.context.view_layer.update();ob.matrix_world=old
 bpy.context.view_layer.update()
 err=max(abs(ob.matrix_world[i][j]-old[i][j]) for i in range(4) for j in range(4))
 assert err<1e-5,(ob.name,err)
 return err
def mesh_sample(ob):
 dg=bpy.context.evaluated_depsgraph_get();e=ob.evaluated_get(dg);me=e.to_mesh()
 ids=list(range(0,len(me.vertices),max(1,len(me.vertices)//80)))
 result=[e.matrix_world@me.vertices[i].co for i in ids];e.to_mesh_clear()
 return result
def arm_target(rig,side,world_pos,influence=1):
 ctrl=rig.pose.bones['hand_ik.'+side];ctrl.location=Vector(world_pos)-rig.data.bones[ctrl.name].head_local
 rig.pose.bones['forearm.'+side].constraints['Pilot hand IK'].influence=influence
def reset_pose(rig):
 for pb in rig.pose.bones:
  pb.location=(0,0,0);pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.scale=(1,1,1)
  for c in pb.constraints:
   if c.type=='IK':c.influence=0
 bpy.context.view_layer.update()
reports={}
for name in ['Amina','Tebo','Kiki','Luma']:
 t=time.time();src=R/reg['assets'][name]['blend'];bpy.ops.wm.open_mainfile(filepath=str(src))
 sc=bpy.context.scene
 assets=[o for o in sc.objects if o.type in ['MESH','CURVE','CURVES']]
 skin=next(o for o in assets if o.type=='MESH' and 'continuous' in o.name.lower() and len(o.data.vertices)>60000)
 baseline=mesh_sample(skin)
 ar=bpy.data.armatures.new(name+' Pilot anatomical skeleton')
 rig=bpy.data.objects.new(name+'_PilotRig',ar);sc.collection.objects.link(rig)
 bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 bones={}
 def bone(n,h,t,parent=None,deform=True):
  b=ar.edit_bones.new(n);b.head=h;b.tail=t;b.use_deform=deform
  if parent:b.parent=bones[parent]
  bones[n]=b;return b
 bone('root',(0,0,0),(0,0,.35),deform=False)
 bone('hips',(0,0,.85),(0,0,.98),'root')
 bone('spine',(0,0,.98),(0,0,1.23),'hips')
 bone('chest',(0,0,1.23),(0,0,1.48),'spine')
 bone('neck',(0,0,1.48),(0,0,1.68),'chest')
 bone('head',(0,0,1.68),(0,0,2.50),'neck')
 for side,s in [('L',1),('R',-1)]:
  bone('clavicle.'+side,(0,0,1.44),(s*.245,0,1.44),'chest')
  bone('upper_arm.'+side,(s*.245,0,1.44),(s*.435,-.016,1.15),'clavicle.'+side)
  bone('forearm.'+side,(s*.435,-.016,1.15),(s*.475,-.043,.94),'upper_arm.'+side)
  bone('hand.'+side,(s*.475,-.043,.94),(s*.476,-.06,.84),'forearm.'+side)
  bone('hand_ik.'+side,(s*.475,-.043,.94),(s*.475,.057,.94),'root',False)
  bone('thigh.'+side,(s*.14,0,.85),(s*.15,-.018,.50),'hips')
  bone('shin.'+side,(s*.15,-.018,.50),(s*.15,0,.23),'thigh.'+side)
  bone('foot.'+side,(s*.15,0,.23),(s*.15,-.16,.15),'shin.'+side)
  bone('foot_ik.'+side,(s*.15,0,.23),(s*.15,-.16,.23),'root',False)
 bpy.ops.object.mode_set(mode='OBJECT')
 for side in ['L','R']:
  c=rig.pose.bones['forearm.'+side].constraints.new('IK');c.name='Pilot hand IK';c.target=rig;c.subtarget='hand_ik.'+side;c.chain_count=2;c.use_stretch=False;c.influence=0
  c=rig.pose.bones['shin.'+side].constraints.new('IK');c.name='Pilot foot IK';c.target=rig;c.subtarget='foot_ik.'+side;c.chain_count=2;c.use_stretch=False;c.influence=0
 coords=[skin.matrix_world@v.co for v in skin.data.vertices]
 records=[weights(p) for p in coords];apply_weights(skin,records,rig)
 kd=KDTree(len(coords))
 for i,p in enumerate(coords):kd.insert(p,i)
 kd.balance();bound=[];attachment_error=0
 for ob in assets:
  if ob==skin:continue
  bb=[ob.matrix_world@Vector(v) for v in ob.bound_box]
  zmin=min(v.z for v in bb);zmax=max(v.z for v in bb)
  if zmin>1.59:
   attachment_error=max(attachment_error,rigid_parent(ob,rig,'head'));bound.append([ob.name,'head'])
  elif ob.type=='MESH':
   skirt='flared dress' in ob.name.lower()
   ws=[weights(ob.matrix_world@v.co,True) if skirt else records[kd.find(ob.matrix_world@v.co)[1]].copy() for v in ob.data.vertices]
   apply_weights(ob,ws,rig);bound.append([ob.name,'weighted'])
  else:
   center=sum(bb,Vector())/8
   bn=max(weights(center),key=weights(center).get)
   attachment_error=max(attachment_error,rigid_parent(ob,rig,bn));bound.append([ob.name,bn])
 bpy.context.view_layer.update()
 after=mesh_sample(skin);rest_error=max((a-b).length for a,b in zip(baseline,after))
 assert rest_error<1e-5,rest_error
 for pb in rig.pose.bones:pb.rotation_mode='XYZ'
 rig.show_in_front=True
 rig['source_blend']=str(src.relative_to(R));rig['pilot_style_authorized']=True;rig['deformation_visual_passed']=False
 sc['rigged']=True;sc['production_ready']=False
 sc.cycles.samples=8;sc.cycles.use_denoising=True
 sc.render.resolution_x=440;sc.render.resolution_y=600;sc.render.resolution_percentage=100
 cam=sc.camera;cam.location=(0,-7,1.65);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.1
 rigpath=O/(name+'_pilot_rig.blend');bpy.ops.wm.save_as_mainfile(filepath=str(rigpath))
 tests={}
 for pose in ['neutral','wave','hold','lean']:
  reset_pose(rig)
  if pose=='wave':arm_target(rig,'L',(.54,-.11,1.88))
  elif pose=='hold':
   arm_target(rig,'L',(.20,-.42,1.10));arm_target(rig,'R',(-.20,-.42,1.10))
  elif pose=='lean':
   rig.pose.bones['spine'].rotation_euler.x=math.radians(8)
   rig.pose.bones['head'].rotation_euler.x=math.radians(-6)
   arm_target(rig,'L',(.20,-.42,1.10));arm_target(rig,'R',(-.20,-.42,1.10))
  bpy.context.view_layer.update();posed=mesh_sample(skin)
  assert all(math.isfinite(v) for p in posed for v in p)
  displacement=max((a-b).length for a,b in zip(baseline,posed))
  if pose!='neutral':assert displacement>.02,(name,pose,displacement)
  sc.render.filepath=str(O/(name+'_'+pose+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),440,600)
  tests[pose]={'max_sample_displacement':displacement,'png_validated':True,'visual_passed':False}
  print('RIG_TEST_RENDER',name,pose,round(displacement,4),flush=True)
 reset_pose(rig);bpy.ops.wm.save_as_mainfile(filepath=str(rigpath))
 bpy.ops.wm.open_mainfile(filepath=str(rigpath));assert bpy.data.objects[name+'_PilotRig'].type=='ARMATURE'
 report={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'rig_sha256':hashlib.sha256(rigpath.read_bytes()).hexdigest(),'rest_skin_world_error':rest_error,'attachment_world_error':attachment_error,'bones':len(ar.bones) if False else len(bpy.data.objects[name+'_PilotRig'].data.bones),'bound_objects':bound,'poses':tests,'seconds':time.time()-t,'production_ready':False}
 (O/(name+'_rig_audit.json')).write_text(json.dumps(report,indent=2));reports[name]=report
 print('PILOT_RIG_BUILT',name,flush=True)
(O/'cast_rig_audit.json').write_text(json.dumps(reports,indent=2))
print('ALL_PILOT_RIGS_BUILT_VISUAL_QA_PENDING',flush=True)
