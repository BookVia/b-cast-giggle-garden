import {chromium} from '@playwright/test';import fs from 'node:fs';import assert from 'node:assert/strict';
const base='https://b-cast.bookvia.org',executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p=>fs.existsSync(p));
const password=fs.readFileSync(process.env.USERPROFILE+'/Documents/B-Cast-login.txt','utf8').match(/Studio password: (.+)/)[1];
const browser=await chromium.launch({executablePath,headless:true});
try{const c=await browser.newContext({viewport:{width:1440,height:1000}}),p=await c.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
assert.equal((await c.request.get(base+'/api/youtube/status')).status(),401);assert.equal((await c.request.post(base+'/api/youtube/connect',{data:{}})).status(),401);
await p.goto(base);await p.fill('#password',password);await p.click('#login button');await p.waitForSelector('#workspace:not([hidden])');
await p.waitForFunction(()=>document.querySelector('#youtube-state').textContent!=='Checking connection');
const y=await(await c.request.get(base+'/api/youtube/status')).json();assert.equal(y.connected,false);assert.equal(y.data,null);
assert.equal((await c.request.post(base+'/api/youtube/connect',{headers:{Origin:'https://evil.example'},data:{}})).status(),403);
assert.equal((await c.request.get(base+'/oauth/youtube/callback?state=forged&code=fake')).status(),400);
await p.locator('#episode-search').fill('unlikely-episode-name');assert.equal(await p.locator('#episodes .episode:visible').count(),0);await p.locator('#episode-search').fill('');
assert(await p.locator('#review-form').isVisible());assert(await p.locator('#tool-centre').isVisible());assert(await p.locator('#yt-config').isVisible());
await p.screenshot({path:'studio-desktop-verified.png',fullPage:true});
await p.setViewportSize({width:390,height:844});await p.waitForTimeout(200);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:'studio-mobile-verified.png',fullPage:true});
assert.deepEqual(errors,[]);
fs.writeFileSync('studio-verification.json',JSON.stringify({utc:new Date().toISOString(),privateEndpoints:true,crossOriginBlocked:true,forgedOAuthBlocked:true,disconnectedNoFakeData:true,episodeSearch:true,reviewForm:true,toolsPanel:true,mobileOverflow:false,browserErrors:errors},null,2));console.log('STUDIO_LIVE_VERIFICATION_PASS')
}finally{await browser.close()}
