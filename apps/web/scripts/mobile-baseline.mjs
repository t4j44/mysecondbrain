import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
const require=createRequire(import.meta.url);
const {chromium}=require('@playwright/test');
const phase=process.argv[2]||'before';
const out=path.resolve('../../.test-tmp/mobile-overhaul',phase);await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch();
const rows=[];
try{
  for(const width of [320,390,430,768]){
    for(const route of ['dashboard','assistant','people','work','capture']){
      const page=await browser.newPage({viewport:{width,height:width===320?568:844},reducedMotion:'reduce'});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto((process.env.MOBILE_FIXTURE_URL||'http://127.0.0.1:4174')+'/'+route);await page.waitForLoadState('networkidle');
      await page.screenshot({fullPage:true,path:path.join(out,`${route}-${width}.png`)});
      const metrics=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,chatWidth:document.querySelector('textarea')?.getBoundingClientRect().width||null,renderCount:window.__renders?.length,renderMs:window.__renders?.reduce((sum,r)=>sum+r.duration,0)}));
      rows.push({route,width,...metrics,errors});await page.close();
    }
  }
}finally{await browser.close();await fs.writeFile(path.join(out,'layout.json'),JSON.stringify(rows,null,2));}
console.log(JSON.stringify(rows));
