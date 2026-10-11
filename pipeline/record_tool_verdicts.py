from pathlib import Path
import json
R=Path(__file__).resolve().parent
out={'production_ready':False,'approved_characters':0,'completed_episodes':0,'experiments':{}}
for key,rel,verdict in [
 ('MPFB','tool_experiments/mpfb_cpu/experiment.json','Useful anatomical quad base. Likeness and child proportions not established.'),
 ('TripoSR','tool_experiments/triposr_head/experiment.json','REJECTED for production: visibly distorted head and puff geometry. Watertight mesh does not establish likeness.'),
 ('QuadriFlow','tool_experiments/quadriflow/experiment.json','Manifold quad result; deformation and visual surface preservation unverified.')]:
 p=R/rel;data=json.loads(p.read_text()) if p.exists() else {'completed':False}
 out['experiments'][key]={'measurement':data,'verdict':verdict,'production_ready':False}
out['amina_v19_visual_review']={'passed':False,'findings':['Oversized spherical hair puffs and repeated thick loops','Doll-like eye and face proportions','Insufficient finger separation','Garment construction and material detail need refinement']}
(R/'tool_experiments/VERIFIED_TOOL_FINDINGS.json').write_text(json.dumps(out,indent=2))
print('Findings saved; no asset approved')
