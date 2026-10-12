import json,subprocess,hashlib,wave
from pathlib import Path
cfg=json.loads(Path('pilot-source-manifest.json').read_text());folder=Path('chunks');out=Path('output');out.mkdir(exist_ok=True);src=Path('render_input')
reports=[];expected=1;concat=[]
for k in range(cfg['render_configuration']['shards']):
 p=folder/('pilot-chunk-%02d.json'%k);r=json.loads(p.read_text());video=folder/('pilot-chunk-%02d.mp4'%k)
 assert r['scene_sha256']==cfg['scene_sha256'] and r['first_frame']==expected and r['shard']==k and r['real_bpy_animation_frames'] and r['all_source_pngs_crc_validated'] and r['chunk_full_decode_passed']
 assert hashlib.sha256(video.read_bytes()).hexdigest()==r['video_sha256'] and r['frames']==r['last_frame']-r['first_frame']+1
 assert [x['frame'] for x in r['source_frames']]==list(range(r['first_frame'],r['last_frame']+1))
 reports.append(r);expected=r['last_frame']+1;concat.append("file '"+str(video.resolve())+"'")
assert expected==3202 and sum(r['frames'] for r in reports)==3201
(out/'concat.txt').write_text('\n'.join(concat)+'\n')
narr=src/'pilot_mix.wav'
with wave.open(str(narr),'rb') as w:assert w.getnchannels()==2 and w.getframerate()==48000 and w.getnframes()==6402000
measurement=subprocess.run(['ffmpeg','-hide_banner','-i',str(narr),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],text=True,capture_output=True,check=True)
text=measurement.stderr;stats=json.loads(text[text.rfind('{'):text.rfind('}')+1])
filt='loudnorm=I=-16:TP=-1.5:LRA=11:measured_I='+stats['input_i']+':measured_TP='+stats['input_tp']+':measured_LRA='+stats['input_lra']+':measured_thresh='+stats['input_thresh']+':offset='+stats['target_offset']+':linear=true:print_format=json'
video=out/'Giggle_Garden_E01_Review.mp4'
subprocess.run(['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(out/'concat.txt'),'-i',str(narr),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-af',filt,'-shortest','-movflags','+faststart','-metadata','title=Giggle Garden - Everyone Gets a Turn',str(video)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],text=True));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert int(v['nb_frames'])==3201 and v['width']==1280 and v['height']==720 and v['avg_frame_rate']=='24/1' and v['pix_fmt']=='yuv420p'
assert a['codec_name']=='aac' and a['channels']==2 and int(a['sample_rate'])==48000
assert abs(float(v['duration'])-133.375)<.05 and abs(float(v['duration'])-float(a['duration']))<.1
decoded=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],text=True,capture_output=True,check=True);assert not decoded.stderr.strip()
assert video.stat().st_size<1024**3
report={'scene_sha256':cfg['scene_sha256'],'output_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'output_bytes':video.stat().st_size,'all_3201_real_frames_verified':True,'all_shards_hash_verified':True,'full_decode_passed':True,'fps':24,'duration':133.375,'resolution':[1280,720],'mixed_audio_sha256':hashlib.sha256(narr.read_bytes()).hexdigest(),'loudness_measurement':stats,'probe':probe,'production_ready':False,'full_video_visual_review_passed':False,'human_listening_review_passed':False,'publication_approved':False,'original_artwork_likeness_passed':False,'pilot_style_authorized':True}
(out/'pilot-final-video-audit.json').write_text(json.dumps(report,indent=2));print('PILOT_FULL_VIDEO_TECHNICALLY_VERIFIED_REVIEW_REQUIRED',flush=True)
