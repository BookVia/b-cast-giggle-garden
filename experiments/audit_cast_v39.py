import bpy,bmesh,math,json,hashlib,sys,array
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'cast_anatomy_v39';sys.path.insert(0,str(R));from png_validation import valid_png
results={}
for name in ['Tebo','Kiki','Luma']:
 path=O/(name+'_anatomy_candidate_UNAPPROVED.blend');bpy.ops.wm.open_mainfile(filepath=str(path))
 sc=bpy.context.scene;report=json.loads((O/(name+'_audit.json')).read_text())
 assert sc.get('character')==name and sc.get('production_ready') is False
 assert not any(o.type=='ARMATURE' for o in sc.objects)
 assert not any(any(t in o.name.lower() for t in ['puff','earring','bow knot','folded bow']) for o in sc.objects)
 required={'Tebo':['Dinosaur body','Dinosaur head'],'Kiki':['Yellow flared dress','Hair clip centre','Clip petal','White daisy petal'],'Luma':['Leaf shirt print','Leaf vein']}[name]
 for prefix in required:assert any(o.name.startswith(prefix) for o in sc.objects),(name,prefix)
 packed=any('Giggle Garden Adventure' in i.name and i.packed_file is not None for i in bpy.data.images)
 assert packed,'Approved reference not embedded'
 for view,size in [('front',(600,820)),('face',(640,640)),('three_quarter',(640,640)),('profile',(640,640))]:assert valid_png(O/(name+'_'+view+'.png'),*size)
 hairpoints=0
 for o in sc.objects:
  if o.type!='CURVES':continue
  a=o.data.attributes['position'];values=array.array('f',[0])* (len(a.data)*3);a.data.foreach_get('vector',values)
  assert all(math.isfinite(v) for v in values);hairpoints+=len(a.data)
 meshchecks={}
 for ob in sc.objects:
  if ob.type!='MESH':continue
  assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
  if any(t in ob.name for t in ['anatomy refinement','connected body','connected tailored hoodie','connected shoulder']):
   bm=bmesh.new();bm.from_mesh(ob.data)
   meshchecks[ob.name]={'vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces)};bm.free()
 report.update(blend_reopen_passed=True,blend_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),identity_component_checks=required,approved_reference_embedded=packed,all_native_hair_points_finite=True,native_hair_points=hairpoints,reopened_mesh_checks=meshchecks)
 (O/(name+'_audit.json')).write_text(json.dumps(report,indent=2));results[name]=report
 print('CAST_REOPEN_QA_PASS',name,json.dumps(meshchecks),flush=True)
(O/'cast_audit.json').write_text(json.dumps(results,indent=2));print('CAST_V39_REOPEN_QA_COMPLETE',flush=True)
