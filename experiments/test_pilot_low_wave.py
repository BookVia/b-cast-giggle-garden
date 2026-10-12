import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'pilot_rigs_v3';sys.path.insert(0,str(R));from png_validation import valid_png
for name in ['Amina','Tebo','Kiki','Luma']:
 bpy.ops.wm.open_mainfile(filepath=str(O/(name+'_pilot_rig.blend')));sc=bpy.context.scene;rig=bpy.data.objects[name+'_PilotRig']
 rig.pose.bones['forearm.L'].constraints['Pilot hand IK'].influence=1;rig.pose.bones['hand_ik.L'].location=Vector((.48,-.30,1.50))-rig.data.bones['hand_ik.L'].head_local
 sc.cycles.samples=8;sc.render.resolution_x=440;sc.render.resolution_y=600;sc.render.filepath=str(O/(name+'_low_wave.png'));bpy.ops.render.render(write_still=True);assert valid_png(Path(sc.render.filepath),440,600)
 print('LOW_WAVE_TEST',name,flush=True)
