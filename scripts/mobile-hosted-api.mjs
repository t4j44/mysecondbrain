import fs from 'node:fs/promises';
import assert from 'node:assert/strict';

// Use only the dedicated local staging accounts. Never log tokens or bodies.
const env={};
for(const file of ['apps/web/.env.local','apps/web/e2e/.env.local']){
 for(const line of (await fs.readFile(file,'utf8')).split(/\r?\n/)){
  const match=line.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/);if(match)env[match[1]]=match[2].replace(/^["']|["']$/g,'');
 }
}
assert.equal(env.NEXT_PUBLIC_SUPABASE_URL,'https://rpkjmdrralzxhdsgceal.supabase.co');
const base='https://second-brain-api-staging.onrender.com/api/v1';
const evidence={scope:'Real staging HTTP with two disposable synthetic accounts; no customer data',measurements:[],checks:[]};
async function login(email,password){
 const response=await fetch(env.NEXT_PUBLIC_SUPABASE_URL+'/auth/v1/token?grant_type=password',{method:'POST',headers:{apikey:env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,'Content-Type':'application/json'},body:JSON.stringify({email,password}),signal:AbortSignal.timeout(30000)});
 const data=await response.json();assert.equal(response.status,200,'Disposable account authentication failed');assert.ok(data.access_token);return data.access_token;
}
async function request(token,route,method='GET',body){
 const start=performance.now();const response=await fetch(base+route,{method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,cache:'no-store',signal:AbortSignal.timeout(60000)});
 const bytes=await response.arrayBuffer();let data;try{data=JSON.parse(Buffer.from(bytes).toString());}catch{}
 const sample={route:route.replace(/[a-f0-9-]{36}/g,':synthetic-id'),method,status:response.status,ms:Math.round(performance.now()-start),bytes:bytes.byteLength,cacheControl:response.headers.get('cache-control'),serverTiming:response.headers.get('server-timing')};
 evidence.measurements.push(sample);console.log(JSON.stringify(sample));return {status:response.status,data,cache:sample.cacheControl};
}
let tokenA,personId;
try{
 tokenA=await login(env.E2E_EMAIL,env.E2E_PASSWORD);const tokenB=await login(env.E2E_EMAIL_B,env.E2E_PASSWORD_B);
 for(let n=0;n<5;n++){
  const home=await request(tokenA,'/relationships/home');assert.equal(home.status,200);assert.match(home.cache,/private/);assert.match(home.cache,/no-store/);
 }
 evidence.checks.push({name:'Dashboard audit write and private no-store responses',status:'PASS'});
 const created=await request(tokenA,'/people','POST',{name:'Synthetic Mobile Audit বাংলা',company:'Fictional Audit Studio',notes:'Disposable staging test only.'});assert.equal(created.status,201);personId=created.data.id;
 assert.equal((await request(tokenA,'/people/'+personId)).status,200);
 assert.equal((await request(tokenB,'/people/'+personId)).status,404);
 evidence.checks.push({name:'Person persists and second account cannot read it',status:'PASS'});
 evidence.status='PASS';
}catch(error){evidence.status='FAIL';evidence.failure=error.message;process.exitCode=1;console.error(error.message);}
finally{
 if(personId&&tokenA){const cleanup=await request(tokenA,'/people/'+personId,'DELETE');evidence.checks.push({name:'Synthetic person cleanup',status:cleanup.status===204?'PASS':'FAIL'});}
 await fs.writeFile('.test-tmp/mobile-overhaul/hosted-api.json',JSON.stringify(evidence,null,2));
}
