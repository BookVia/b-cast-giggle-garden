import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const base='https://b-cast.bookvia.org';
const secret=fs.readFileSync('C:/Users/jason/Documents/B-Cast-login.txt','utf8').match(/Studio password: (.+)/)[1].trim();
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(base);await page.locator('#password').fill(secret);await page.locator('#login button').click();await page.locator('#workspace').waitFor({state:'visible'});
 const response=await page.request.get(base+'/api/state');assert.equal(response.status(),200);const state=await response.json();
 assert.equal(state.snapshot.productionReady,false);assert.equal(state.snapshot.approvedCharacters,0);
 for(const n of ['Amina','Tebo','Kiki','Luma']){
  const a=state.snapshot.assetRevisions[n];assert.equal(a.pilotStyleAuthorized,true);assert.equal(a.rigged,true);assert.match(a.revision,/rig V3/);
  for(const view of ['','_face','_three_quarter','_profile']){
   const r=await page.request.get(base+'/preview/'+n+view);assert.equal(r.status(),200);assert.match(r.headers()['content-type'],/image/);assert.ok((await r.body()).length>1000);
  }
 }
 assert.ok(state.snapshot.episodes.find(e=>e.id==='pilot-episode-01').status.includes('PILOT'));
 await page.waitForFunction(()=>document.querySelectorAll('.candidate-views a').length===12);
 assert.equal(await page.locator('#cast .badge').filter({hasText:'Pilot rig checked'}).count(),4);
 await page.locator('#cast').scrollIntoViewIfNeeded();await page.waitForFunction(()=>[...document.querySelectorAll('#cast img')].every(i=>i.complete&&i.naturalWidth>0));await page.screenshot({path:'pilot-cast-live-desktop.png'});
 await page.setViewportSize({width:390,height:844});await page.locator('#cast').scrollIntoViewIfNeeded();await page.screenshot({path:'pilot-cast-live-mobile.png'});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 await page.locator('#refresh').click();await page.waitForFunction(()=>document.querySelectorAll('.candidate-views a').length===12);assert.deepEqual(errors,[]);
 const other=await browser.newContext();assert.equal((await other.request.get(base+'/preview/Tebo_face')).status(),401);await other.close();
 fs.writeFileSync('pilot-cast-live-verification.json',JSON.stringify({passed:true,cast:4,protectedViews:16,pilotBadges:4,productionReady:false,pageErrors:errors},null,2));
 console.log('PILOT_CAST_LIVE_VERIFIED: four rigged pilot characters, 16 protected views, mobile layout, honest readiness');
}finally{await browser.close()}
