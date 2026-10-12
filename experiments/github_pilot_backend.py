"""Bounded free public GitHub render controller; no automatic YouTube publication."""
import subprocess,json,os,re,time,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).parent;REPO='BookVia/b-cast-giggle-garden'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def atomic(p,data):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));os.replace(temp,p)
def env():
 e=os.environ.copy();e['GH_TOKEN']=subprocess.check_output(['gh','auth','token','--user','BookVia'],text=True).strip();return e
def gh(args,e):return subprocess.check_output(['gh',*args],text=True,env=e)
def render_final(ep):
 assert ep.resolve()==ROOT/'episodes/pilot-episode-01'
 C=ep/'cgi';e=env();m=read(C/'ci_source_manifest.json');scene=C/'Everyone_Gets_a_Turn_pilot.blend'
 assert hashlib.sha256(scene.read_bytes()).hexdigest()==m['scene_sha256']
 meta=json.loads(gh(['repo','view',REPO,'--json','isPrivate,nameWithOwner'],e));assert meta['isPrivate'] is False and meta['nameWithOwner']==REPO
 assert m['public_standard_runner_only'] and not m['artifact_uploads'] and not m['caches'] and m['render_configuration']['max_parallel']<=8 and m['render_configuration']['max_job_minutes']<=180
 config=read(ROOT/'bcast-github-project/pilot-source-manifest.json');assert config==m
 info_path=C/'github_render_dispatch.json'
 if info_path.exists():
  info=read(info_path);assert info['scene_sha256']==m['scene_sha256'],'Existing render uses another source; preserve and explicitly supersede it'
 else:
  result=gh(['workflow','run','pilot-episode-render.yml','--repo',REPO],e)
  match=re.search(r'/actions/runs/(\d+)',result)
  if match:run_id=match.group(1)
  else:
   runs=json.loads(gh(['run','list','--workflow','pilot-episode-render.yml','--repo',REPO,'--limit','1','--json','databaseId'],e));assert runs;run_id=str(runs[0]['databaseId'])
  info={'run_id':run_id,'url':'https://github.com/'+REPO+'/actions/runs/'+run_id,'scene_sha256':m['scene_sha256'],'asset_tag':m['asset_tag'],'automatic_retries':0}
  atomic(info_path,info)
 print('FULL_PILOT_GITHUB_RENDER_STARTED',info['url'],flush=True)
 shards=m['render_configuration']['shards']
 while True:
  run=json.loads(gh(['run','view',info['run_id'],'--repo',REPO,'--json','status,conclusion,jobs,url'],e))
  complete=[];active=[];failed=[]
  for j in run['jobs']:
   match=re.fullmatch(r'render \((\d+)\)',j['name'])
   if not match:continue
   k=int(match.group(1))
   if j['conclusion']=='success':complete.append(k)
   elif j['status']=='in_progress':active.append(k)
   elif j['status']=='completed' and j['conclusion']!='success':failed.append(k)
  done=sum(3201*(k+1)//shards-3201*k//shards for k in complete)
  progress={'status':'RUNNING' if run['status']!='completed' else 'ASSEMBLED' if run['conclusion']=='success' else 'FAILED','done':done,'total':3201,'shards_done':len(complete),'shards_total':shards,'active_shards':active,'failed_shards':failed,'github_url':info['url'],'github_status':run['status'],'github_conclusion':run['conclusion'],'scene_sha256':m['scene_sha256'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'Only completed, verified chunks count toward rendered frames; partial active frames are not guessed.'}
  atomic(C/'render_progress.json',progress);print('PILOT_RENDER_PROGRESS',done,3201,len(active),'active shards',flush=True)
  if run['status']=='completed':
   if run['conclusion']=='success':break
   if info['automatic_retries']<1:
    subprocess.run(['gh','run','rerun',info['run_id'],'--repo',REPO,'--failed'],check=True,env=e);info['automatic_retries']+=1;atomic(info_path,info);time.sleep(30);continue
   raise RuntimeError('Bounded GitHub render failed after one retry; existing successful chunks and source remain preserved. '+info['url'])
  time.sleep(30)
 out=ep/'final';out.mkdir(exist_ok=True)
 subprocess.run(['gh','release','download',m['asset_tag'],'--repo',REPO,'--pattern','Giggle_Garden_E01_Review.mp4','--pattern','pilot-final-video-audit.json','--dir',str(out),'--clobber'],env=e,check=True)
 video=out/'Giggle_Garden_E01_Review.mp4';audit=read(out/'pilot-final-video-audit.json')
 assert audit['scene_sha256']==m['scene_sha256'] and hashlib.sha256(video.read_bytes()).hexdigest()==audit['output_sha256']
 assert audit['all_3201_real_frames_verified'] and audit['full_decode_passed'] and not audit['production_ready'] and not audit['publication_approved']
 # Verify the downloaded full file locally too, rather than trusting a transfer alone.
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 audit['local_download_sha256_verified']=True;audit['local_full_decode_passed']=True
 audit['video_url']='https://github.com/'+REPO+'/releases/download/'+m['asset_tag']+'/Giggle_Garden_E01_Review.mp4'
 audit['output']=str(video);atomic(out/'video_audit.json',audit)
 atomic(C/'render_progress.json',{**progress,'status':'DONE','done':3201,'video_url':audit['video_url'],'local_full_decode_passed':True})
 return video
