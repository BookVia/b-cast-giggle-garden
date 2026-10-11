"""Outbound-only B Cast local agent. Never accepts arbitrary commands."""
import argparse,base64,datetime,io,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BASE=Path(__file__).resolve().parent
def read(p,default=None):
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except (OSError,ValueError):return default
def api(path,data,config):
 raw=json.dumps(data).encode()
 req=urllib.request.Request(config['url']+'/api/agent/'+path,data=raw,headers={'Content-Type':'application/json','User-Agent':'GiggleGarden-Bcast-Agent/1.0','Authorization':'Bearer '+config['token']})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def snapshot():
 episodes=[]
 for ep in sorted((ROOT/'episodes').iterdir()):
  if not ep.is_dir() or not (ep/'story.json').exists():continue
  story=read(ep/'story.json',{})
  progress=read(ep/'pipeline_progress.json',{})
  timing=read(ep/'local_voice_audition'/'timing.json',{})
  duration=timing.get('duration') or timing.get('total_duration_seconds') or timing.get('total_duration')
  if not duration:
   import wave
   duration=0
   for f in (ep/'local_voice_audition').glob('*.wav'):
    try:
     with wave.open(str(f)) as w:duration+=w.getnframes()/w.getframerate()
    except (OSError,wave.Error):pass
  episodes.append({'id':ep.name,'title':story.get('title',ep.name),'status':story.get('status','DRAFT')+' / PRODUCTION BLOCKED','audioSeconds':round(duration,2) if duration else None,'stages':progress.get('stages',{})})
 registry=read(ROOT/'CURRENT_PRODUCTION_ASSETS.json',{})
 return {'githubExtension':{'repository':read(ROOT/'tool_experiments/github_repository.json',{}),'costPolicy':read(ROOT/'bcast-github-project/github-cost-policy.json',{}),'localTrial':read(ROOT/'bcast-github-project/output/ci-result.json',{}),'hostedCheckpoint':read(ROOT/'tool_experiments/github_ci_checkpoint.json',{})},'toolResearch':{**read(ROOT/'tool_experiments'/'VERIFIED_TOOL_FINDINGS.json',{}),'characterFeatureAudit':read(ROOT/'tool_experiments'/'AMINA_FEATURE_AUDIT.json',{})},'featureAudit':read(ROOT/'tool_experiments'/'AMINA_FEATURE_AUDIT.json',{}),'assetRevisions':{n:{'revision':a.get('revision'),'faceAudit':a.get('face_audit','NOT VERIFIED')} for n,a in registry.get('assets',{}).items()},'generationExperiment':read(ROOT/'pipeline_audit'/'qwen17_generation_progress.json',{}),'episodes':episodes,'completedEpisodes':0,'approvedCharacters':0,'productionReady':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':registry.get('note','All character and garden candidates remain unapproved. No approved rigs or finished episodes are available.')}
def previews():
 from PIL import Image
 paths={'reference':ROOT/'approved_reference_assets'/'Giggle Garden Adventure.png'}
 paths.update({n:ROOT/'artwork_refinement_v10'/(n+'_review.png') for n in ['Amina','Tebo','Kiki','Luma','garden']})
 registry=read(ROOT/'CURRENT_PRODUCTION_ASSETS.json',{})
 for name,asset in registry.get('assets',{}).items():
  if name not in ['Amina','Tebo','Kiki','Luma','garden']:continue
  candidate=(ROOT/asset.get('preview','')).resolve()
  if candidate.is_relative_to(ROOT) and candidate.is_file():paths[name]=candidate
  if name=='Amina' and asset.get('face_preview'):
   face=(ROOT/asset['face_preview']).resolve()
   if face.is_relative_to(ROOT) and face.is_file():paths['Amina_face']=face
 out={}
 for name,path in paths.items():
  if not path.exists():continue
  with Image.open(path) as im:
   im=im.convert('RGB');im.thumbnail((1000,750));buf=io.BytesIO();im.save(buf,format='JPEG',quality=78);out[name]=base64.b64encode(buf.getvalue()).decode()
 return out
def command(job):
 ep=job.get('episode','');action=job.get('action')
 if action not in ('preflight','voice_audition','render','tool_audit','ci_local') or not ep or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in ep):raise ValueError('Invalid allowlisted job')
 target=(ROOT/'episodes'/ep).resolve()
 if target.parent!=(ROOT/'episodes').resolve() or not (target/'story.json').exists():raise ValueError('Episode outside project or missing')
 if action=='ci_local':return [r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe','-b','--python',str(ROOT/'bcast-github-project/pipeline/ci_check.py')]
 if action=='tool_audit':return [sys.executable,str(ROOT/'record_tool_verdicts.py')]
 args=[sys.executable,str(ROOT/'pipeline_runner.py'),'--episode',ep]
 if action=='voice_audition':args+=['--voice-audition']
 if action=='render':args+=['--render']
 return args
def main():
 p=argparse.ArgumentParser();p.add_argument('--once',action='store_true');p.add_argument('--no-jobs',action='store_true');a=p.parse_args()
 config=read(BASE/'agent-config.json');assert config and config['url']=='https://b-cast.bookvia.org'
 import msvcrt
 lockfile=(BASE/'agent.lock').open('a+b')
 lockfile.seek(0)
 if lockfile.read(1)==b'':lockfile.write(b'0');lockfile.flush()
 lockfile.seek(0)
 try:msvcrt.locking(lockfile.fileno(),msvcrt.LK_NBLCK,1)
 except OSError:raise SystemExit('Agent already running')
 active=None;proc=None;log=None;lastpreviews=0;lastyoutube=0
 try:
  while True:
   try:
    data={'snapshot':snapshot(),'activeJob':active['id'] if active else None}
    if time.time()-lastpreviews>600:data['previews']=previews()
    if time.time()-lastyoutube>3600:data['youtubeSync']=True
    api('sync',data,config);lastyoutube=time.time() if data.get('youtubeSync') else lastyoutube;lastpreviews=time.time() if 'previews' in data else lastpreviews
    if proc and proc.poll() is not None:
     log.close();content=Path(log.name).read_text(encoding='utf-8',errors='replace')[-16000:]
     progress=read(ROOT/'episodes'/active['episode']/'pipeline_progress.json',{})
     blocked=progress.get('stages',{}).get('final_render',{}).get('status')=='BLOCKED'
     script_blocked=progress.get('stages',{}).get('script_quality',{}).get('status')=='BLOCKED'
     status='FAILED' if proc.returncode else 'BLOCKED' if (script_blocked and active['action'] in ('preflight','voice_audition','render')) or (blocked and active['action'] in ('preflight','render')) else 'DONE'
     api('result',{'id':active['id'],'status':status,'result':content},config)
     proc=None;active=None;log=None
    if not active and not a.no_jobs:
     active=api('claim',{},config).get('job')
     if active:
      try:
       args=command(active);(BASE/'logs').mkdir(exist_ok=True);log=(BASE/'logs'/(active['id']+'.log')).open('w',encoding='utf-8');proc=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
      except Exception as e:
       if log:log.close()
       api('result',{'id':active['id'],'status':'FAILED','result':str(e)},config);active=None;proc=None;log=None
    (BASE/'agent-health.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'activeJob':active['id'] if active else None,'status':'ONLINE'}))
    if a.once:break
   except Exception as e:
    error={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ERROR','error':type(e).__name__+': '+str(e)}
    (BASE/'agent-health.json').write_text(json.dumps(error))
    print(error['utc'],error['error'],flush=True)
    if a.once:raise
   time.sleep(30)
 finally:
  if log:log.close()
  lockfile.close()
if __name__=='__main__':main()
