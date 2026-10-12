import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'cast_pilot_v47';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from png_validation import valid_png
reports={}
for name in ['Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'cast_pilot_v46'/(name+'_pilot_character.blend')))
 m=bpy.data.materials.new(name+' pilot groom matched to Amina material style');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value={'Tebo':(.025,.009,.003),'Kiki':(.014,.006,.003),'Luma':(.18,.064,.018)}[name]+(1,);p.inputs['Roughness'].default_value=.48
 if p.inputs.get('Specular IOR Level'):p.inputs['Specular IOR Level'].default_value=.22
 for ob in bpy.context.scene.objects:
  if ob.type=='CURVES':ob.data.materials.clear();ob.data.materials.append(m)
 sc=bpy.context.scene;sc.cycles.samples=16;sc['pilot_style_authorized']=True;sc['production_ready']=False;sc['rigged']=False
 path=O/(name+'_pilot_character.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path))
 for view,loc,target,scale,size in [('front',(0,-7,1.65),(0,0,1.4),3.05,(600,820)),('face',(0,-7,2.1),(0,0,2.1),1.3,(640,640)),('three_quarter',(3,-6,2.1),(0,0,2.1),1.3,(640,640)),('profile',(6,-1,2.1),(0,0,2.1),1.3,(640,640))]:
  cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=size;sc.render.filepath=str(O/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),*size);print('V47_REVIEW_PASS',name,view,flush=True)
 bpy.ops.wm.open_mainfile(filepath=str(path));report=json.loads((R/'cast_pilot_v46'/(name+'_audit.json')).read_text());report['blend_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();report['changes'].append('Restored dark/brown original groom palette after physical shader caused excessive lightening')
 (O/(name+'_audit.json')).write_text(json.dumps(report,indent=2));reports[name]=report
(O/'cast_audit.json').write_text(json.dumps(reports,indent=2));print('PILOT_CAST_V47_COMPLETE',flush=True)
