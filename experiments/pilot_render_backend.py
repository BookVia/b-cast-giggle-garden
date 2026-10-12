"""First-pilot exception: accepted model style, real animation, review-only output."""
import json,hashlib,subprocess,shutil,os,datetime,wave
from pathlib import Path
ROOT=Path(__file__).parent
BLENDER=Path(r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(ep):
 issues=[]
 if ep.resolve()!=ROOT/'episodes/pilot-episode-01':return ['Pilot exception is restricted to episode one'],{}
 try:
  policy=read(ep/'pilot_quality_policy.json')
  if not policy.get('pilot_style_authorized') or not policy.get('allow_rigging_and_review_render'):issues.append('Pilot style authorization missing')
  if policy.get('automatic_publication') or policy.get('paid_tools_or_rendering_allowed'):issues.append('Review-only/free-tools policy violated')
  story=read(ep/'story.json')
  if story.get('characters')!=['Amina','Tebo','Kiki','Luma'] or str(story.get('status','')).startswith('REJECTED'):issues.append('Pilot story/cast mismatch')
  timing=read(ep/'timing.json')
  if timing['fps']!=24 or timing['total_frames']!=3201 or not 120<=timing['duration']<=180:issues.append('Invalid pilot duration/frame count')
  voice=read(ep/'voice_manifest.json')
  audio=read(ep/'audio/audio_audit.json')
  for s in timing['scenes']:
   p=ep/'voice'/('%03d.wav'%s['index'])
   if sha(p)!=s['sha256']:issues.append('Voice file hash changed')
  mix=ep/'audio/pilot_mix.wav'
  with wave.open(str(mix),'rb') as w:
   if w.getnchannels()!=2 or w.getframerate()!=48000 or abs(w.getnframes()/w.getframerate()-timing['duration'])>.001:issues.append('Audio timeline mismatch')
  if audio['clipping_samples']!=0:issues.append('Audio clipping')
  cgi=ep/'cgi';scene=cgi/'Everyone_Gets_a_Turn_pilot.blend';build=read(cgi/'scene_build_report.json');qa=read(cgi/'qa/scene_qa.json')
  if sha(scene)!=build['sha256'] or sha(scene)!=qa['scene_sha256']:issues.append('Animated scene changed since review')
  if not qa.get('technical_passed') or not qa.get('visual_passed'):issues.append('Scene technical/visual review incomplete')
  if not build.get('real_character_animation'):issues.append('Real character animation missing')
  for name,digest in build['cast_source_rig_sha256'].items():
   p=ROOT/'pilot_rigs_v3'/(name+'_pilot_rig.blend');r=read(ROOT/'pilot_rigs_v3'/(name+'_rig_audit.json'))
   if sha(p)!=digest or sha(p)!=r['rig_sha256']:issues.append(name+' rig changed')
   if not r.get('pilot_pose_visual_review_passed'):issues.append(name+' pilot pose review incomplete')
  if not BLENDER.is_file() or not shutil.which('ffmpeg') or not shutil.which('ffprobe'):issues.append('Blender/FFmpeg missing')
  return issues,{'scene':str(scene),'timing':timing,'audio':str(mix)}
 except (OSError,KeyError,ValueError,wave.Error) as e:return ['Missing/invalid pilot input: '+str(e)],{}
def render_final(ep):
 issues,data=validate(ep)
 if issues:raise RuntimeError('; '.join(issues))
 cgi=ep/'cgi';out=ep/'final';out.mkdir(exist_ok=True)
 with (cgi/'full_render.log').open('w',encoding='utf-8') as log:
  subprocess.run([str(BLENDER),'-b','--threads','2','--python-exit-code','1','-P',str(ROOT/'pilot_render_frames.py')],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=ROOT)
 from png_validation import valid_png
 frames=cgi/'frames'
 for i in range(1,3202):assert valid_png(frames/('%06d.png'%i),1280,720),i
 ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
 # Measure loudness, then apply a measured second pass to the complete mix.
 measured=subprocess.run([ffmpeg,'-hide_banner','-i',data['audio'],'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 j=measured.stderr;stats=json.loads(j[j.rfind('{'):j.rfind('}')+1]);(out/'loudness_measurement.json').write_text(json.dumps(stats,indent=2))
 filt='loudnorm=I=-16:TP=-1.5:LRA=11:measured_I='+stats['input_i']+':measured_TP='+stats['input_tp']+':measured_LRA='+stats['input_lra']+':measured_thresh='+stats['input_thresh']+':offset='+stats['target_offset']+':linear=true:print_format=json'
 temp=out/'Giggle_Garden_E01_Review.partial.mp4'
 args=[ffmpeg,'-hide_banner','-y','-framerate','24','-start_number','1','-i',str(frames/'%06d.png'),'-i',data['audio'],'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-af',filt,'-shortest','-movflags','+faststart','-metadata','title=Giggle Garden - Everyone Gets a Turn',str(temp)]
 with (out/'assembly.log').open('w',encoding='utf-8') as log:subprocess.run(args,check=True,stdout=log,stderr=subprocess.STDOUT)
 probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(temp)],text=True))
 video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert video['width']==1280 and video['height']==720 and video['avg_frame_rate']=='24/1'
 assert int(video['nb_frames'])==3201 and video['pix_fmt']=='yuv420p' and video['codec_name']=='h264'
 assert audio['codec_name']=='aac' and int(audio['sample_rate'])==48000 and audio['channels']==2
 assert abs(float(video['duration'])-133.375)<.05 and abs(float(audio['duration'])-float(video['duration']))<.1
 decoded=subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(temp),'-f','null','-'],capture_output=True,text=True,check=True)
 assert not decoded.stderr.strip(),decoded.stderr
 output=out/'Giggle_Garden_E01_Review.mp4'
 if output.exists():output.rename(out/('Giggle_Garden_E01_previous_'+sha(output)[:12]+'.mp4'))
 os.replace(temp,output)
 audit={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(output),'sha256':sha(output),'scene_sha256':sha(Path(data['scene'])),'mixed_audio_sha256':sha(Path(data['audio'])),'full_decode_passed':True,'all_3201_source_pngs_validated':True,'duration_seconds':133.375,'resolution':[1280,720],'fps':24,'real_3d_character_animation':True,'pilot_style_authorized':True,'original_artwork_likeness_passed':False,'full_video_visual_review_passed':False,'human_listening_review_passed':False,'publication_approved':False,'production_ready':False,'probe':probe}
 (out/'video_audit.json').write_text(json.dumps(audit,indent=2))
 package={'title':'Everyone Gets a Turn | Giggle Garden','description':'Amina, Tebo, Kiki and Luma learn to take turns while caring for their garden seedlings. A gentle story about sharing, waiting and saying thank you.','made_for_kids':True,'language':'en-GB','visibility':'unlisted','upload_approved':False,'video_sha256':audit['sha256']}
 (out/'youtube_package.json').write_text(json.dumps(package,indent=2))
 return output
