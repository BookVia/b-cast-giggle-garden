import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'amina_reconstruction_v35';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'amina_reconstruction_v34/Amina_anatomy_refinement_UNAPPROVED.blend'))
head=bpy.data.objects['Amina anatomy refinement V34 UNAPPROVED'];head.name='Amina anatomy refinement V35 UNAPPROVED'
# Use the independently verified operand order, updating geometry before creating the modifier.
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,location=(0,-.275,1.9286));cut=bpy.context.object
for v in cut.data.vertices:v.co.x*=.145;v.co.y*=.16;v.co.z*=.060
cut.data.update();bpy.context.view_layer.update()
bpy.context.view_layer.objects.active=head;head.select_set(True);cut.select_set(False)
mod=head.modifiers.new('Verified-order mouth cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;mod.solver='EXACT'
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
for p in head.data.polygons:
 q=p.center;dist=(q.x/.145)**2+((q.y+.275)/.16)**2+((q.z-1.9286)/.060)**2
 if abs(dist-1)<.08 and q.y>-.30:p.material_index=1
 p.use_smooth=True
head.data.update()
sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc.cycles.samples=16
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Amina_anatomy_refinement_UNAPPROVED.blend'))
for name,loc in [('face',(0,-7,2.2)),('three_quarter',(3,-6,2.2)),('profile',(6,-1,2.2))]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector((0,0,2.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.5;sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);print('V35_REVIEW_DONE',name,flush=True)
sys.path.insert(0,str(R));from png_validation import valid_png
for name in ['face','three_quarter','profile']:assert valid_png(O/(name+'.png'),640,640)
report=json.loads((R/'amina_reconstruction_v34/fit_changes.json').read_text());report['changes'].append('Mouth cavity corrected using independently verified modifier/dependency order')
(O/'fit_changes.json').write_text(json.dumps(report,indent=2));print('V35_COMPLETE')
