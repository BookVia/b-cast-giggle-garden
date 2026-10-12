import json,wave,hashlib,math
from pathlib import Path
import numpy as np
R=Path(__file__).parent;E=R/'episodes/pilot-episode-01';O=E/'audio';O.mkdir(exist_ok=True)
tim=json.loads((E/'timing.json').read_text());sr=48000;n=round(tim['duration']*sr)
voice=np.zeros(n,dtype=np.float32);sources=[]
for s in tim['scenes']:
 path=E/'voice'/('%03d.wav'%s['index'])
 with wave.open(str(path),'rb') as w:
  assert w.getnchannels()==1 and w.getsampwidth()==2
  data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float32)/32768
  source_rate=w.getframerate()
 expected=round(s['duration']*sr)
 up=np.interp(np.arange(expected)*source_rate/sr,np.arange(len(data)),data).astype(np.float32)
 start=round(s['start']*sr);voice[start:start+expected]=up
 sources.append({'file':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
music=np.zeros((n,2),dtype=np.float32);fx=np.zeros((n,2),dtype=np.float32)
def put(bus,data,start,pan=0):
 i=round(start*sr);a=max(0,i);b=min(n,i+len(data))
 if b<=a:return
 seg=data[a-i:b-i]
 bus[a:b,0]+=seg*math.sqrt((1-pan)/2)
 bus[a:b,1]+=seg*math.sqrt((1+pan)/2)
# Original pentatonic marimba/chime arrangement. No external samples.
scale=[261.626,293.665,329.628,391.995,440.]
melody=[0,2,4,2,1,3,2,0,2,3,4,3,2,1,0,2]
for k,start in enumerate(np.arange(.2,tim['duration']-1,.75)):
 freq=scale[melody[k%len(melody)]]*(2 if k%8==7 else 1)
 t=np.arange(round(sr*.72))/sr
 tone=(np.sin(2*np.pi*freq*t)+.20*np.sin(2*np.pi*freq*2.76*t)+.08*np.sin(2*np.pi*freq*5.4*t))
 env=(1-np.exp(-t*160))*np.exp(-t*5.8)
 put(music,(tone*env*.019).astype(np.float32),float(start),.15*math.sin(k*.7))
for start in np.arange(.2,tim['duration']-2,3.):
 t=np.arange(round(sr*2.4))/sr
 chord=sum(np.sin(2*np.pi*f*t) for f in [130.813,164.814,195.998])/3
 env=(1-np.exp(-t*15))*np.exp(-t*2)
 put(music,(chord*env*.015).astype(np.float32),float(start),0)
rng=np.random.default_rng(20261012)
water_events=[]
for s in tim['scenes']:
 if s['action'].endswith('_water'):
  start=s['start']+6;duration=3
  t=np.arange(round(sr*duration))/sr
  raw=rng.normal(0,1,len(t)).astype(np.float32)
  smooth=np.convolve(raw,np.ones(9)/9,mode='same')
  env=np.minimum(1,t/.18)*np.minimum(1,(duration-t)/.28)
  water=(smooth*.015+np.sin(2*np.pi*(700*t+90*np.sin(t*5)))*.002)*env
  put(fx,water.astype(np.float32),start,.25)
  for k in range(28):
   tt=np.arange(round(sr*.09))/sr
   drop=np.sin(2*np.pi*(1600*tt-4500*tt*tt))*np.exp(-tt*65)*.009
   put(fx,drop.astype(np.float32),start+.12+k*.095,.25)
  water_events.append({'scene':s['index'],'start':start,'duration':duration})
for k,start in enumerate(np.arange(3,tim['duration']-3,19)):
 t=np.arange(round(sr*.8))/sr
 phase=2*np.pi*(1800*t+150*np.sin(t*24))
 env=np.sin(np.pi*t/.8)**2*(.55+.45*np.sin(t*30)**2)
 put(fx,(np.sin(phase)*env*.008).astype(np.float32),float(start),(-.5 if k%2 else .5))
fade=np.ones(n,dtype=np.float32);fade[:sr]=np.linspace(0,1,sr);fade[-2*sr:]=np.linspace(1,0,2*sr)
music*=fade[:,None];fx*=fade[:,None]
narr=np.column_stack([voice,voice])*.88
mix=narr+music+fx;peak=float(np.max(np.abs(mix)))
assert peak<.98 and np.isfinite(mix).all(),peak
def save(name,data):
 pcm=(np.clip(data,-1,1)*32767).astype('<i2')
 with wave.open(str(O/name),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
 with wave.open(str(O/name),'rb') as w:assert w.getnframes()==n and w.getframerate()==sr
save('narration.wav',narr);save('original_music.wav',music);save('garden_effects.wav',fx);save('pilot_mix.wav',mix)
report={'duration_seconds':n/sr,'sample_rate':sr,'samples':n,'peak':peak,'clipping_samples':int(np.sum(np.abs(mix)>=1)),'narration_sources':sources,'music_rights':'Original procedural arrangement created for this project; no third-party samples','effects_rights':'Original locally synthesized water and birds','water_events':water_events,'human_listening_review_passed':False,'publication_approved':False}
(O/'audio_audit.json').write_text(json.dumps(report,indent=2))
print('PILOT_AUDIO_ASSEMBLED',round(n/sr,3),'seconds','peak',round(peak,4),'NO_CLIPPING')
