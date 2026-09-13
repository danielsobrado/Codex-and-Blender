import {chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';

if(process.argv.includes('--optimized')) {
  process.env.FOREST_URL='http://127.0.0.1:4174';
  process.env.FOREST_EVIDENCE='../output/browser';
}

const browser=await chromium.launch({headless:true});
const errors=[],screenshots=new Map();
let report;
try {
  const page=await browser.newPage({viewport:{width:1600,height:900}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('favicon'))errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))errors.push(`${r.status()} ${r.url()}`);});
  async function settle() {
    await page.waitForFunction(()=>window.forestStats?.revision===window.forestWorld?.stats.revision&&window.forestStats.calls<=100,null,{timeout:60000});
    await page.waitForTimeout(1000);
  }
  async function capture(name) {await settle();screenshots.set(name,await page.screenshot());return page.evaluate(()=>window.forestStats);}
  await page.goto(process.env.FOREST_URL||'http://127.0.0.1:4173');
  await page.waitForFunction(()=>window.forestReady,null,{timeout:120000});
  const referenceStats=await capture('threejs_preview.png');
  if(referenceStats.visibleInstances>=referenceStats.sourceInstances*.25)errors.push('Reference view retains too many world instances');
  if(referenceStats.visibleChunks>=referenceStats.totalChunks)errors.push('Frustum culling did not reject any chunks');
  if(referenceStats.capacityDrops)errors.push('Visible instance capacity exceeded');
  await page.locator('#alternate').click();
  const interiorStats=await capture('threejs_interior.png');
  await page.locator('#wind').click();
  if(await page.locator('#wind').textContent()!=='Wind: off')errors.push('Wind control failed');
  await page.locator('#overview').click();
  const overviewStats=await capture('threejs_overview.png');
  if(!overviewStats.lodInstances)errors.push('Overview did not use tree LODs');
  if(overviewStats.triangles>referenceStats.triangles)errors.push('Overview did not reduce geometry workload');
  const offscreenStats=await page.evaluate(async()=>{
    const camera=window.forestCamera.clone();camera.far=200;camera.updateProjectionMatrix();
    camera.position.set(0,60,280);camera.lookAt(0,60,500);camera.updateMatrixWorld();
    return window.forestWorld.update(camera,true);
  });
  if(offscreenStats.visibleInstances!==0)errors.push('Off-screen world was not fully culled');
  await page.locator('#reset').click();await settle();
  const before=await page.evaluate(()=>window.forestWorld.stats.cameraPosition);
  await page.keyboard.down('KeyW');
  try {await page.waitForFunction(start=>Math.hypot(...window.forestWorld.stats.cameraPosition.map((v,i)=>v-start[i]))>.2,before,{timeout:30000});}
  finally {await page.keyboard.up('KeyW');}
  await page.locator('#reset').click();await settle();
  const stats=await page.evaluate(()=>window.forestStats);
  const renderer=await page.evaluate(()=>{
    const gl=document.querySelector('canvas').getContext('webgl2');
    const ext=gl.getExtension('WEBGL_debug_renderer_info');
    return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'Unavailable';
  });
  const loading=await page.evaluate(()=>({readyMs:window.forestLoadMs,resources:performance.getEntriesByType('resource').map(r=>({name:new URL(r.name).pathname,transferBytes:r.transferSize,encodedBytes:r.encodedBodySize,decodedBytes:r.decodedBodySize}))}));
  report={passed:errors.length===0,errors,stats,referenceStats,interiorStats,overviewStats,offscreenStats,renderer,loading};
} finally {await browser.close();}

for(const [name,buffer] of screenshots) {
  for(let attempt=0;;attempt++) {
    try {await writeFile(`${process.env.FOREST_EVIDENCE||'../output/forest'}/${name}`,buffer);break;}
    catch(error) {if(attempt===2)throw error;await new Promise(resolve=>setTimeout(resolve,300));}
  }
}
await writeFile(`${process.env.FOREST_EVIDENCE||'../output/forest'}/browser_validation.json`,JSON.stringify(report,null,2));
if(errors.length)throw Error(errors.join('\n'));
console.log(report);
