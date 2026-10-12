import bpy,bmesh,json,sys,hashlib,array
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'amina_reconstruction_v45';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from png_validation import valid_png
bpy.ops.wm.open_mainfile(filepath=str(R/'amina_reconstruction_v44/Amina_complete_character_candidate_UNAPPROVED.blend'))
cap=bpy.data.objects['Amina V44 smooth surface fitted scalp']
bvh=BVHTree.FromPolygons([cap.matrix_world@v.co for v in cap.data.vertices],[tuple(p.vertices) for p in cap.data.polygons])
m=bpy.data.materials.new('Amina V45 physical scalp hair');m.use_nodes=True;m.node_tree.nodes.clear()
out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');hair=m.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled');hair.parametrization='COLOR';hair.inputs['Color'].default_value=(.022,.009,.004,1);hair.inputs['Roughness'].default_value=.42;m.node_tree.links.new(hair.outputs[0],out.inputs['Surface'])
counts={}
for ob in bpy.context.scene.objects:
 if ob.type!='CURVES' or not ('swept scalp' in ob.name or 'native hairline detail' in ob.name):continue
 att=ob.data.attributes['position'];raw=array.array('f',[0])* (len(att.data)*3);att.data.foreach_get('vector',raw);new=array.array('f');inv=ob.matrix_world.inverted()
 for i in range(0,len(raw),3):
  q=ob.matrix_world@Vector(raw[i:i+3]);hit=bvh.find_nearest(q);assert hit[0] is not None
  p=inv@(hit[0]+hit[1]*(.0017 if 'swept scalp' in ob.name else .0013));new.extend(p)
 att.data.foreach_set('vector',new);ob.data.materials.clear();ob.data.materials.append(m);counts[ob.name]=len(att.data)
# A low-gloss underlying mass supports the real fibres rather than dominating them.
shader=cap.data.materials[0].node_tree.nodes.get('Principled BSDF')
if shader:
 shader.inputs['Roughness'].default_value=.66
 if shader.inputs.get('Specular IOR Level'):shader.inputs['Specular IOR Level'].default_value=.20
bpy.context.view_layer.update();sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False;sc.cycles.samples=16
path=O/'Amina_complete_character_candidate_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
for view,loc,target,scale,size in [('face',(0,-7,2.1),(0,0,2.1),1.5,(640,640)),('three_quarter',(3,-6,2.1),(0,0,2.1),1.5,(640,640)),('profile',(6,-1,2.1),(0,0,2.1),1.5,(640,640)),('front',(0,-7,1.65),(0,0,1.45),3.1,(600,820))]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(O/(view+'.png'),*size);print('V45_RENDER_PASS',view,flush=True)
bpy.ops.wm.open_mainfile(filepath=str(path))
report=json.loads((R/'amina_reconstruction_v44/technical_audit.json').read_text());report.update(blend_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reprojected_native_hair_points=counts,changes=report['changes']+['Reprojected buried scalp fibres to the actual replacement surface and used a physical hair shader'])
(O/'technical_audit.json').write_text(json.dumps(report,indent=2));print('AMINA_V45_COMPLETE',flush=True)
