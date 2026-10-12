"""Resumable real 720p Blender animation renderer, executed inside Blender."""
import bpy,json,time,sys,os,hashlib
from pathlib import Path
R=Path(__file__).parent;E=R/'episodes/pilot-episode-01';C=E/'cgi';F=C/'frames';F.mkdir(exist_ok=True)
sys.path.insert(0,str(R));from png_validation import valid_png
scene=C/'Everyone_Gets_a_Turn_pilot.blend';bpy.ops.wm.open_mainfile(filepath=str(scene));sc=bpy.context.scene
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.cycles.samples=8;sc.cycles.device='CPU';sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=15
manifest={'scene_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'width':1280,'height':720,'fps':24,'engine':sc.render.engine,'samples':8,'total_frames':sc.frame_end}
mfile=C/'frame_source_manifest.json'
if mfile.exists():assert json.loads(mfile.read_text())==manifest,'Source/settings changed; preserve and explicitly supersede old frame directory before rerender'
else:mfile.write_text(json.dumps(manifest,indent=2))
start=time.time();done=0;rendered=0;elapsed_frames=[]
def progress(status,frame=None):
 data={'status':status,'done':done,'total':sc.frame_end,'last_frame':frame,'new_frames_this_run':rendered,'elapsed_seconds':round(time.time()-start,2),'last_render_seconds':elapsed_frames[-1] if elapsed_frames else None,'estimated_remaining_seconds':round((sc.frame_end-done)*sum(elapsed_frames[-12:])/len(elapsed_frames[-12:]),1) if elapsed_frames else None,'scene_sha256':manifest['scene_sha256'],'output_directory':str(F),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 p=C/'render_progress.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));os.replace(temp,p)
try:
 for frame in range(1,sc.frame_end+1):
  dest=F/('%06d.png'%frame)
  if valid_png(dest,1280,720):done+=1;continue
  if dest.exists():dest.rename(dest.with_suffix('.invalid-'+str(int(time.time()))+'.png'))
  sc.frame_set(frame)
  # Explicitly select the shot camera as well as using timeline markers.
  active=max((m for m in sc.timeline_markers if m.camera and m.frame<=frame),key=lambda m:m.frame)
  sc.camera=active.camera;sc.render.filepath=str(dest);tick=time.time();bpy.ops.render.render(write_still=True)
  assert valid_png(dest,1280,720),str(dest)
  elapsed_frames.append(round(time.time()-tick,3));done+=1;rendered+=1;progress('RUNNING',frame)
  print('PILOT_FRAME_VALID',frame,sc.frame_end,elapsed_frames[-1],flush=True)
 progress('DONE',sc.frame_end);print('PILOT_ALL_3201_REAL_FRAMES_VALIDATED',flush=True)
except Exception:
 progress('FAILED');raise
