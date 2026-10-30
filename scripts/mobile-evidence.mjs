import fs from 'node:fs/promises';
import path from 'node:path';
const source='.test-tmp/mobile-overhaul',out='docs/mobile-overhaul';
const read=async file=>{try{return JSON.parse(await fs.readFile(path.join(source,file),'utf8'));}catch{return null;}};
const median=items=>[...items].sort((a,b)=>a-b)[Math.floor(items.length/2)];
const lighthouse={};
for(const phase of ['before','after']){
 const samples=await read(`lighthouse/${phase}-summary.json`);
 lighthouse[phase]=samples?{scope:samples[0].scope,samples,median:{performance:median(samples.map(r=>r.performance)),lcpMs:median(samples.map(r=>r.lcp)),tbtMs:median(samples.map(r=>r.tbt)),cls:median(samples.map(r=>r.cls)),accessibility:median(samples.map(r=>r.accessibility)),transferBytes:median(samples.map(r=>r.transferBytes))}}:null;
}
const sql=await read('sql-benchmark.json');
const sqlSummary=sql?Object.fromEntries(['before','after'].map(phase=>{const rows=sql.filter(r=>r.phase===phase);return [phase,{queryCount:rows[0].query_count,warmMedianWallMs:median(rows.slice(1).map(r=>r.wall_ms)),warmMedianSqlMs:median(rows.slice(1).map(r=>r.sql_ms)),payloadBytes:rows[0].payload_bytes,responseEqual:rows.every(r=>r.response_equal)}];})):null;
const build={};for(const phase of ['before','after']){const data=await read(`build-${phase}.json`);build[phase]={method:data?.method,routes:data?.routes.filter(r=>/\/(login|assistant|dashboard|capture|people|work)\/page$/.test(r.route)).map(({route,jsBytes,gzipBytes})=>({route,jsBytes,gzipBytes}))};}
const evidence={
 generatedAt:new Date().toISOString(),baseline:'1c4d5372ea719c6e2307c8d11746a1d13c63d506',testedImplementation:'734ed7ac7aaa51059e161257fd4667994e0e1399',performanceMeasurementSource:'9ad17b103e5de1da6134eeaa8081d1f5c191de66; subsequent change only enlarged-text conversation navigation CSS',
 releaseStatus:'Automated gates and protected-preview primary workflow PASS; overall physical-device/provider/human acceptance PARTIAL',
 historicalCI:{source:'dc54f462e9972034bd5be894ac518f3c6dcf7ca8',security:{url:'https://github.com/t4j44/mysecondbrain/actions/runs/39792746110',status:'PASS',backendTests:475,frontendTests:74,mobile:{pass:308,fail:0,skip:16,total:324}},postgres:{url:'https://github.com/t4j44/mysecondbrain/actions/runs/39792755814',status:'PASS',integrationTests:67,upgradeRestoreAndDocker:'PASS'}},
 local:{preComposerFixMatrix:(await read('final-matrix/matrix-results.json'))?.stats,currentZoomAndOffline:(await read('current-zoom/matrix-results.json'))?.stats,draftAndFormFix:(await read('draft-form-fix/matrix-results.json'))?.stats,publicNextAuth:(await read('public-auth-results.json'))?.stats,realStagingViaAllowedLocalOrigin:(await read('staging-phone-results.json'))?.stats,providerJourneyInitial:(await read('provider-journey-results.json'))?.stats,providerJourneyFinal:(await read('provider-journey-final.json'))?.stats,releaseMetadataAndHomeTests:{pass:13,fail:0,scope:'Local SQLite disposable tests; runtime commit must override pinned release label'},frontendComponentTests:{pass:74,files:17,status:'PASS after form and draft fixes'},earlyRealStagingFailures:'Preserved locally: initial local API URL misconfiguration, premature test reload, intermittent redirect to Home, pre-hydration form input and WebKit draft loss; corrected startup paths passed the subsequent 9-case phone run. A clean rerun does not prove absence of intermittent auth issues.'},
 deployment:{preview:{url:'https://second-brain-web-staging-git-co-699a83-thenadish-4808s-projects.vercel.app',immutableBuildUrl:'https://second-brain-web-staging-n31s3p125-thenadish-4808s-projects.vercel.app',id:'dpl_G8jp1Q3K9yMTrVz4JRHR9LccCUZY',source:'734ed7ac7aaa51059e161257fd4667994e0e1399',state:'READY',browser:'PASS: authenticated Chrome, real Home data, 390px Ask retrieval and supporting-source navigation; no horizontal overflow',protection:'Enabled; no bypass link. Use branch alias: only the explicitly approved origins are allowed by staging API CORS.'},api:{service:'srv-dbbjrp4s728c738mhsj0',deploy:'dep-dbd5nsafngtc73fnc71g',state:'live',source:'ac7d4bf3b2aa899a0d5dbd458c9445f03ca98dbb',healthMetadata:'Runtime commit verified after security patch; later redeploy uses identical audited source plus explicitly approved CORS additions'}},
 performance:{lighthouse,sql:{scope:'SQLite harness using identical fictional graph and exact response equality, not hosted PostgreSQL timing',results:sqlSummary},build,messageRenders:{before:await read('renders-before.json'),after:await read('renders-after.json')},publicApi:{before:await read('api-latency-before-backend-deploy.json'),after:await read('api-latency-after-backend-deploy.json')},authenticatedStaging:await read('hosted-api.json')},
 cors:await read('cors-verification.json'),cleanup:await read('cleanup.json'),
 blocked:['Physical iPhone/Android, real software keyboards, VoiceOver/TalkBack and human five-task test','Field INP, proven process-cold authenticated latency and representative populated RLS query plans','Actual Gemini delivery, OCR/upload and all secondary settings/meeting workflows have not passed a complete mobile acceptance matrix'],
 security:{productionChanged:false,hostedSchemaMigration:false,sharedPrivateCache:false,newInfrastructure:false,credentials:'Ignored local E2E file only; never in this report',data:'Only synthetic staging accounts and fictional test records; account A contact was inaccessible to account B and cleaned up'},
};
const latest=await read('release-verification.json');if(latest)evidence.latest=latest;
await fs.mkdir(path.join(out,'evidence'),{recursive:true});
await fs.writeFile(path.join(out,'EVIDENCE.json'),JSON.stringify(evidence,null,2)+'\n');
for(const filename of ['sql-benchmark.json','hosted-api.json','api-latency-after-backend-deploy.json'])await fs.copyFile(path.join(source,filename),path.join(out,'evidence',filename));
for(const phase of ['before','after'])await fs.copyFile(path.join(source,`lighthouse/${phase}-summary.json`),path.join(out,'evidence',`lighthouse-${phase}.json`));
for(const [from,to] of [['before/assistant-390.png','assistant-before-390.png'],['after/assistant-390.png','assistant-after-390.png'],['after/assistant-text-200-webkit-390.png','assistant-enlarged-webkit-390.png']]){try{await fs.copyFile(path.join(source,from),path.join(out,'evidence',to));}catch{}}
for(const route of ['dashboard','assistant','capture']){try{await fs.copyFile(path.join(source,`staging-screenshots/${route}-chromium-390.png`),path.join(out,'evidence',`staging-${route}-390.png`));}catch{}}
console.log('Wrote sanitized evidence; no credentials, tokens or customer records copied.');
async function pages(directory){const found=[];for(const item of await fs.readdir(directory,{withFileTypes:true})){const file=path.join(directory,item.name);if(item.isDirectory())found.push(...await pages(file));else if(item.name==='page.tsx')found.push(file);}return found;}
const rows=[];
for(const file of await pages('apps/web/app')){
 const route='/'+path.relative('apps/web/app',path.dirname(file)).replaceAll('\\','/').split('/').filter(part=>part&&!part.startsWith('(')).join('/');
 let coverage='Source/build only; full route-specific mobile behavior NOT VERIFIED';
 if(['/dashboard','/people','/assistant','/capture','/work'].includes(route))coverage='18-profile synthetic matrix; real staging primary flows at 320/390px; protected Home/Ask/source verified after approved exact-origin CORS change. See EVIDENCE.json.';
 if(['/organizations','/memories','/ideas','/achievements','/kpis','/content'].includes(route))coverage='Actual paginated component with synthetic API, 4 widths x 2 engines; hosted route acceptance NOT VERIFIED';
 if(['/people/new','/people/[personId]','/people/[personId]/edit','/memories/new','/sources/[kind]/[id]'].includes(route))coverage='Synthetic create/edit/source persistence tests; real hosted contact results recorded separately';
 if(route==='/login')coverage='54 real Next.js public-auth tests across 18 profiles; authenticated protected-preview login at 390px; Lighthouse before/after';
 if(route.startsWith('/meetings'))coverage='Existing meeting-component CI at 3 widths; hosted audio/provider/complete route lifecycle NOT VERIFIED';
 rows.push(`| \`${route}\` | ${coverage} |`);
}
await fs.writeFile(path.join(out,'ROUTE_INVENTORY.md'),`# Route coverage inventory\n\nGenerated from all ${rows.length} current page.tsx files. Shared-shell improvements apply to dashboard routes, but shared layout/build success does not establish each route's complete functional acceptance. No untested route is marked PASS.\n\n| Route | Actual evidence boundary |\n| --- | --- |\n${rows.sort().join('\n')}\n`);
