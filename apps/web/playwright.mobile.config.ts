import {defineConfig,devices} from '@playwright/test';
const sizes=[[320,568],[360,800],[375,812],[390,844],[412,915],[430,932],[768,1024],[1024,768],[1440,900]];
const output=process.env.MOBILE_AUDIT_OUTPUT||'../../.test-tmp/mobile-overhaul';
export default defineConfig({
 testDir:'./e2e',testMatch:/mobile-layout\.fixture\.spec\.ts/,fullyParallel:true,workers:2,retries:0,timeout:45000,
 reporter:[['list'],['json',{outputFile:`${output}/matrix-results.json`}],['html',{outputFolder:`${output}/playwright-report`,open:'never'}]],
 use:{baseURL:process.env.MOBILE_FIXTURE_URL||'http://127.0.0.1:4175',contextOptions:{reducedMotion:'reduce'},screenshot:'only-on-failure',trace:'retain-on-failure'},
 outputDir:`${output}/matrix`,
 projects:['chromium','webkit'].flatMap(browserName=>sizes.map(([width,height])=>({
  name:`${browserName}-${width}`,use:{...(width<768?devices[browserName==='webkit'?'iPhone 12 Pro':'Pixel 5']:{}),browserName:browserName as 'chromium'|'webkit',viewport:{width,height},deviceScaleFactor:1,isMobile:width<768,hasTouch:width<768},
 }))),
});
