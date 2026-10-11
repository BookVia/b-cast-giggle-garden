"""Reconstruction-input experiment; original reference remains unchanged."""
import os,sys,json,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'tool_experiments'/'triposr_clean_head';O.mkdir(exist_ok=True)
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
sys.path.insert(0,str(R/'character_reconstruction'/'TripoSR'))
import torch,numpy as np,cv2
from PIL import Image,ImageDraw
torch.set_num_threads(2)
REF=R/'approved_reference_assets'/'Giggle Garden Adventure.png'
im=Image.open(REF).convert('RGB');box=(120,182,515,539);crop=im.crop(box)
outline=[(83,9),(133,5),(180,19),(199,45),(207,61),(211,48),(222,63),(239,105),(265,116),(284,103),(314,98),(342,107),(364,129),(378,153),(385,181),(378,209),(362,235),(335,254),(315,261),(299,289),(281,314),(253,336),(219,345),(188,341),(165,325),(134,291),(114,270),(90,263),(75,247),(52,238),(45,221),(49,202),(68,190),(59,177),(38,166),(18,148),(8,120),(12,93),(25,72),(38,47),(55,27)]
mask=Image.new('L',crop.size,0);ImageDraw.Draw(mask).polygon(outline,fill=255)
binary=np.array(mask);gc=np.where(binary>0,cv2.GC_PR_FGD,cv2.GC_BGD).astype('uint8')
gc[cv2.erode(binary,np.ones((15,15),np.uint8))>0]=cv2.GC_FGD
gc[binary==0]=cv2.GC_BGD
cv2.grabCut(np.array(crop),gc,None,np.zeros((1,65)),np.zeros((1,65)),5,cv2.GC_INIT_WITH_MASK)
alpha=Image.fromarray(np.where((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD),255,0).astype('uint8'))
rgba=crop.convert('RGBA');rgba.putalpha(alpha)
rgba=rgba.rotate(26,resample=Image.Resampling.BICUBIC,expand=True)
rgba=rgba.crop(rgba.getbbox());side=max(rgba.size);canvas=Image.new('RGBA',(side,side),(128,128,128,0))
canvas.alpha_composite(rgba,((side-rgba.width)//2,(side-rgba.height)//2));canvas.save(O/'reference_head_isolated.png')
gray=Image.new('RGB',canvas.size,(128,128,128));gray.paste(canvas,mask=canvas.getchannel('A'));gray.save(O/'reference_head_input.png')
report={'tool':'TripoSR','input_reference_sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'device':'cpu','mc_resolution':256,'chunk_size':1024,'production_ready':False,'visual_reference_passed':False,'input_limit':'Single posed head; back and hidden geometry unverified','experiment':'Tighter traced mask, GrabCut edge refinement, eye-line alignment, higher extraction resolution'}
(O/'experiment.json').write_text(json.dumps(report,indent=2));started=time.time()
try:
 from tsr.system import TSR
 model=TSR.from_pretrained(str(R/'character_reconstruction'/'weights'),config_name='config.yaml',weight_name='model.ckpt')
 model.renderer.set_chunk_size(1024);model.to('cpu');print('MODEL_LOADED',flush=True)
 with torch.inference_mode():codes=model([gray],device='cpu')
 print('HEAD_INFERENCE_DONE',flush=True)
 mesh=model.extract_mesh(codes,True,resolution=256)[0];mesh.export(O/'head_UNAPPROVED.glb')
 report.update(completed=True,seconds=round(time.time()-started,2),vertices=len(mesh.vertices),faces=len(mesh.faces),watertight=bool(mesh.is_watertight),finite_coordinates=bool(np.isfinite(mesh.vertices).all()),mesh_sha256=hashlib.sha256((O/'head_UNAPPROVED.glb').read_bytes()).hexdigest())
except Exception as e:
 report.update(completed=False,error=type(e).__name__+': '+str(e),seconds=round(time.time()-started,2))
(O/'experiment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not report['completed']:sys.exit(1)
