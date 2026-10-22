import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn,execFileSync} from 'node:child_process';
import {auditBundles} from './mobile-bundle-audit.mjs';
const root=process.cwd(),phase=process.argv[2]||'after';
const out=path.join(root,'.test-tmp/mobile-overhaul');await fs.mkdir(out,{recursive:true});
let project=root;
if(phase==='before'){
 project=path.join(root,'.test-tmp/mobile-release-baseline');await fs.mkdir(project,{recursive:true});
 const archive=path.join(out,'release-baseline.tar');
 const git='git';
 await fs.writeFile(archive,execFileSync(git,['archive','--format=tar','1c4d537'],{cwd:root,maxBuffer:32*1024*1024}));
 execFileSync('tar',['-xf',archive,'-C',project]);
 for(const relative of ['node_modules','apps/web/node_modules']){try{await fs.symlink(path.join(root,relative),path.join(project,relative),process.platform==='win32'?'junction':'dir');}catch(error){if(error.code!=='EEXIST')throw error;}}
}
const logFile=path.join(out,`build-${phase}.log`);const chunks=[];
const env={...process.env,NEXT_TELEMETRY_DISABLED:'1',NEXT_PUBLIC_SUPABASE_URL:'https://mock.supabase.co',NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:'mock-public-key-for-build-audit',NEXT_PUBLIC_SUPABASE_ANON_KEY:'mock-public-key-for-build-audit',NEXT_PUBLIC_API_BASE_URL:'http://127.0.0.1:4175/api/v1'};
const child=spawn(process.execPath,[path.join(root,'apps/web/node_modules/next/dist/bin/next'),'build'],{cwd:path.join(project,'apps/web'),env,windowsHide:true,stdio:['ignore','pipe','pipe']});
for(const stream of [child.stdout,child.stderr])stream.on('data',chunk=>{chunks.push(chunk);process.stdout.write(chunk);});
const code=await new Promise(resolve=>child.on('exit',resolve));await fs.writeFile(logFile,Buffer.concat(chunks));if(code){process.exitCode=code;}else{
 await auditBundles(root,project,phase);
}
