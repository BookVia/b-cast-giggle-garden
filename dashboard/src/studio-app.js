export const STUDIO_APP = String.raw`
let ytWindow=28,ytData=null;
const fmt=n=>n===undefined||n===null?'Unavailable':Number(n).toLocaleString();
async function ytRefresh(){
 try{const s=await api('youtube/status');ytData=s.data;$('#youtube-state').textContent=s.connected?'Connected':s.configured?'Ready to connect':'One-time setup needed';$('#youtube-state').className='badge '+(s.connected?'good':'warn');
 $('#yt-connect').disabled=!s.configured;$('#yt-disconnect').hidden=!s.connected;$('#yt-sync').disabled=!s.connected;$('#yt-setup').open=!s.configured;
 $('#youtube-help').textContent=s.connected?(s.data?'Last refreshed '+new Date(s.data.updated).toLocaleString()+'. Daily reports end two days ago; data availability may lag.':'Connected; click Refresh analytics to load the channel.'):'Connect your channel once to see private watch time and subscriber trends. No example numbers are shown.';
 paintYT();
 }catch(e){$('#youtube-help').textContent=e.message}
}
function paintYT(){
 const d=ytData,rows=d?.reports?.[ytWindow]?.rows||[];let views=0,minutes=0,gained=0,lost=0,weighted=0;
 for(const r of rows){views+=Number(r[1]||0);minutes+=Number(r[2]||0);weighted+=Number(r[3]||0)*Number(r[1]||0);gained+=Number(r[4]||0);lost+=Number(r[5]||0)}
 $('#yt-channel').textContent=d?.channel?.title||'Your channel';
 const available=!!d?.reports?.[ytWindow];$('#yt-metrics').innerHTML=[['Views',available?fmt(views):'Not connected'],['Watch hours',available?(minutes/60).toFixed(1):'Unavailable'],['Net subscribers',available?fmt(gained-lost):'Unavailable'],['Average view duration',available?(views?Math.round(weighted/views):0)+' sec':'Unavailable'],['Channel subscribers',fmt(d?.channel?.statistics?.subscriberCount)],['Uploaded videos',fmt(d?.channel?.statistics?.videoCount)]].map(([label,value])=>'<article class="metric"><span>'+esc(label)+'</span><strong>'+esc(value)+'</strong></article>').join('');
 const chart=$('#yt-chart'),existing=window.echarts?.getInstanceByDom(chart);if(existing)existing.dispose();chart.replaceChildren();
 if(rows.length&&window.echarts){const metric=$('#yt-chart-metric')?.value||'views';const label=metric==='watch'?'Watch hours':metric==='subscribers'?'Net subscribers':'Views';const values=rows.map(r=>metric==='watch'?Number(r[2])/60:metric==='subscribers'?Number(r[4])-Number(r[5]):Number(r[1]));const instance=echarts.init(chart,null,{renderer:'svg'});
 instance.setOption({color:['#8660af'],tooltip:{trigger:'axis'},grid:{left:50,right:28,top:30,bottom:70},xAxis:{type:'category',data:rows.map(r=>r[0]),axisLabel:{color:'#7d889b'},axisLine:{lineStyle:{color:'#dde4ed'}}},yAxis:{type:'value',name:label,splitLine:{lineStyle:{color:'#edf1f6'}}},dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:10}],series:[{name:label,type:'line',smooth:true,showSymbol:false,data:values,lineStyle:{width:3},areaStyle:{opacity:.12}}],aria:{enabled:true}});
 }else chart.textContent=d?.analyticsError||(d?'No daily analytics returned for this period.':'Connect YouTube to see your actual performance. No sample data is displayed.');
 $('#yt-videos').innerHTML=(d?.videos||[]).map(v=>'<tr><td><a href="https://www.youtube.com/watch?v='+esc(v.id)+'" target="_blank" rel="noopener">'+esc(v.title)+'</a></td><td>'+esc(fmt(v.views))+'</td><td>'+esc(v.privacy||'Unavailable')+'</td><td>'+esc(v.madeForKids===undefined?'Unavailable':v.madeForKids?'Yes':'No')+'</td><td>'+esc(new Date(v.publishedAt).toLocaleDateString())+'</td></tr>').join('')||'<tr><td colspan="5">No connected video data available.</td></tr>';
}
$('#yt-chart-metric').onchange=()=>paintYT();
window.addEventListener('resize',()=>{for(const id of ['#yt-chart','#production-chart'])window.echarts?.getInstanceByDom($(id))?.resize()});
$('#yt-export').onclick=()=>{const rows=ytData?.reports?.[ytWindow]?.rows;if(!rows?.length){$('#youtube-help').textContent='No connected analytics rows to export.';return}const csv=['date,views,watch_minutes,average_view_seconds,subscribers_gained,subscribers_lost',...rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(','))].join('\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));const a=document.createElement('a');a.href=url;a.download='giggle-garden-analytics-'+ytWindow+'days.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('#yt-window').onchange=e=>{ytWindow=Number(e.target.value);paintYT()};
$('#yt-connect').onclick=async()=>{try{const r=await api('youtube/connect',{});location.assign(r.url)}catch(e){$('#youtube-help').textContent=e.message}};
$('#yt-sync').onclick=async()=>{const b=$('#yt-sync');b.disabled=true;try{await api('youtube/refresh',{});await ytRefresh()}catch(e){$('#youtube-help').textContent=e.message}finally{b.disabled=false}};
$('#yt-disconnect').onclick=async()=>{try{await api('youtube/disconnect',{});await ytRefresh()}catch(e){$('#youtube-help').textContent=e.message}};
$('#yt-config').onsubmit=async e=>{e.preventDefault();try{await api('youtube/configure',{client_id:$('#yt-client-id').value.trim(),client_secret:$('#yt-client-secret').value.trim()});$('#yt-client-id').value='';$('#yt-client-secret').value='';await ytRefresh()}catch(e){$('#youtube-help').textContent=e.message}};
$('#yt-json').onchange=async e=>{try{const file=e.target.files?.[0];if(!file)return;if(file.size>16000)throw Error('OAuth file is too large');const raw=JSON.parse(await file.text()),c=raw.web;if(!c?.client_id||!c?.client_secret)throw Error('Choose a Google web application OAuth JSON file');$('#yt-client-id').value=c.client_id;$('#yt-client-secret').value=c.client_secret;$('#youtube-help').textContent='Credentials loaded. Save connection settings to continue.'}catch(e){$('#youtube-help').textContent=e.message}finally{e.target.value=''}};
async function studioRefresh(){
 if($('#workspace').hidden)return;
 try{const state=await api('state'),s=state.snapshot||{};
 $('#github-status').textContent=JSON.stringify(s.githubExtension||{status:'Waiting for local agent sync'},null,2);$('#ci-local').disabled=!state.lastSeen||Date.now()/1000-state.lastSeen>120;
 $('#tool-reports').textContent=JSON.stringify(s.toolResearch||{status:'Waiting for the local agent to report experiments'},null,2);
 if(window.echarts){const el=$('#production-chart'),chart=echarts.getInstanceByDom(el)||echarts.init(el,null,{renderer:'svg'});const counts={Blocked:0,Running:0,Completed:0,Draft:0};for(const e of s.episodes||[]){const text=String(e.status).toUpperCase();counts[text.includes('BLOCKED')?'Blocked':text.includes('RUNNING')?'Running':text.includes('COMPLETE')?'Completed':'Draft']++}chart.setOption({tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},grid:{left:90,right:35,top:25,bottom:30},xAxis:{type:'value',minInterval:1,splitLine:{lineStyle:{color:'#edf1f6'}}},yAxis:{type:'category',data:Object.keys(counts)},series:[{type:'bar',barWidth:28,data:Object.values(counts).map((value,i)=>({value,itemStyle:{color:['#e9b257','#8660af','#509c79','#99aac0'][i],borderRadius:5}})),label:{show:true,position:'right'}}],aria:{enabled:true}})}
 $('#generation-status').textContent=JSON.stringify(s.generationExperiment||{},null,2);
 $('#tool-queue').disabled=!state.lastSeen||Date.now()/1000-state.lastSeen>120;
 $('#job-filter').onchange=()=>filterJobs();$('#episode-search').oninput=()=>{const q=$('#episode-search').value.toLowerCase();document.querySelectorAll('#episodes .episode').forEach(el=>el.hidden=!el.textContent.toLowerCase().includes(q))};
 for(const [i,j] of state.jobs.entries()){const tr=$('#jobs').children[i];if(!tr)continue;tr.dataset.status=j.status;if(j.status==='QUEUED'){const b=document.createElement('button');b.textContent='Cancel queued job';b.onclick=async()=>{try{await api('cancel',{id:j.id});await refresh();await studioRefresh()}catch(e){$('#notice').textContent=e.message}};tr.children[2].append(b)}}filterJobs();
 const reviews=await api('reviews');$('#review-history').innerHTML=reviews.items.map(r=>'<article class="review-note"><strong>'+esc(r.asset)+'</strong><p>'+esc(r.note)+'</p><small>'+esc(new Date(r.created).toLocaleString())+'</small></article>').join('')||'<p>No review notes yet.</p>';
 await ytRefresh();
 }catch(e){$('#notice').textContent=e.message}
}
function filterJobs(){const wanted=$('#job-filter').value;document.querySelectorAll('#jobs tr').forEach(r=>r.hidden=wanted!=='ALL'&&r.dataset.status!==wanted)}
$('#ci-local').onclick=async()=>{try{const s=await api('state'),ep=s.snapshot?.episodes?.[0]?.id;if(!ep)throw Error('No episode workspace');await api('jobs',{action:'ci_local',episode:ep});await refresh();await studioRefresh()}catch(e){$('#notice').textContent=e.message}};
$('#tool-queue').onclick=async()=>{try{const s=await api('state');const ep=s.snapshot?.episodes?.[0]?.id;if(!ep)throw Error('No local episode workspace');await api('jobs',{action:'tool_audit',episode:ep});await refresh();await studioRefresh()}catch(e){$('#notice').textContent=e.message}};
$('#review-form').onsubmit=async e=>{e.preventDefault();try{await api('reviews',{asset:$('#review-asset').value,note:$('#review-note').value});$('#review-note').value='';await studioRefresh()}catch(e){$('#notice').textContent=e.message}};
document.addEventListener('click',e=>{if(e.target.closest('#refresh'))setTimeout(studioRefresh,600)});
const studioObserver=new MutationObserver(()=>{if(!$('#workspace').hidden)studioRefresh()});studioObserver.observe($('#workspace'),{attributes:true,attributeFilter:['hidden']});
if(!$('#workspace').hidden)studioRefresh();setInterval(studioRefresh,30000);
`;
