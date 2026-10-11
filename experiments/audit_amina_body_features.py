import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'amina_reconstruction_v25'
bpy.ops.wm.open_mainfile(filepath=str(R/'amina_reconstruction_v22/Amina_likeness_candidate_UNAPPROVED.blend'))
items={}
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or not any(s in ob.name.lower() for s in ['body','shirt','tee','overall','bib','shoe','sneaker','flower','button','lace','nail','finger']):continue
 bm=bmesh.new();bm.from_mesh(ob.data);b=[ob.matrix_world@Vector(v) for v in ob.bound_box]
 items[ob.name]={'vertices':len(bm.verts),'faces':len(bm.faces),'quads':sum(len(f.verts)==4 for f in bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'bounds':[[min(v[i] for v in b),max(v[i] for v in b)] for i in range(3)],'armature_modifiers':sum(m.type=='ARMATURE' for m in ob.modifiers),'material_names':[m.name for m in ob.data.materials if m]}
 bm.free()
report={'production_ready':False,'visual_reference_passed':False,'source':'V22 complete candidate, not integrated into anatomy head branch','meshes':items,'armatures':[o.name for o in bpy.context.scene.objects if o.type=='ARMATURE'],'visual_findings':['Pink tee, purple overalls, flower, buttons and pink shoes are present','Clothing silhouette and flat bib still differ from approved cloth construction','Hands and nail placement remain visibly unsuitable; no deformation verification','Standing review pose does not establish the approved kneeling pose or garden interaction']}
(O/'body_feature_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'body_feature_objects':len(items),'armatures':report['armatures'],'nonfinite_meshes':[n for n,v in items.items() if not v['finite']],'overused_meshes':[n for n,v in items.items() if v['overused_edges']]}))
