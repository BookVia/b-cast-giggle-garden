import { PAGE } from './page.js';
const enc=new TextEncoder(), now=()=>Math.floor(Date.now()/1000);
const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"};
function reply(data,status=200,extra={}){return new Response(JSON.stringify(data),{status,headers:{...headers,'Content-Type':'application/json',...extra}})}
async function hash(s){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(s)))].map(x=>x.toString(16).padStart(2,'0')).join('')}
async function same(a,b){return await hash(a)===await hash(b)}
async function sig(s,env){const k=await crypto.subtle.importKey('raw',enc.encode(env.SESSION_SECRET),{name:'HMAC',hash:'SHA-256'},false,['sign']);return [...new Uint8Array(await crypto.subtle.sign('HMAC',k,enc.encode(s)))].map(x=>x.toString(16).padStart(2,'0')).join('')}
async function admin(req,env){const c=req.headers.get('Cookie')?.match(/(?:^|;\s*)bcast=([0-9]+)\.([a-f0-9]+)/);return !!c && Number(c[1])>now() && Number(c[1])<now()+43201 && await same(c[2],await sig(c[1],env))}
async function body(req){if(Number(req.headers.get('Content-Length')||0)>1400000)throw Error('Payload too large');const t=await req.text();if(t.length>1400000)throw Error('Payload too large');return JSON.parse(t)}
function origin(req){return req.headers.get('Origin')===new URL(req.url).origin}
export default {async fetch(req,env){
 try{
 const p=new URL(req.url).pathname;
 if(p==='/health')return reply({service:'giggle-garden-bcast',ok:true});
 if(p==='/'&&req.method==='GET')return new Response(PAGE,{headers:{...headers,'Content-Type':'text/html; charset=utf-8'}});
 if(p==='/app.js'&&req.method==='GET')return new Response(APP,{headers:{...headers,'Content-Type':'text/javascript'}});
 if(p==='/api/login'&&req.method==='POST'){
 if(!origin(req))return reply({error:'Invalid origin'},403);
 const ip=req.headers.get('CF-Connecting-IP')||'local',row=await env.DB.prepare('SELECT * FROM attempts WHERE ip=?').bind(ip).first();
 if(row&&row.until>now()&&row.count>=8)return reply({error:'Too many attempts; try again in 15 minutes'},429);
 const b=await body(req);
 if(typeof b.password!=='string'||!await same(await hash(b.password),env.ADMIN_HASH)){
 await env.DB.prepare('INSERT INTO attempts(ip,count,until) VALUES(?,1,?) ON CONFLICT(ip) DO UPDATE SET count=CASE WHEN until<? THEN 1 ELSE count+1 END,until=CASE WHEN until<? THEN excluded.until ELSE until END').bind(ip,now()+900,now(),now()).run();return reply({error:'Incorrect password'},401)}
 await env.DB.prepare('DELETE FROM attempts WHERE ip=?').bind(ip).run();
 const expiry=String(now()+43200);return reply({ok:true},200,{'Set-Cookie':'bcast='+expiry+'.'+await sig(expiry,env)+'; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200'});
 }
 if(p.startsWith('/api/agent/')){
 if(!await same(req.headers.get('Authorization')||'','Bearer '+env.AGENT_TOKEN))return reply({error:'Unauthorized'},401);
 if(req.method!=='POST')return reply({error:'Method'},405);
 const b=await body(req);
 if(p==='/api/agent/sync'){
 if(!b.snapshot||typeof b.snapshot!=='object')return reply({error:'Missing snapshot'},400);
 await env.DB.prepare('INSERT INTO snapshot(id,payload,updated) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,updated=excluded.updated').bind(JSON.stringify(b.snapshot),now()).run();
 if(b.activeJob)await env.DB.prepare("UPDATE jobs SET updated=? WHERE id=? AND status='RUNNING'").bind(now(),b.activeJob).run();
 for(const [name,data] of Object.entries(b.previews||{})){if(/^(reference|Amina|Amina_face|Tebo|Kiki|Luma|garden)$/.test(name)&&typeof data==='string'&&data.length<220000&&/^[A-Za-z0-9+/=]+$/.test(data))await env.DB.prepare('INSERT INTO previews(name,data) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET data=excluded.data').bind(name,data).run()}
 return reply({ok:true})}
 if(p==='/api/agent/claim'){
 await env.DB.prepare("UPDATE jobs SET status='INTERRUPTED',result='Agent heartbeat lost; inspect local work before retrying',updated=? WHERE status='RUNNING' AND updated<?").bind(now(),now()-300).run();
 const running=await env.DB.prepare("SELECT id FROM jobs WHERE status='RUNNING' LIMIT 1").first();if(running)return reply({job:null});
 const job=await env.DB.prepare("UPDATE jobs SET status='RUNNING',updated=? WHERE id=(SELECT id FROM jobs WHERE status='QUEUED' ORDER BY created LIMIT 1) AND status='QUEUED' RETURNING *").bind(now()).first();return reply({job})}
 if(p==='/api/agent/result'){
 if(!['DONE','FAILED','BLOCKED'].includes(b.status)||typeof b.result!=='string')return reply({error:'Invalid result'},400);
 await env.DB.prepare("UPDATE jobs SET status=?,result=?,updated=? WHERE id=? AND status='RUNNING'").bind(b.status,b.result.slice(-16000),now(),b.id).run();return reply({ok:true})}
 return reply({error:'Not found'},404)}
 if(p.startsWith('/api/')||p.startsWith('/preview/')){
 if(!await admin(req,env))return reply({error:'Please sign in'},401);
 if(req.method!=='GET'&&!origin(req))return reply({error:'Invalid origin'},403);
 if(p==='/api/logout'&&req.method==='POST')return reply({ok:true},200,{'Set-Cookie':'bcast=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'});
 if(p==='/api/compute'&&req.method==='GET')return reply({"coordination": "Cloudflare Worker and D1", "rendering": "Local Blender CPU", "aiInference": "Disabled: account billing and shared quota unverified", "containers": "Disabled: require paid Workers plan", "automaticPublishing": false, "approvedCharacters": 0, "productionReady": false});
 if(p==='/api/state'&&req.method==='GET'){const s=await env.DB.prepare('SELECT * FROM snapshot WHERE id=1').first();const jobs=await env.DB.prepare('SELECT * FROM jobs ORDER BY created DESC LIMIT 40').all();return reply({snapshot:s?JSON.parse(s.payload):null,lastSeen:s?.updated||0,jobs:jobs.results})}
 if(p.startsWith('/preview/')&&req.method==='GET'){const row=await env.DB.prepare('SELECT data FROM previews WHERE name=?').bind(p.slice(9)).first();if(!row)return reply({error:'Not available'},404);return new Response(Uint8Array.from(atob(row.data),c=>c.charCodeAt(0)),{headers:{...headers,'Content-Type':'image/jpeg'}})}
 if(p==='/api/jobs'&&req.method==='POST'){const b=await body(req);if(!['preflight','voice_audition','render'].includes(b.action)||typeof b.episode!=='string'||!/^[a-zA-Z0-9_-]{1,80}$/.test(b.episode))return reply({error:'Invalid job'},400);
 const s=await env.DB.prepare('SELECT payload,updated FROM snapshot WHERE id=1').first();if(!s||s.updated<now()-120)return reply({error:'Local agent is offline'},409);
 const snap=JSON.parse(s.payload);if(!snap.episodes?.some(e=>e.id===b.episode))return reply({error:'Unknown episode'},400);
 const q=await env.DB.prepare("SELECT id FROM jobs WHERE status IN ('QUEUED','RUNNING') AND episode=? LIMIT 1").bind(b.episode).first();if(q)return reply({error:'This episode already has a job'},409);
 const id=crypto.randomUUID();await env.DB.prepare("INSERT INTO jobs(id,episode,action,status,created,updated) VALUES(?,?,?,'QUEUED',?,?)").bind(id,b.episode,b.action,now(),now()).run();return reply({id},201)}
 if(p==='/api/cancel'&&req.method==='POST'){const b=await body(req);const r=await env.DB.prepare("UPDATE jobs SET status='CANCELLED',updated=? WHERE id=? AND status='QUEUED'").bind(now(),b.id).run();return reply({ok:r.meta.changes>0})}
 }
 return reply({error:'Not found'},404);
 }catch(e){console.error('Request failed',e.message);return reply({error:'Request failed'},500)}
}};
const APP = "const $=s=>document.querySelector(s);\nconst esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c]));\nasync function api(p,b){const r=await fetch('/api/'+p,b?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}:{});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}\n$('#login').onsubmit=async e=>{e.preventDefault();try{await api('login',{password:$('#password').value});$('#password').value='';await refresh()}catch(e){$('#message').textContent=e.message}};\n$('#logout').onclick=async()=>{await api('logout',{});location.reload()};\n$('#refresh').onclick=()=>refresh();\ndocument.addEventListener('click',async e=>{const b=e.target.closest('[data-action]');if(!b)return; b.disabled=true;try{await api('jobs',{episode:b.dataset.episode,action:b.dataset.action});await refresh()}catch(e){$('#notice').textContent=e.message}finally{b.disabled=false}\n});\nasync function refresh(){try{const d=await api('state');$('#sign-in').hidden=true;$('#workspace').hidden=false;const ref=$('[data-src]');if(!ref.getAttribute('src'))ref.src=ref.dataset.src;const s=d.snapshot||{};const online=d.lastSeen&&Date.now()/1000-d.lastSeen<120;$('#connection').textContent=online?'Local studio online':'Local studio offline';$('#connection').className='badge '+(online?'good':'warn');$('#seen').textContent=d.lastSeen?'Last sync '+new Date(d.lastSeen*1000).toLocaleString():'Waiting for first local sync';\n$('#metrics').innerHTML=[['Completed episodes',s.completedEpisodes??0],['Episode target','9 episodes, 2-3 min'],['Approved characters',s.approvedCharacters??0],['Rendering','Local CPU'],['Cloud extension','Job coordination + tracking'],['Cloud AI','Billing verification required']].map(([a,b])=>'<article class=\"metric\"><span>'+esc(a)+'</span><strong>'+esc(b)+'</strong></article>').join('');\n$('#episodes').innerHTML=(s.episodes||[]).map(e=>'<article class=\"episode\"><div><h3>'+esc(e.title||e.id)+'</h3><small>'+esc(e.id)+'</small></div><p class=\"badge warn\">'+esc(e.status)+'</p><p>'+esc(e.audioSeconds?e.audioSeconds+' sec local audition':'No measured audition')+'</p><details><summary>Production checks</summary><pre>'+esc(JSON.stringify(e.stages||{},null,2))+'</pre></details><div class=\"actions\">'+[['preflight','Check pipeline'],['voice_audition','Generate voice audition'],['render','Render reviewed inputs']].map(([a,t])=>'<button data-action=\"'+a+'\" data-episode=\"'+esc(e.id)+'\" '+(!online?'disabled':'')+'>'+t+'</button>').join('')+'</div></article>').join('')||'<p>No local episodes synced yet.</p>';\n$('#cast').innerHTML=['Amina','Tebo','Kiki','Luma','garden'].map(n=>'<article class=\"asset\"><img src=\"/preview/'+n+'\" alt=\"'+n+' current candidate\" loading=\"lazy\"><div><h3>'+esc((n==='garden'?'Garden environment':n)+(s.assetRevisions?.[n]?.revision?' \u00b7 '+s.assetRevisions[n].revision:''))+'</h3><span class=\"badge warn\">Needs visual refinement</span>'+(n==='Amina'?'<p class=\"muted\">Facial surface audit: '+esc(s.assetRevisions?.Amina?.faceAudit||'Not verified')+'</p><a href=\"/preview/Amina_face\" target=\"_blank\" rel=\"noopener\">Inspect facial close-up</a>':'')+'</div></article>').join('');\n$('#jobs').innerHTML=d.jobs.map(j=>'<tr><td>'+esc(j.episode)+'</td><td>'+esc(j.action)+'</td><td>'+esc(j.status)+'</td><td><details><summary>Output</summary><pre>'+esc(j.result||'Waiting for local agent')+'</pre></details></td></tr>').join('')||'<tr><td colspan=\"4\">No jobs yet.</td></tr>';\n$('#notes').textContent=s.note||'Production status is unverified until the local agent reports.';\n}catch(e){if(e.message==='Please sign in'){$('#sign-in').hidden=false;$('#workspace').hidden=true}else{$('#notice').textContent=e.message}}}\nrefresh();setInterval(()=>{if(!$('#workspace').hidden)refresh()},30000);";
