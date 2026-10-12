import bpy,json,sys,argparse,time,hashlib,subprocess,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from png_validation import valid_png
parser=argparse.ArgumentParser();parser.add_argument('--shard',type=int,required=True);a=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
src=Path('render_input');config=json.loads(Path('pilot-source-manifest.json').read_text());m=json.loads((src/'source_manifest.json').read_text());settings=config['render_configuration'];shards=settings['shards'];assert 0<=a.shard<shards<=64
scene=src/'scene.blend';assert hashlib.sha256(scene.read_bytes()).hexdigest()==config['scene_sha256']==m['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(scene));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True
sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.fps=24;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
first=3201*a.shard//shards+1;last=3201*(a.shard+1)//shards;assert first<=last
out=Path('output');frames=out/'frames';frames.mkdir(parents=True,exist_ok=True);tick=time.time();checks=[]
for frame in range(first,last+1):
 sc.frame_set(frame);sc.camera=max((x for x in sc.timeline_markers if x.camera and x.frame<=frame),key=lambda x:x.frame).camera
 file=frames/('%06d.png'%frame);sc.render.filepath=str(file.resolve());t=time.time();bpy.ops.render.render(write_still=True);assert valid_png(file,1280,720)
 checks.append({'frame':frame,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'seconds':round(time.time()-t,3)})
 print('PILOT_VERIFIED_RENDER_FRAME',a.shard,frame,last,checks[-1]['seconds'],flush=True)
video=out/('pilot-chunk-%02d.mp4'%a.shard)
subprocess.run(['ffmpeg','-hide_banner','-y','-framerate','24','-start_number',str(first),'-i',str(frames/'%06d.png'),'-frames:v',str(last-first+1),'-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(video)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(video)],text=True));v=probe['streams'][0]
assert int(v['nb_frames'])==last-first+1 and v['avg_frame_rate']=='24/1' and v['width']==1280 and v['height']==720 and v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
assert video.stat().st_size<64*1024*1024
report={'shard':a.shard,'shards':shards,'first_frame':first,'last_frame':last,'frames':len(checks),'scene_sha256':config['scene_sha256'],'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'real_bpy_animation_frames':True,'all_source_pngs_crc_validated':True,'chunk_full_decode_passed':True,'engine':'CYCLES','samples':8,'resolution':[1280,720],'fps':24,'elapsed_seconds':round(time.time()-tick,3),'source_frames':checks}
(out/('pilot-chunk-%02d.json'%a.shard)).write_text(json.dumps(report,indent=2))
print('PILOT_SHARD_TECHNICALLY_VERIFIED',a.shard,report['frames'],flush=True)
