import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
const root=process.cwd(),phase=process.argv[2]||'before';
const require=createRequire(path.join(root,'apps/web/package.json'));
const {chromium}=require('@playwright/test');
const {default:lighthouse}=await import(pathToFileURL(path.join(root,'.test-tmp/mobile-tools/node_modules/lighthouse/core/index.js')));
const project=phase==='before'?path.join(root,'.test-tmp/mobile-release-baseline'):root;
const out=path.join(root,'.test-tmp/mobile-overhaul/lighthouse');await fs.mkdir(out,{recursive:true});
const env={...process.env,NEXT_TELEMETRY_DISABLED:'1',NEXT_PUBLIC_SUPABASE_URL:'https://mock.supabase.co',NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:'mock-public-key-for-build-audit',NEXT_PUBLIC_SUPABASE_ANON_KEY:'mock-public-key-for-build-audit',NEXT_PUBLIC_API_BASE_URL:'http://127.0.0.1:4175/api/v1'};
const server=spawn(process.execPath,[path.join(root,'apps/web/node_modules/next/dist/bin/next'),'start','--port','4176'],{cwd:path.join(project,'apps/web'),env,stdio:['ignore','pipe','pipe'],windowsHide:true});
let chrome;
try{
 await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error('Next server startup timed out: '+text.slice(-1200))),60000);for(const stream of [server.stdout,server.stderr])stream.on('data',chunk=>{text+=chunk;process.stdout.write(chunk);if(text.includes('Ready in')){clearTimeout(timer);resolve();}});server.on('exit',code=>{clearTimeout(timer);reject(Error('Next start exited '+code+': '+text.slice(-1000)));});});
 await fetch('http://127.0.0.1:4176/login');
 // Playwright supplies a compatible browser process on Windows and Linux.
 chrome=await chromium.launch({args:['--remote-debugging-port=9227']});
 await fetch('http://127.0.0.1:9227/json/version');
 const rows=[];
 for(let run=0;run<3;run++){
  const result=await lighthouse('http://127.0.0.1:4176/login',{port:9227,output:'html',logLevel:'error',onlyCategories:['performance','accessibility','best-practices'],formFactor:'mobile',screenEmulation:{mobile:true,width:390,height:844,deviceScaleFactor:1,disabled:false}});
  const report=result.lhr,audits=report.audits;
  const row={phase,run,url:report.finalDisplayedUrl,lighthouse:report.lighthouseVersion,performance:Math.round(report.categories.performance.score*100),accessibility:Math.round(report.categories.accessibility.score*100),lcp:audits['largest-contentful-paint'].numericValue,cls:audits['cumulative-layout-shift'].numericValue,tbt:audits['total-blocking-time'].numericValue,fcp:audits['first-contentful-paint'].numericValue,transferBytes:audits['total-byte-weight']?.numericValue,inp:null,scope:'Production Next.js login, mock public config, Lighthouse default mobile throttling; no authenticated or field-INP claim'};
  rows.push(row);await fs.writeFile(path.join(out,`${phase}-${run}.html`),result.report);await fs.writeFile(path.join(out,`${phase}-${run}.json`),JSON.stringify(report));await fs.writeFile(path.join(out,`${phase}-summary.json`),JSON.stringify(rows,null,2));console.log(JSON.stringify(row));
 }
}finally{await chrome?.close();server.kill();}
