import bpy,bmesh,json,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'amina_reconstruction_v18'
p=O/'Amina_body_reconstruction.blend';bpy.ops.wm.open_mainfile(filepath=str(p))
report={'blend_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'production_ready':False,'visual_reference_passed':False,'deformation_verified':False,'surfaces':{}}
for name in ['Amina V18 connected body with shaped hands','Amina V18 connected cotton tee','Amina V18 shaped overall shorts','Amina connected facial surface with socket and lip loops']:
 ob=bpy.data.objects.get(name);assert ob,name
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
 unseen=set(bm.verts);sizes=[]
 while unseen:
  seed=unseen.pop();stack=[seed];count=0
  while stack:
   v=stack.pop();count+=1
   for e in v.link_edges:
    w=e.other_vert(v)
    if w in unseen:unseen.remove(w);stack.append(w)
  sizes.append(count)
 result={'vertices':len(bm.verts),'faces':len(bm.faces),'connected_components':len(sizes),'component_sizes':sorted(sizes,reverse=True),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
 report['surfaces'][name]=result;bm.free()
report['body_geometry_passed']=all(v['finite'] and v['connected_components']==1 and v['overused_edges']==0 and v['zero_area_faces']==0 and v['boundary_edges']==0 for k,v in report['surfaces'].items() if 'V18' in k)
(O/'technical_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
