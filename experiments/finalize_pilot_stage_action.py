import bpy,json,shutil,hashlib,math
from pathlib import Path
R=Path(__file__).parent;O=R/'episodes/pilot-episode-01/cgi';p=O/'Everyone_Gets_a_Turn_pilot.blend'
shutil.copy2(p,O/'Everyone_Gets_a_Turn_before_water_and_gaze.blend')
if (O/'qa').exists():shutil.move(str(O/'qa'),str(O/'qa_before_soil_water_fix'))
bpy.ops.wm.open_mainfile(filepath=str(p));sc=bpy.context.scene;tim=json.loads((O.parent/'timing.json').read_text());order=['Tebo','Kiki','Luma','Amina'];positions={n:-2.1+1.4*k for k,n in enumerate(order)}
for ob in sc.objects:
 if 'tender seedling stem' in ob.name or 'curved seedling leaf' in ob.name:ob.location.x+=.28
# Small gaze changes on the existing iris/pupil/reflection geometry retain eye shape.
eyes=[]
for ob in sc.objects:
 name=ob.get('pilot_character')
 if name not in order or ob.type!='MESH' or not any(s in ob.name.lower() for s in ['iris','pupil','eye reflection','secondary reflection']):continue
 if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
 down=ob.shape_key_add(name='Pilot Look Down');side=ob.shape_key_add(name='Pilot Look Side');side.slider_min=-1;side.slider_max=1
 for v in down.data:v.co.z-=.013
 for v in side.data:v.co.x+=.012
 down.value=side.value=0;eyes.append((name,down,side))
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
for f in list(range(1,3202,6))+[3201]:
 t=(f-1)/24;s=next(s for s in reversed(tim['scenes']) if t>=s['start']-1e-6);local=t-s['start'];i=s['index']
 canx=-2.1 if i<3 else positions[order[min(3,i-3)]]
 if 4<=i<=6:
  u=smooth((local-.25)/2.75);canx=positions[order[i-4]]*(1-u)+positions[order[i-3]]*u
 gaze=.85*smooth((local-4.5)/.8)*(1-smooth((local-10)/1)) if 3<=i<=6 else .55 if i==7 else 0
 for name,down,side in eyes:
  down.value=gaze;down.keyframe_insert('value',frame=f)
  side.value=max(-.45,min(.45,(canx-positions[name])*.16)) if 1<=i<=6 else 0;side.keyframe_insert('value',frame=f)
sc.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p))
report=json.loads((O/'scene_build_report.json').read_text());report['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();report['water_placement']='Seedlings offset .28 scene units so stream lands on soil beside each plant';report['eye_gaze']='Small existing iris/pupil/glint gaze shape keys, staggered blinks preserved';report['visual_qa_passed']=False;(O/'scene_build_report.json').write_text(json.dumps(report,indent=2))
# Reproducible seedling placement in the scene builder.
q=R/'build_pilot_episode_scene.py';s=q.read_text(encoding='utf-8-sig').replace("x=positions[name].x\n tube(name+' tender","x=positions[name].x+.28\n tube(name+' tender");q.write_text(s,encoding='utf-8')
print('PILOT_SOIL_WATER_PLACEMENT_AND_GAZE_SAVED',len(eyes),flush=True)
