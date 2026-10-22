import fs from 'node:fs/promises';
import path from 'node:path';
const output=path.resolve('.test-tmp/mobile-overhaul/api-latency.json');await fs.mkdir(path.dirname(output),{recursive:true});
const rows=[];
for(const route of ['/health','/health/ready'])for(let sample=0;sample<5;sample++){
 const started=performance.now();
 try{
  const response=await fetch('https://second-brain-api-staging.onrender.com'+route,{cache:'no-store',signal:AbortSignal.timeout(25000)});
  const bytes=await response.arrayBuffer();let releaseSha;
  if(route==='/health'){try{releaseSha=JSON.parse(Buffer.from(bytes).toString()).release_sha;}catch{}}
  const row={route,sample,timestamp:new Date().toISOString(),label:sample===0?'first_observed_not_proven_cold':'subsequent_warm_candidate',status:response.status,ms:Math.round(performance.now()-started),bytes:bytes.byteLength,cacheControl:response.headers.get('cache-control'),releaseSha};rows.push(row);console.log(JSON.stringify(row));
 }catch(error){const row={route,sample,timestamp:new Date().toISOString(),error:error.name,causeCode:error.cause?.code,ms:Math.round(performance.now()-started)};rows.push(row);console.log(JSON.stringify(row));}
 await fs.writeFile(output,JSON.stringify(rows,null,2));
}
