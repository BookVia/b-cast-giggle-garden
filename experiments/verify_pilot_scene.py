import bpy,json,math,time,sys,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;E=R/'episodes/pilot-episode-01';O=E/'cgi';Q=O/'qa';Q.mkdir(exist_ok=True)
sys.path.insert(0,str(R));from png_validation import valid_png
path=O/'Everyone_Gets_a_Turn_pilot.blend';bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
tim=json.loads((E/'timing.json').read_text());fps=tim['fps']
report={'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'engine':sc.render.engine,'technical_passed':False,'visual_passed':False,'frames':[],'cast_motion':{},'visual_review_notes':[]}
rigs=[o for o in sc.objects if o.type=='ARMATURE']
assert len(rigs)==4 and sc.frame_end==3201
assert all(o.animation_data and o.animation_data.action for o in rigs)
bpy.context.view_layer.update()
for rig in rigs:
 sc.frame_set(1);p0=(rig.matrix_world@rig.pose.bones['hand.L'].head).copy()
 sc.frame_set(121);p1=(rig.matrix_world@rig.pose.bones['hand.L'].head).copy()
 assert (p0-p1).length>.01,(rig.name,p0,p1)
 report['cast_motion'][rig.name]={'hand_displacement':(p0-p1).length,'real_armature_keyframes':True}
sc.render.resolution_x=640;sc.render.resolution_y=360;sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
for s in tim['scenes']:
 local=7.5 if s['index'] in [3,4,5,6] else 5 if s['index']==0 else 2 if s['index']==4 else 9 if s['index']==8 else 6
 frame=round((s['start']+local)*fps)+1;sc.frame_set(frame)
 cam=next(o for o in sc.objects if o.type=='CAMERA' and o.name=='Pilot shot '+str(s['index']+1));sc.camera=cam
 bpy.context.view_layer.update()
 for rig in rigs:
  assert all(math.isfinite(v) for pb in rig.pose.bones for row in pb.matrix for v in row)
 dest=Q/('shot_%02d.png'%s['index']);sc.render.filepath=str(dest);start=time.time();bpy.ops.render.render(write_still=True)
 assert valid_png(dest,640,360)
 report['frames'].append({'shot':s['index'],'frame':frame,'path':str(dest.relative_to(R)),'seconds':round(time.time()-start,3)})
 (Q/'scene_qa.json').write_text(json.dumps(report,indent=2));print('PILOT_SHOT_QA_RENDER',s['index'],round(time.time()-start,3),flush=True)
# Dedicated transfer check, with both actors' hands in the shot.
s=tim['scenes'][4];frame=round((s['start']+1.625)*fps)+1;sc.frame_set(frame);sc.camera=bpy.data.objects['Pilot shot 5'];sc.render.filepath=str(Q/'handoff.png');bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),640,360)
report['technical_passed']=True;(Q/'scene_qa.json').write_text(json.dumps(report,indent=2))
print('PILOT_SCENE_TECHNICAL_QA_DONE_VISUAL_PENDING',flush=True)
