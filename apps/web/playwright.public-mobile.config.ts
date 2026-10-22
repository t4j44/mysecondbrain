import {defineConfig} from '@playwright/test';
import mobile from './playwright.mobile.config';
import './e2e/helpers/credentials';
export default defineConfig({
 testDir:'./e2e',testMatch:/unauthenticated\.spec\.ts/,workers:1,retries:0,timeout:90000,
 reporter:[['list'],['json',{outputFile:'../../.test-tmp/mobile-overhaul/public-auth-results.json'}]],
 use:{baseURL:'http://127.0.0.1:4181',screenshot:'only-on-failure',trace:'retain-on-failure'},
 outputDir:'../../.test-tmp/mobile-overhaul/public-auth',
 webServer:{command:'node node_modules/next/dist/bin/next dev --port 4181',url:'http://127.0.0.1:4181/login',timeout:120000,reuseExistingServer:false},
 projects:mobile.projects,
});
