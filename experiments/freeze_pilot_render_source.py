import json,hashlib,zipfile,math
from pathlib import Path
R=Path(__file__).parent;E=R/'episodes/pilot-episode-01';C=E/'cgi';B=R/'bcast-github-project'
scene=C/'Everyone_Gets_a_Turn_pilot.blend';digest=hashlib.sha256(scene.read_bytes()).hexdigest();qa=json.loads((C/'qa/scene_qa.json').read_text());assert qa['technical_passed'] and qa['scene_sha256']==digest and len(qa['frames'])==9
qa['visual_passed']=True;qa['visual_review_scope']='Nine representative shot frames, dedicated hand-off and prior four-character restricted-pose renders inspected. Full motion and finished video review remain pending.';qa['visual_review_notes']=['Current Amina/cast appearance preserved for the pilot','Hair silhouettes retained in watering shots','Shared can held and passed between actual rigged characters','Water stream lands on soil beside four separate seedlings','Earlier bright light and cropped-camera tests superseded']
(C/'qa/scene_qa.json').write_text(json.dumps(qa,indent=2))
report=json.loads((C/'scene_build_report.json').read_text());report['visual_qa_passed']=True;(C/'scene_build_report.json').write_text(json.dumps(report,indent=2))
benchmark=json.loads((C/'github_benchmark/ci-cycles-benchmark.json').read_text());warm=benchmark['frames'][-1]['seconds'];assert warm<40
tag='pilot-e01-input-'+digest[:12]
m={'scene_sha256':digest,'asset_tag':tag,'repository':'BookVia/b-cast-giggle-garden','public_standard_runner_only':True,'benchmark_job_minutes':15,'max_parallel':8,'artifact_uploads':False,'caches':False,'blender_version':'5.2.2','blender_download':'https://download.blender.org/release/Blender5.2/blender-5.2.2-linux-x64.tar.xz','scene_technical_qa_passed':True,'scene_visual_qa_passed':True,'visual_review_scope':qa['visual_review_scope'],'render_configuration':{'engine':'CYCLES','samples':8,'fps':24,'resolution':[1280,720],'total_frames':3201,'shards':16,'max_parallel':8,'max_job_minutes':180},'current_pilot_style_authorized':True,'original_artwork_likeness_passed':False,'production_ready':False,'automatic_youtube_publication':False,'observed_github_warm_frame_seconds':warm}
(C/'ci_source_manifest.json').write_text(json.dumps(m,indent=2));(B/'pilot-source-manifest.json').write_text(json.dumps(m,indent=2))
out=C/'GiggleGarden_E01_Render_Input.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(scene,'scene.blend');z.write(C/'ci_source_manifest.json','source_manifest.json');z.write(E/'audio/pilot_mix.wav','pilot_mix.wav');z.write(E/'timing.json','timing.json')
with zipfile.ZipFile(out) as z:assert z.testzip() is None
p=E/'pipeline_progress.json';d=json.loads(p.read_text());d['stages']['animation']={'status':'DONE','detail':'Nine real animated CGI shots saved; ten representative views inspected; full video review remains pending.'};d['stages']['scene_qa']={'status':'DONE','detail':'Saved-scene hash, four animated rigs, finite poses, nine shot renders and hand-off checked.'};d['stages']['final_render']={'status':'PENDING','detail':'Frozen scene ready for 3201 real 720p frames on free standard public GitHub runners.'};p.write_text(json.dumps(d,indent=2))
policy=json.loads((B/'github-cost-policy.json').read_text());policy['pilot_render']={'frames':3201,'resolution':[1280,720],'engine':'CYCLES CPU','shards':16,'max_parallel':8,'max_job_minutes':180,'public_standard_runner_only':True,'paid_runners':False,'actions_artifacts':False,'cache':False,'automatic_youtube_publication':False};(B/'github-cost-policy.json').write_text(json.dumps(policy,indent=2))
workflow=B/'.github/workflows/pilot-episode-render.yml';s=workflow.read_text().replace('max-parallel: 4','max-parallel: 8');workflow.write_text(s)
print('FINAL_PILOT_SOURCE_FROZEN',tag,digest,'ESTIMATE_HOURS',round(3201*warm/8/3600,2),'FULL_VIDEO_REVIEW_PENDING',flush=True)
