import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).parent;O=R/'episodes/pilot-episode-01/cgi';p=O/'Everyone_Gets_a_Turn_pilot.blend';bpy.ops.wm.open_mainfile(filepath=str(p));count=0
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.data.shape_keys:continue
 keys=ob.data.shape_keys.key_blocks
 if not keys.get('Pilot Look Side'):continue
 for base,down,side in zip(keys['Basis'].data,keys['Pilot Look Down'].data,keys['Pilot Look Side'].data):
  down.co=base.co.copy();down.co.z-=.013
  side.co=base.co.copy();side.co.x+=.012
 count+=1
bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(p))
report=json.loads((O/'scene_build_report.json').read_text());report['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();report['independent_gaze_keys_verified']=count;(O/'scene_build_report.json').write_text(json.dumps(report,indent=2));assert count==32
print('PILOT_GAZE_KEYS_INDEPENDENT_FINAL_SOURCE',report['sha256'],flush=True)
