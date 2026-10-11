import bpy,bmesh,json,time,hashlib,math,os
from pathlib import Path
from mathutils import Vector
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from png_validation import valid_png
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
candidate=ROOT/'ci-inputs/Amina_review_UNAPPROVED.blend'
started=time.time()
assert bpy.app.version[:3]==(5,2,2),'Exact Blender version required for compatibility trial'
bpy.ops.wm.open_mainfile(filepath=str(candidate))
assert bpy.context.scene.get('production_ready') is not True
body=bpy.data.objects.get('Amina V18 connected body with shaped hands');assert body is not None
bm=bmesh.new();bm.from_mesh(body.data)
audit={'vertices':len(bm.verts),'faces':len(bm.faces),'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),'boundary_edges':sum(e.is_boundary for e in bm.edges),'overused_edges':sum(len(e.link_faces)>2 for e in bm.edges)}
bm.free();assert audit['finite'] and audit['boundary_edges']==0 and audit['overused_edges']==0
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=320;sc.render.resolution_y=320;sc.render.resolution_percentage=100
cam=sc.camera;cam.location=(0,-7,2.16);cam.rotation_euler=(Vector((0,-.03,2.18))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.3
sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/'compatibility_preview_UNAPPROVED.png')
bpy.ops.render.render(write_still=True)
png=Path(sc.render.filepath);assert valid_png(png,320,320),'Strict PNG integrity verification failed'
report={'blender':bpy.app.version_string,'render_device':'CPU','seconds':round(time.time()-started,2),'blend_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'preview_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'technical_audit':audit,'render_width':320,'render_height':320,'samples':8,'png_integrity_verified':True,'production_ready':False,'visual_reference_passed':False,'animation_verified':False,'purpose':'Software pipeline compatibility and bounded preview-render test','hosted_runner':bool(os.environ.get('GITHUB_ACTIONS'))}
(OUT/'ci-result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
