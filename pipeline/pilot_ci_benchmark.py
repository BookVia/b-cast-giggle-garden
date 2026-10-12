import bpy,sys,json,time,hashlib,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from png_validation import valid_png
a=argparse.ArgumentParser();a.add_argument('--engine',choices=['cycles','eevee'],required=True);args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path('render_input');out=Path('output');out.mkdir(exist_ok=True)
manifest=json.loads((source/'source_manifest.json').read_text());scene=source/'scene.blend';assert hashlib.sha256(scene.read_bytes()).hexdigest()==manifest['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(scene));sc=bpy.context.scene
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
if args.engine=='cycles':
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
else:sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=8
report={'engine':args.engine,'scene_sha256':manifest['scene_sha256'],'blender_version':bpy.app.version_string,'resolution':[1280,720],'real_animation_scene':True,'production_ready':False,'frames':[]}
for frame in [121,1245]:
 sc.frame_set(frame);sc.camera=max((m for m in sc.timeline_markers if m.camera and m.frame<=frame),key=lambda m:m.frame).camera
 dst=out/('ci-'+args.engine+'-frame-%04d.png'%frame);sc.render.filepath=str(dst.resolve());t=time.time();bpy.ops.render.render(write_still=True);assert valid_png(dst,1280,720)
 report['frames'].append({'frame':frame,'seconds':round(time.time()-t,3),'png_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
 print('VERIFIED_PILOT_CI_FRAME',args.engine,frame,report['frames'][-1]['seconds'],flush=True)
(out/('ci-'+args.engine+'-benchmark.json')).write_text(json.dumps(report,indent=2));print('PILOT_CI_BENCHMARK_COMPLETE',args.engine,flush=True)
