/** Real Chromium + production components/CSS, synthetic adapters/API only.
 * Run from apps/web: node scripts/meeting-ui-smoke.mjs
 * Does not prove microphone, Gemini, hosted auth, or physical-phone behavior.
 */
import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'package.json'));
const viteRequire = createRequire(require.resolve('vite/package.json'));
const { build } = viteRequire('esbuild');
const { chromium, expect } = require('@playwright/test');
const shared = `
export let meeting=JSON.parse(localStorage.getItem('meeting-fixture') || 'null') || {id:'meeting-1',title:'Meeting with Sarah — customer feedback and the next beta test',meeting_date:'2026-10-08T08:00:00Z',duration_minutes:90,metadata:{timezone:'Asia/Dhaka'},transcript_text:'I will send the report. বাংলা and English.',capture:{state:'awaiting_review',audio_deleted_at:'2026-10-08',confirmed_at:null,receipt:{},speaker_mappings:{},transcript_segments:[{segment_id:'c0:0',speaker_local_id:'c0:spk_1',start_offset:0,end_offset:5,text:'I will send the report.'},{segment_id:'c0:1',speaker_local_id:'c0:spk_2',start_offset:2700,end_offset:2710,text:'UAE expansion: দুবাইয়ের বাজার পরীক্ষা করব, যদি অনুমতি পাই।'}],intelligence:{summary:'Discussed customer feedback and the report.',executive_summary:'Customer feedback, report and conditional UAE exploration.',discussion_sections:[{id:'side',title:'UAE expansion',kind:'secondary',summary:'Explore UAE only with approval.',key_points:[{text:'Permission is required.',evidence:[{segment_id:'c0:1',speaker_id:'c0:spk_2',start_seconds:2700,end_seconds:2710,quote:'যদি অনুমতি পাই।'}]}],evidence:[{segment_id:'c0:1',speaker_id:'c0:spk_2',start_seconds:2700,end_seconds:2710,quote:'যদি অনুমতি পাই।'}]}],commitments:[{description:'Send the customer report',evidence_text:'I will send the report.',confidence:.9,from_speaker:'c0:spk_1',to_speaker:'c0:spk_2'}]}}};
export const persist=()=>localStorage.setItem('meeting-fixture',JSON.stringify(meeting)); export const meetingApi={usage:async()=>({used_seconds:11400,limit_seconds:18000,remaining_seconds:6600,percentage_used:63.33,data_mode:'free_redacted',max_bytes:52428800,retention_days:7}),create:async()=>({id:'meeting-1',title:'Meeting'}),authorize:async()=>({max_bytes:52428800}),finalize:async()=>({}),get:async()=>structuredClone(meeting),map:async(_id,speaker,value)=>{meeting.capture.speaker_mappings[speaker]=value;persist();},confirm:async(_id,selected)=>{meeting.capture.state='completed';meeting.capture.confirmed_at='2026-10-08T09:00:00Z';meeting.capture.receipt={selected};persist();},retry:async()=>({})};`;
const modules = {
  '@/lib/meetings/api': shared,
  '@/lib/api/browser-client': `import {meeting,persist} from '@/lib/meetings/api';export const api={get:async(path)=>path.includes('/export/')?'# Meeting minutes\\nStatus: proposed\\nAttendees: Not confirmed':path.endsWith('/notes')?meeting.metadata.meeting_notes:path.includes('people-search')?[{id:'person-1',name:'Sarah Ahmed'}]:{items:[]},put:async(path,body)=>{if(path.endsWith('/notes')){meeting.metadata.meeting_notes={version:body.expected_version+1,markdown:body.markdown};persist();return meeting.metadata.meeting_notes;}return meeting;},post:async()=>({id:'person-2',name:'New person'})};`,
  '@/lib/supabase/client': `export const createClient=()=>({auth:{getSession:async()=>({data:{session:{access_token:'synthetic',user:{id:'owner'}}}})}});`,
  '@/lib/meetings/local-recordings': `export const listLocalRecordings=async()=>[];export const saveLocalRecording=async()=>{};export const deleteLocalRecording=async()=>{};`,
  '@/lib/meetings/recorder': `export class BrowserRecorderAdapter{async start(_pcm,onChunk){onChunk(new Blob(['synthetic'],{type:'audio/webm'}));}pause(){}resume(){}async stop(){return new Blob(['synthetic'],{type:'audio/webm'});}async dispose(){}}`,
  '@/lib/meetings/live': `export class BrowserLiveTranscriptClient{start(_id,_token,onText,onState){onState('Live transcript reconnecting...');onText({sequence:0,start_offset:0,end_offset:2,text:'বাংলা and English'});}send(){}stop(){}}`,
  '@/lib/meetings/upload': `export class BrowserAudioUploadClient{async upload(_blob,_auth,_token,onProgress){onProgress(100);}}`,
  '@/lib/env': `export const env={NEXT_PUBLIC_API_BASE_URL:'http://127.0.0.1/api/v1'};`,
  'next/navigation': `export const useParams=()=>({meetingId:'meeting-1'});export const useRouter=()=>({push(){}});`,
  'next/link': `import React from 'react';export default function Link({href,children,...props}){return React.createElement('a',{href,...props},children);}`,
};
const bundle = await build({entryPoints:[path.join(root,'scripts/meeting-ui-smoke.fixture.tsx')],bundle:true,write:false,platform:'browser',format:'iife',jsx:'automatic',tsconfig:path.join(root,'tsconfig.json'),define:{'process.env.NODE_ENV':'"test"'},plugins:[{name:'synthetic-meeting-adapters',setup(b){b.onResolve({filter:/.*/},args=>args.path in modules?{path:args.path,namespace:'meeting-smoke'}:undefined);b.onLoad({filter:/.*/,namespace:'meeting-smoke'},args=>({contents:modules[args.path],loader:'jsx',resolveDir:root}));}}]});
const loadConfig = require('tailwindcss/loadConfig');
const tailwindConfig = loadConfig(path.join(root,'tailwind.config.ts'));
tailwindConfig.content = [path.join(root,'components/**/*.{ts,tsx}'),path.join(root,'app/**/*.{ts,tsx}')];
const css = await require('postcss')([require('tailwindcss')(tailwindConfig),require('autoprefixer')]).process(await fs.readFile(path.join(root,'app/globals.css'),'utf8'),{from:undefined});
const server = http.createServer((request,response)=>{
  if(request.url==='/bundle.js'){response.setHeader('Content-Type','application/javascript');response.end(bundle.outputFiles[0].contents);}
  else if(request.url==='/style.css'){response.setHeader('Content-Type','text/css');response.end(css.css+'\n:root{--font-inter:Arial,sans-serif;--font-jetbrains-mono:monospace;--font-outfit:Arial,sans-serif}');}
  else {response.setHeader('Content-Type','text/html');response.end('<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/style.css"><div id="root"></div><script src="/bundle.js"></script>');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try {
  browser=await chromium.launch({headless:true});
  const output=path.resolve(root,'../../.test-tmp/meeting-ui');await fs.mkdir(output,{recursive:true});
  for(const width of [320,390,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});const errors=[];page.on('pageerror',error=>errors.push(error.message));
    const url=`http://127.0.0.1:${server.address().port}`;
    await page.goto(url);await expect(page.getByText(/3h 10m/)).toBeVisible();
    await expect(page.getByRole('button',{name:'Record meeting'})).toBeDisabled();
    for(const box of await page.getByRole('checkbox').all())await box.check();
    await page.getByRole('button',{name:'Record meeting'}).click();
    await expect(page.getByText('বাংলা and English')).toBeVisible();await expect(page.getByText('Live transcript reconnecting...')).toBeVisible();
    await page.getByRole('button',{name:'Pause'}).click();await expect(page.getByText('Paused',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Resume'}).click();
    await page.screenshot({fullPage:true,path:path.join(output,`capture-${width}.png`)});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await page.getByRole('button',{name:'End meeting'}).click();await expect(page.getByText(/Recording uploaded privately/)).toBeVisible();
    await page.goto(url+'/?detail=1');await expect(page.getByRole('heading',{name:/Meeting with Sarah/})).toBeVisible();
    await expect(page.getByRole('heading',{name:'Other important discussions'})).toBeVisible();
    await page.getByRole('link',{name:/Source c0:1/}).first().click();
    await expect(page.locator('[id="segment-c0:1"]')).toBeVisible();
    await page.getByLabel('Search transcript').fill('UAE');
    await expect(page.locator('[id="segment-c0:1"]')).toBeVisible();
    await page.getByLabel('Search transcript').fill('');
    await page.getByLabel('Meeting notes').fill('# Reviewed notes\nUAE only with permission.');
    await page.getByRole('button',{name:'Save notes',exact:true}).click();
    await expect(page.getByText('Notes saved.',{exact:true})).toBeVisible();
    await page.reload();
    await expect(page.getByLabel('Meeting notes')).toHaveValue('# Reviewed notes\nUAE only with permission.');
    await page.getByRole('combobox',{name:'Map speaker 1'}).selectOption('me');
    await expect(page.getByRole('combobox',{name:'Map speaker 2'})).toBeEnabled();await page.getByRole('combobox',{name:'Map speaker 2'}).selectOption('person-1');
    await expect(page.getByRole('button',{name:'Save all'})).toBeEnabled();await page.getByText('Review details',{exact:true}).click();
    await page.screenshot({fullPage:true,path:path.join(output,`detail-${width}.png`)});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await page.getByRole('button',{name:'Save all'}).click();await expect(page.getByText('Saved to your people and plans ✓')).toBeVisible();
    expect(errors).toEqual([]);console.log(`PASS: ${width}px capture, pause/resume, reconnect, upload, speaker mapping, confirmation, detailed side topic, evidence jump, transcript search, note persistence, no horizontal overflow or page errors`);await page.close();
  }
  console.log('3 viewport scenarios passed (synthetic API/adapters). Physical microphone and hosted provider behavior remain unverified.');
} finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
