"""Compare actual source geometry with the anatomy branch; no visual approval inferred."""
import bpy,json,hashlib,array,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'amina_reconstruction_v35'
def fingerprint(o):
 h=hashlib.sha256()
 if o.type=='MESH':
  a=array.array('f',[0])*(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',a);h.update(a.tobytes())
  a=array.array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',a);h.update(a.tobytes())
 elif o.type=='CURVES':
  at=o.data.attributes['position'];a=array.array('f',[0])*(len(at.data)*3);at.data.foreach_get('vector',a);h.update(a.tobytes())
 elif o.type=='CURVE':
  for s in o.data.splines:
   for p in s.points:h.update(array.array('f',p.co).tobytes())
   for p in s.bezier_points:h.update(array.array('f',p.co).tobytes())
 return h.hexdigest()
def inventory(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));out={}
 for o in bpy.context.scene.objects:
  if o.type not in ['MESH','CURVE','CURVES']:continue
  bounds=[o.matrix_world@Vector(v) for v in o.bound_box]
  out[o.name]={'type':o.type,'geometry_sha256':fingerprint(o),'matrix_world':[list(row) for row in o.matrix_world],'bounds':[[min(p[i] for p in bounds),max(p[i] for p in bounds)] for i in range(3)],'materials':[m.name for m in o.data.materials if m],'vertices':len(o.data.vertices) if o.type=='MESH' else None}
 return out
source=inventory(R/'amina_reconstruction_v22/Amina_likeness_candidate_UNAPPROVED.blend')
target=inventory(O/'Amina_anatomy_refinement_UNAPPROVED.blend')
compared={}
for name,item in target.items():
 old=source.get(name)
 compared[name]={'origin':'V22 transferred object' if old else 'new anatomy or refinement geometry','source_geometry_unchanged':item['geometry_sha256']==old['geometry_sha256'] if old else None,'source_transform_unchanged':item['matrix_world']==old['matrix_world'] if old else None,'source_materials_unchanged':item['materials']==old['materials'] if old else None,**item}
source_earrings={n:v for n,v in source.items() if any(s in n.lower() for s in ['earring','ear ring','purple drop'])}
target_earrings={n:v for n,v in target.items() if any(s in n.lower() for s in ['earring','ear ring','purple drop'])}
report={'production_ready':False,'visual_reference_passed':False,'comparison':'V22 complete candidate versus V35 anatomy head branch','objects':compared,'source_earring_objects':source_earrings,'target_earring_objects':target_earrings,'omitted_source_objects':sorted(set(source)-set(target)),'limitations':['Matching geometry hashes prove reuse, not correct fit','Bounding boxes do not prove clearance or surface attachment','V35 is a head branch; body, clothes and hands have not been integrated','Nose, cheeks, jaw and ears come from anisotropically fitted MPFB anatomy, not the old V22 head']}
(O/'feature_transfer_audit.json').write_text(json.dumps(report,indent=2))
summary={'target_objects':len(target),'unchanged_transfers':[n for n,v in compared.items() if v['source_geometry_unchanged'] and v['source_transform_unchanged']],'refitted_transfers':[n for n,v in compared.items() if v['origin']=='V22 transferred object' and not v['source_geometry_unchanged']],'source_earrings':list(source_earrings),'target_earrings':list(target_earrings)}
print(json.dumps(summary,indent=2))
