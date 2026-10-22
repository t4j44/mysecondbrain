import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
const {chromium}=createRequire(import.meta.url)('@playwright/test');
const phase=process.argv[2]||'after';
const browser=await chromium.launch();
const rows=[];
try{
 for(let run=0;run<3;run++){
  const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
  await page.goto((process.env.MOBILE_FIXTURE_URL||'http://127.0.0.1:4175')+'/assistant?history=1');
  await page.waitForLoadState('networkidle');
  await page.evaluate(()=>{window.__renders=[];window.__messageRenders=0;});
  await page.locator('textarea').pressSequentially('A synthetic follow-up question',{delay:20});
  const result=await page.evaluate(()=>({commits:window.__renders.length,renderMs:window.__renders.reduce((sum,row)=>sum+row.duration,0),messageRenderCalls:window.__messageRenders}));
  rows.push({phase,run,historyMessages:60,scope:'Development React Profiler, actual components, fictional history, 29 typed characters; not production CPU or INP.',...result});
  await page.close();
 }
}finally{await browser.close();}
await fs.writeFile(path.resolve('../../.test-tmp/mobile-overhaul',`renders-${phase}.json`),JSON.stringify(rows,null,2));
console.log(JSON.stringify(rows));
