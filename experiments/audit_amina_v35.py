import bpy,bmesh,json,math,hashlib
from pathlib import Path
R=Path(__file__).parent;O=R/'amina_reconstruction_v35';p=O/'Amina_anatomy_refinement_UNAPPROVED.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
items={}
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not ob.name.startswith(('Amina anatomy refinement','V33 scalp','V33 curved','V33 mouth','V35 surface fitted')):continue
 bm=bmesh.new();bm.from_mesh(ob.data)
 items[ob.name]={'vertices':len(bm.verts),'faces':len(bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
 bm.free()
report={'blend_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'meshes':items,'production_ready':False,'visual_reference_passed':False,'rigged':False,'purpose':'Geometry integrity audit, not deformation approval'}
assert all(v['finite'] for v in items.values())
(O/'mesh_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
