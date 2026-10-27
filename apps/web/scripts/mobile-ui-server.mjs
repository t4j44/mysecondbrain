/** Production components and styles with explicitly synthetic auth/API adapters.
 * No customer records, auth tokens or provider calls. Not hosted E2E evidence.
 */
import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'package.json'));
const repo = path.resolve(root, '../..');
const baseline = process.env.MOBILE_BASELINE_REF;
function source(file) {
  if (baseline) {
    try { return execFileSync('git', ['show', `${baseline}:${path.relative(repo,file).replaceAll('\\','/')}`], {cwd:repo, encoding:'utf8',stdio:['ignore','pipe','ignore']}); } catch { /* Fixture-only files are untracked. */ }
  }
  return null;
}
const { build } = createRequire(require.resolve('vite/package.json'))('esbuild');
const modules = {
  'next/navigation': `export const usePathname=()=>location.pathname;export const useRouter=()=>({push:(url)=>location.assign(url),refresh:()=>location.reload(),back:()=>history.back()});export const useSearchParams=()=>new URLSearchParams(location.search);export const useParams=()=>({personId:location.pathname.split('/')[2],kind:location.pathname.split('/')[2],id:location.pathname.split('/')[3]});`,
  'next/link': `import React from 'react';export default function Link({href,children,prefetch,...props}){return <a href={href} {...props}>{children}</a>;}`,
  'next-themes': `export const useTheme=()=>({theme:'dark',setTheme(){}});`,
  '@/lib/env': `export const env={NEXT_PUBLIC_API_BASE_URL:location.origin+'/api/v1'};`,
  '@/lib/supabase/client': `export const createClient=()=>({auth:{getSession:async()=>({data:{session:{access_token:'synthetic-fixture-only',user:{id:'fixture-owner'}}}}),getUser:async()=>({data:{user:{id:'fixture-owner',email:'fictional@example.invalid',user_metadata:{full_name:'Demo'}}}}),signOut:async()=>({})}});`,
};
// Count actual message render-function calls only in this synthetic dev harness.
// Instrument both versions in memory; production source is never modified.
const renderCounter = {name:'message-render-counter',setup(b){b.onLoad({filter:/[\\/]chat[\\/]ChatArea\.tsx$/},async args=>{
 const contents=source(args.path)||await fs.readFile(args.path,'utf8');
 const marker=baseline?'messages.map((msg) => {':'const Message = memo(function Message({ message }: { message: ChatMessage }) {';
 if(!contents.includes(marker))throw Error('Message profiling marker changed; update the harness.');
 return {contents:contents.replace(marker,marker+' window.__messageRenders = (window.__messageRenders || 0) + 1;'),loader:'tsx',resolveDir:path.dirname(args.path)};
});}};
const bundle = await build({ entryPoints:[path.join(root,'scripts/mobile-ui.fixture.tsx')],bundle:true,write:false,platform:'browser',format:'esm',jsx:'automatic',splitting:true,outdir:'out',tsconfig:path.join(root,'tsconfig.json'),define:{'process.env.NODE_ENV':'"development"'},plugins:[renderCounter,{name:'synthetic-mobile-adapters',setup(b){b.onResolve({filter:/.*/},args=>args.path in modules?{path:args.path,namespace:'mobile-fixture'}:undefined);b.onLoad({filter:/.*/,namespace:'mobile-fixture'},args=>({contents:modules[args.path],loader:'jsx',resolveDir:root}));if(baseline)b.onLoad({filter:/\.[jt]sx?$/},args=>{if(args.path.includes('node_modules')||!args.path.startsWith(root))return;const contents=source(args.path);return contents?{contents,loader:args.path.endsWith('x')?'tsx':'ts',resolveDir:path.dirname(args.path)}:undefined;});}}] });
const tailwindConfig=require('tailwindcss/loadConfig')(path.join(root,'tailwind.config.ts'));
tailwindConfig.content=baseline ? [{raw:execFileSync('git',['grep','-h','.',baseline,'--','apps/web/**/*.tsx','apps/web/**/*.ts'],{cwd:repo,encoding:'utf8',maxBuffer:32*1024*1024}),extension:'tsx'}] : [path.join(root,'components/**/*.{ts,tsx}'),path.join(root,'app/**/*.{ts,tsx}')];
const css=await require('postcss')([require('tailwindcss')(tailwindConfig),require('autoprefixer')]).process(source(path.join(root,'app/globals.css'))||await fs.readFile(path.join(root,'app/globals.css'),'utf8'),{from:undefined});
const files=new Map(bundle.outputFiles.map(f=>['/'+path.basename(f.path),f.contents]));
const people=Array.from({length:125},(_,i)=>({id:`person-${i}`,name:i===124?'Farzana বাংলা দীর্ঘ নাম':`Fictional Person ${String(i).padStart(3,'0')}`,role:'Designer',company:'Fictional Studio',relationship_type:'contact',notes:'Met at a fictional event. '+(i===0?'বাংলা '+ 'long-context-'.repeat(20):''),created_at:'2026-10-01',updated_at:'2026-10-01'}));
const home={followups:[],meetings:[],projects:[],recent_activity:[],opportunities:[],limits:'Fixture data only.',activation:{counts:{people:0,interactions:0,projects:0,commitments:0,ask_answers:0},targets:{people:5,interactions:3,projects:1,commitments:1,ask_answers:1},first_activated_at:null}};
const notes=Array.from({length:23},(_,i)=>({id:`synthetic-note-${i}`,title:`Fictional saved note ${i}`,body:'Fictional saved context বাংলা',updated_at:'2026-10-22T10:00:00Z'}));
let requests=[];
const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost');
  res.setHeader('Cache-Control','private, no-store');
  if(url.pathname==='/__requests'){res.setHeader('Content-Type','application/json');return res.end(JSON.stringify(requests));}
  if(url.pathname.startsWith('/api/v1/')){
    requests.push({path:url.pathname,query:url.search,method:req.method});
    res.setHeader('Content-Type','application/json');
    await new Promise(resolve=>setTimeout(resolve,Number(req.headers['x-fixture-delay']||0)));
    if(url.pathname.endsWith('/relationships/home')) return res.end(JSON.stringify(home));
    if(url.pathname.endsWith('/assistant/connections/telegram')) return res.end(JSON.stringify({available:false,status:'not_connected',linked_at:null,expires_at:null}));
    if(url.pathname.endsWith('/meetings/usage')) return res.end(JSON.stringify({used_seconds:0,limit_seconds:18000,remaining_seconds:18000,percentage_used:0,data_mode:'free_redacted',max_bytes:52428800,retention_days:7}));
    if(url.pathname.endsWith('/meetings')) return res.end(JSON.stringify({items:[],total:0,limit:100,offset:0,has_more:false}));
    if(/^\/api\/v1\/(memories|ideas|organizations|achievements|kpis|content)$/.test(url.pathname)){
      if(req.method==='POST'){let body='';for await(const chunk of req)body+=chunk;const note={...JSON.parse(body),id:randomUUID(),updated_at:'2026-10-22T10:00:00Z'};notes.unshift(note);return res.end(JSON.stringify(note));}
      const offset=Number(url.searchParams.get('offset')||0),limit=Number(url.searchParams.get('limit')||20);
      return res.end(JSON.stringify({items:notes.slice(offset,offset+limit),total:notes.length}));
    }
    if(/^\/api\/v1\/sources\/[^/]+\/[^/]+$/.test(url.pathname)){
      const note=notes.find(row=>row.id===url.pathname.split('/').at(-1));
      return res.end(JSON.stringify(note?{...note,text:note.body}:{title:'Fictional conversation',text:'Fictional source evidence বাংলা.',updated_at:'2026-10-22T10:00:00Z'}));
    }
    if(url.pathname.endsWith('/people')) {
      if(req.method==='POST'){let body='';for await(const chunk of req)body+=chunk;const row={...JSON.parse(body),id:randomUUID()};people.unshift(row);return res.end(JSON.stringify(row));}
      const q=url.searchParams.get('q')?.toLowerCase()||'';const tag=url.searchParams.get('relationship_type');
      const rows=people.filter(p=>(!q||[p.name,p.company,p.notes].join(' ').toLowerCase().includes(q))&&(!tag||p.relationship_type===tag));
      const offset=Number(url.searchParams.get('offset')||0),limit=Number(url.searchParams.get('limit')||100);
      return res.end(JSON.stringify({items:rows.slice(offset,offset+limit),total:rows.length}));
    }
    if(/^\/api\/v1\/people\/[^/]+$/.test(url.pathname)){
      const id=url.pathname.split('/').at(-1);const row=people.find(person=>person.id===id);
      if(!row){res.statusCode=404;return res.end(JSON.stringify({error:{code:'NOT_FOUND',message:'Synthetic record not found'}}));}
      if(req.method==='PATCH'){let body='';for await(const chunk of req)body+=chunk;Object.assign(row,JSON.parse(body));}
      if(req.method==='DELETE'){people.splice(people.indexOf(row),1);res.statusCode=204;return res.end();}
      return res.end(JSON.stringify(row));
    }
    if(/^\/api\/v1\/relationships\/people\/[^/]+$/.test(url.pathname)){
      const person=people.find(person=>person.id===url.pathname.split('/').at(-1));
      return res.end(JSON.stringify({person:{...person,id:person?.id,title:person?.name,kind:'person',uri:'/people/'+person?.id},first_interaction:null,last_interaction:null,recency:{label:'Unknown',days_since:null,interaction_count:0,explanation:'No recorded interaction.',rule:'Recency only.'},timeline:[],topics:[],affiliations:[],related:[],commitments:[],tasks:[],brief:[],followups:[],moments:[],limits:'Synthetic data only.'}));
    }
    if(url.pathname.endsWith('/claims'))return res.end('[]');
    if(url.pathname.endsWith('/ai/content-generate')) return res.end(JSON.stringify({generated_text:'Saved source excerpt (fixture): Met Farzana at the fictional event. '+ 'https://example.invalid/'.repeat(14),citations:[{id:'fictional-source',entity_type:'interaction',title:'Fictional conversation বাংলা'}]}));
    if(url.pathname.endsWith('/tasks')&&req.method==='GET')return res.end(JSON.stringify({items:[],total:0}));
    return res.end(JSON.stringify({items:[],total:0}));
  }
  if(files.has(url.pathname)){res.setHeader('Content-Type','application/javascript');return res.end(files.get(url.pathname));}
  if(url.pathname==='/style.css'){res.setHeader('Content-Type','text/css');return res.end(css.css+'\n:root{--font-inter:Arial,sans-serif;--font-jetbrains-mono:monospace;--font-outfit:Arial,sans-serif}');}
  const theme=url.searchParams.get('theme')==='dark'?'dark':'light';
  res.setHeader('Content-Type','text/html');res.end(`<!doctype html><html lang="en" class="${theme}"><head><title>Second Brain synthetic mobile QA</title><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="stylesheet" href="/style.css"></head><body><div id="root"></div><script type="module" src="/mobile-ui.fixture.js"></script></body></html>`);
});
server.listen(Number(process.env.MOBILE_FIXTURE_PORT||4174),'127.0.0.1',()=>console.log('Synthetic mobile UI ready at http://127.0.0.1:'+server.address().port));
