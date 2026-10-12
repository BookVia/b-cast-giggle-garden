import bpy,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'pilot_rigs_v3';O.mkdir(exist_ok=True);sys.path.insert(0,str(R));from png_validation import valid_png
for name in ['Amina','Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'pilot_rigs_v2'/(name+'_pilot_rig.blend')));sc=bpy.context.scene;rig=bpy.data.objects[name+'_PilotRig']
 skin=next(o for o in sc.objects if o.type=='MESH' and 'continuous' in o.name.lower())
 p=skin.data.materials[0].node_tree.nodes.get('Principled BSDF');col=tuple(p.inputs['Base Color'].default_value)
 crease=bpy.data.materials.new(name+' gentle eyelid crease');crease.use_nodes=True;shader=crease.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=tuple(c*.4 for c in col[:3])+(1,);shader.inputs['Roughness'].default_value=.6
 seams=[]
 for lid in [o for o in list(sc.objects) if 'Blink lid' in o.name]:
  side='L' if lid.name.endswith('L') else 'R'
  eye=next(o for o in sc.objects if 'seated eyeball' in o.name and (sum((o.matrix_world@Vector(v)).x for v in o.bound_box)>0)==(side=='L'))
  bb=[eye.matrix_world@Vector(v) for v in eye.bound_box];lo=Vector([min(p[i] for p in bb) for i in range(3)]);hi=Vector([max(p[i] for p in bb) for i in range(3)]);center=(lo+hi)/2;rad=(hi-lo)/2
  # Shape keys are in lid-local coordinates after keep-world bone parenting.
  inv=lid.matrix_world.inverted()
  key=lid.data.shape_keys.key_blocks['Blink']
  for i,v in enumerate(key.data):
   colidx=i%33;row=i//33;u=-.995+1.99*colidx/32;zn=math.sqrt(max(0,1-u*u))*(1-1.97*row/16)
   v.co=inv@Vector((center.x+rad.x*u,center.y-rad.y-.024+.035*u*u+.02*zn*zn,center.z+rad.z*zn))
  key.value=0
  curve=bpy.data.curves.new(name+' lid seam '+side,'CURVE');curve.dimensions='3D';curve.bevel_depth=.0022;curve.bevel_resolution=2
  s=curve.splines.new('POLY');s.points.add(24)
  for j,pnt in enumerate(s.points):
   u=-.91+1.82*j/24;pnt.co=(center.x+rad.x*u,center.y-rad.y-.026+.035*u*u,center.z+.012*(1-u*u),1)
  ob=bpy.data.objects.new(name+' blink crease '+side,curve);sc.collection.objects.link(ob);curve.materials.append(crease)
  old=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='head';bpy.context.view_layer.update();ob.matrix_world=old;ob.hide_render=True;ob.hide_viewport=True;seams.append(ob)
 sc.render.resolution_x=440;sc.render.resolution_y=600;sc.cycles.samples=8
 cam=sc.camera;cam.location=(0,-7,1.65);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.1
 rig.pose.bones['forearm.L'].constraints['Pilot hand IK'].influence=1
 rig.pose.bones['hand_ik.L'].location=Vector((.55,-.25,1.72))-rig.data.bones['hand_ik.L'].head_local
 sc.render.filepath=str(O/(name+'_wave.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),440,600)
 rig.pose.bones['forearm.L'].constraints['Pilot hand IK'].influence=0;rig.pose.bones['hand_ik.L'].location=(0,0,0)
 for lid in [o for o in sc.objects if 'Blink lid' in o.name]:lid.data.shape_keys.key_blocks['Blink'].value=1
 for ob in seams:ob.hide_render=False;ob.hide_viewport=False
 cam.location=(0,-7,2.1);cam.rotation_euler=(Vector((0,0,2.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.35;sc.render.resolution_x=512;sc.render.resolution_y=512
 sc.render.filepath=str(O/(name+'_blink.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),512,512)
 for lid in [o for o in sc.objects if 'Blink lid' in o.name]:lid.data.shape_keys.key_blocks['Blink'].value=0
 for ob in seams:ob.hide_render=True;ob.hide_viewport=True
 cam.location=(0,-7,1.65);cam.rotation_euler=(Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.1
 path=O/(name+'_pilot_rig.blend');bpy.ops.wm.save_as_mainfile(filepath=str(path))
 report=json.loads((R/'pilot_rigs_v2'/(name+'_rig_audit.json')).read_text());report['rig_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();report['wave_target']=[.55,-.25,1.72];report['v3_visual_review_passed']=False
 (O/(name+'_rig_audit.json')).write_text(json.dumps(report,indent=2));print('PILOT_RIG_V3_DONE',name,flush=True)
print('PILOT_RIG_V3_COMPLETE',flush=True)
