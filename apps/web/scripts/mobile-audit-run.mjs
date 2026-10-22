import {spawn} from 'node:child_process';
const phase=process.argv[2]||'after';
const port=process.env.MOBILE_FIXTURE_PORT||'4175';
const env={...process.env,MOBILE_FIXTURE_PORT:port,MOBILE_FIXTURE_URL:`http://127.0.0.1:${port}`,...(['before','renders-before'].includes(phase)?{MOBILE_BASELINE_REF:'1c4d537'}:{})};
const server=spawn(process.execPath,['scripts/mobile-ui-server.mjs'],{env,stdio:['ignore','pipe','inherit'],windowsHide:true});
try{
 await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(Error('Fixture server did not start')),120000);server.stdout.on('data',chunk=>{output+=chunk;process.stdout.write(chunk);if(output.includes('Synthetic mobile UI ready')){clearTimeout(timer);resolve();}});server.on('exit',code=>{clearTimeout(timer);reject(Error('Server exited '+code));});});
 const args=phase.startsWith('renders-')?['scripts/mobile-render-profile.mjs',phase.slice(8)]:['matrix','focused'].includes(phase)?['node_modules/@playwright/test/cli.js','test','--config=playwright.mobile.config.ts',...(phase==='focused'?['--grep','person form|200 percent|drawer']:[]),...process.argv.slice(3)]:['scripts/mobile-baseline.mjs',phase];
 const child=spawn(process.execPath,args,{env,stdio:'inherit',windowsHide:true});
 process.exitCode=await new Promise(resolve=>child.on('exit',resolve));
}finally{server.kill();}
