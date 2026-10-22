import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gzipSync} from 'node:zlib';
export async function auditBundles(root,project,phase){
 const next=path.join(project,'apps/web/.next');
 const manifest=JSON.parse(await fs.readFile(path.join(next,'app-build-manifest.json'),'utf8'));
 const rows=[];
 for(const [route,ownFiles] of Object.entries(manifest.pages)){
  const segments=route.split('/').filter(Boolean),parents=['/layout'];
  for(let i=1;i<segments.length;i++)parents.push('/'+segments.slice(0,i).join('/')+'/layout');
  const files=[...new Set([...ownFiles,...parents.flatMap(parent=>manifest.pages[parent]||[])])].filter(file=>file.endsWith('.js'));
  const buffers=await Promise.all(files.map(file=>fs.readFile(path.join(next,file))));
  rows.push({route,jsFiles:files.length,jsBytes:buffers.reduce((sum,b)=>sum+b.length,0),gzipBytes:buffers.reduce((sum,b)=>sum+gzipSync(b).length,0),files});
 }
 await fs.writeFile(path.join(root,'.test-tmp/mobile-overhaul',`build-${phase}.json`),JSON.stringify({phase,project,node:process.version,method:'Unique JS from page plus all ancestor layouts; gzip per file.',routes:rows},null,2));
 console.log('Full-route bundle audit written:',phase,rows.length,'entries');
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=process.cwd();await auditBundles(root,path.join(root,'.test-tmp/mobile-release-baseline'),'before');await auditBundles(root,root,'after');
}
