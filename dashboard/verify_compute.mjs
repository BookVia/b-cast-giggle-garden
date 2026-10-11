import {chromium} from '@playwright/test';
import fs from 'node:fs';import assert from 'node:assert/strict';
const base='https://b-cast.bookvia.org';
const executablePath=['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe'].find(p=>fs.existsSync(p));
const password=fs.readFileSync(process.env.USERPROFILE+'/Documents/B-Cast-login.txt','utf8').match(/Studio password: (.+)/)[1];
const browser=await chromium.launch({executablePath,headless:true});
try{
const c=await browser.newContext();assert.equal((await c.request.get(base+'/api/compute')).status(),401);
const p=await c.newPage();const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto(base);await p.fill('#password',password);await p.click('#login button');await p.waitForSelector('#workspace:not([hidden])');
const response=await c.request.get(base+'/api/compute');assert.equal(response.status(),200);const policy=await response.json();
assert.equal(policy.rendering,'Local Blender CPU');assert.equal(policy.productionReady,false);assert.match(policy.aiInference,/Disabled/);
assert.match(await p.locator('#metrics').innerText(),/Job coordination \+ tracking/);
await p.setViewportSize({width:390,height:844});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
fs.writeFileSync('compute-verification.json',JSON.stringify({utc:new Date().toISOString(),unauthorizedRejected:true,authenticatedEndpoint:true,dashboardMetrics:true,mobileOverflow:false,browserErrors:errors,policy},null,2));
console.log('COMPUTE_VERIFICATION_PASS');
}finally{await browser.close()}
