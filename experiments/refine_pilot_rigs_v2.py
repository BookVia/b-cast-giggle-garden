import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'pilot_rigs_v2';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from png_validation import valid_png
def parent_keep(ob,rig):
 mw=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='head';bpy.context.view_layer.update();ob.matrix_world=mw
for name in ['Amina','Tebo','Kiki','Luma']:
 src=R/'pilot_rigs_v1'/(name+'_pilot_rig.blend')
 bpy.ops.wm.open_mainfile(filepath=str(src));sc=bpy.context.scene;rig=bpy.data.objects[name+'_PilotRig']
 skin=next(o for o in sc.objects if o.type=='MESH' and 'continuous' in o.name.lower())
 mat=skin.data.materials[0]
 lids=[]
 for eye in [o for o in list(sc.objects) if 'seated eyeball' in o.name]:
  bb=[eye.matrix_world@Vector(v) for v in eye.bound_box]
  lo=Vector([min(p[i] for p in bb) for i in range(3)]);hi=Vector([max(p[i] for p in bb) for i in range(3)])
  center=(lo+hi)/2;radius=(hi-lo)/2
  verts=[];closed=[];faces=[];nx=33;nr=17
  for row in range(nr):
   t=row/(nr-1)
   for col in range(nx):
    u=-.995+1.99*col/(nx-1);arc=math.sqrt(max(0,1-u*u))
    zs=arc*(1-.035*t);zc=arc*(1-1.97*t)
    def pos(z):return (center.x+radius.x*u,center.y-radius.y*math.sqrt(max(0,1-u*u-z*z))-.023,center.z+radius.z*z)
    verts.append(pos(zs));closed.append(pos(zc))
  for row in range(nr-1):
   for col in range(nx-1):
    i=row*nx+col;faces.append((i,i+1,i+nx+1,i+nx))
  me=bpy.data.meshes.new(name+' fitted blinking eyelid');me.from_pydata(verts,[],faces);me.update()
  ob=bpy.data.objects.new(name+' Blink lid '+('L' if center.x>0 else 'R'),me);sc.collection.objects.link(ob);me.materials.append(mat)
  for p in me.polygons:p.use_smooth=True
  ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='Blink')
  for v,p in zip(key.data,closed):v.co=p
  parent_keep(ob,rig);lids.append(ob)
 # Reduced greeting wave avoids rejected extreme raised-arm sleeve folds.
 for side in ['L','R']:rig.pose.bones['forearm.'+side].constraints['Pilot hand IK'].influence=0
 sc.render.resolution_x=440;sc.render.resolution_y=600;sc.cycles.samples=8
 rig.pose.bones['forearm.L'].constraints['Pilot hand IK'].influence=1
 rig.pose.bones['hand_ik.L'].location=Vector((.66,-.16,1.62))-rig.data.bones['hand_ik.L'].head_local
 sc.render.filepath=str(O/(name+'_gentle_wave.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),440,600)
 rig.pose.bones['forearm.L'].constraints['Pilot hand IK'].influence=0;rig.pose.bones['hand_ik.L'].location=(0,0,0)
 for lid in lids:lid.data.shape_keys.key_blocks['Blink'].value=1
 cam=sc.camera;cam.location=(0,-7,2.1);cam.rotation_euler=(Vector((0,0,2.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.35;sc.render.resolution_x=512;sc.render.resolution_y=512
 sc.render.filepath=str(O/(name+'_blink_closed.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),512,512)
 for lid in lids:lid.data.shape_keys.key_blocks['Blink'].value=0
 sc.render.filepath=str(O/(name+'_blink_open.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),512,512)
 cam.location=(0,-7,1.65);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.1
 path=O/(name+'_pilot_rig.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path))
 report=json.loads((R/'pilot_rigs_v1'/(name+'_rig_audit.json')).read_text());report['rig_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();report['blink_lids']=len(lids);report['pilot_pose_scope']=['neutral','gentle_wave','hold','lean'];report['extreme_wave_accepted']=False;report['v2_visual_review_passed']=False
 (O/(name+'_rig_audit.json')).write_text(json.dumps(report,indent=2));print('PILOT_RIG_V2_DONE',name,flush=True)
print('PILOT_RIG_V2_COMPLETE_VISUAL_REVIEW_PENDING',flush=True)
