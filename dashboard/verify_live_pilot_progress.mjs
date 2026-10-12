import fs from 'node:fs';import assert from 'node:assert/strict';import {chromium} from 'playwright';
const base='https://b-cast.bookvia.org';
const secret=fs.readFileSync('C:/Users/jason/Documents/B-Cast-login.txt','utf8').match(/Studio password: (.+)/)[1].trim();
const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(base);await page.locator('#password').fill(secret);await page.locator('#login button').click();await page.locator('#workspace').waitFor({state:'visible'});await page.locator('#pilot-production-panel').waitFor({state:'visible'});
 const r=await page.request.get(base+'/api/state');assert.equal(r.status(),200);const state=await r.json();const pilot=state.snapshot.episodes.find(e=>e.id==='pilot-episode-01');assert.ok(pilot);
 assert.equal(state.snapshot.productionReady,false);assert.equal(state.snapshot.pilotProgress.stages.rigging.status,'DONE');assert.equal(state.snapshot.pilotProgress.stages.animation.status,'DONE');assert.equal(state.snapshot.pilotProgress.stages.scene_qa.status,'DONE');
 assert.equal(await page.locator('#pilot-production-panel video').count(),0);assert.equal(await page.locator('#cast .badge').filter({hasText:'Pilot rig checked'}).count(),4);
 await page.screenshot({path:'pilot-production-live-desktop.png'});await page.setViewportSize({width:390,height:844});await page.locator('#pilot-production-panel').scrollIntoViewIfNeeded();await page.screenshot({path:'pilot-production-live-mobile.png'});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 assert.deepEqual(errors,[]);fs.writeFileSync('pilot-production-live-verification.json',JSON.stringify({passed:true,pilotStatus:pilot.status,renderStage:state.snapshot.pilotProgress.stages.final_render.status,progressPanel:true,castRigBadges:4,noFakeVideo:true,productionReady:false,errors},null,2));console.log('LIVE_PILOT_PROGRESS_PANEL_VERIFIED',pilot.status,state.snapshot.pilotProgress.stages.final_render.status);
}finally{await browser.close()}
