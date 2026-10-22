import {defineConfig} from '@playwright/test';
import mobile from './playwright.mobile.config';
import {AUTH_STATE_PATH} from './e2e/helpers/credentials';
export default defineConfig({
 testDir:'./e2e',workers:1,retries:0,timeout:120000,expect:{timeout:20000},
 reporter:[['list'],['json',{outputFile:'../../.test-tmp/mobile-overhaul/staging-mobile-results.json'}]],
 use:{baseURL:'http://127.0.0.1:3000',screenshot:'only-on-failure',trace:'retain-on-failure'},
 outputDir:'../../.test-tmp/mobile-overhaul/staging-mobile',
 webServer:{command:'node node_modules/next/dist/bin/next dev --port 3000',url:'http://127.0.0.1:3000/login',timeout:120000,reuseExistingServer:false,env:{NEXT_PUBLIC_API_BASE_URL:'https://second-brain-api-staging.onrender.com/api/v1'}},
 projects:[{name:'setup',testMatch:/auth\.setup\.ts/},...mobile.projects!.filter(project=>/-(320|390|430|768)$/.test(project.name!)).map(project=>({...project,testMatch:/mobile-hosted\.spec\.ts/,dependencies:['setup'],use:{...project.use,storageState:AUTH_STATE_PATH}}))],
});
