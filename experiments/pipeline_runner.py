"""Resumable prepare/render worker with atomic state and exclusive job lock."""
import argparse,json,os,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def save(path,data):
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,path)
def run(name,render=False,audition=False):
 ep=(ROOT/'episodes'/name).resolve()
 if ep.parent!=(ROOT/'episodes').resolve() or not ep.is_dir():raise ValueError('Invalid episode')
 lock=ep/'pipeline.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 state={'episode':name,'stages':{},'production_ready':False}
 path=ep/'pipeline_progress.json'
 if path.exists():state=json.loads(path.read_text())
 def record(stage,status,detail=''):
  state['stages'][stage]={'status':status,'detail':detail,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save(path,state)
 try:
  if name=='pilot-episode-01' and (ep/'pilot_quality_policy.json').is_file():
   from pilot_render_backend import validate as pilot_validate, render_final as pilot_render
   record('plan','DONE','First pilot uses the current cast style authorized by the user; exact artwork matching deferred')
   if audition:record('voice','DONE','Existing licensed Kokoro narration retained; release listening review pending')
   issues,_=pilot_validate(ep)
   if issues:record('final_render','BLOCKED','; '.join(issues))
   elif render:
    record('final_render','RUNNING','Real 720p/24fps animation; resumable frames; local Blender and FFmpeg')
    output=pilot_render(ep)
    record('final_render','DONE',str(output)+'; technically verified review video; full visual/listening review still required')
   else:record('final_render','PENDING','Pilot inputs verified; ready for review rendering')
   record('youtube','BLOCKED','Finished video review and verified channel authorization required; no automatic publication')
   print(json.dumps(state,indent=2));return state
  from episode_blueprint import compile_plan
  record('plan','RUNNING')
  story=json.loads((ep/'story.json').read_text(encoding='utf-8-sig'))
  if str(story.get('status','')).startswith('REJECTED'):
   record('plan','BLOCKED','Rejected draft cannot be compiled for production')
   record('script_quality','BLOCKED','Draft rejected by editorial quality checks')
   record('final_render','BLOCKED','Rejected story cannot enter production')
   record('youtube','BLOCKED','Rejected story; no production-ready video')
   print(json.dumps(state,indent=2));return state
  plan=compile_plan(story);save(ep/'production_plan_v1.json',plan);record('plan','DONE','Draft plan; estimated timing')
  if audition:
   record('local_voice_audition','RUNNING')
   from local_voice_backend import pilot
   pilot(ep);record('local_voice_audition','DONE','Local neural audition; not approved final character voices')
  from final_render_backend import validate,render_final
  issues,_=validate(ep)
  if issues:record('final_render','BLOCKED','; '.join(issues))
  elif render:
   record('final_render','RUNNING');output=render_final(ep);record('final_render','DONE',str(output)+'; full-video review still required')
  else:record('final_render','PENDING','Inputs pass; --render required')
  record('youtube','BLOCKED','No verified channel authorization or production-ready reviewed video')
 except Exception as e:
  record('worker','FAILED',str(e));raise
 finally:lock.unlink(missing_ok=True)
 print(json.dumps(state,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--episode',required=True);p.add_argument('--render',action='store_true');p.add_argument('--voice-audition',action='store_true');a=p.parse_args()
 run(a.episode,a.render,a.voice_audition)
