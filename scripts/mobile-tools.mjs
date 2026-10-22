import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
const directory=path.resolve('.test-tmp/mobile-tools');await fs.mkdir(directory,{recursive:true});
const dependencies={'lighthouse':'13.5.0','@axe-core/playwright':'4.14.0'};
await fs.writeFile(path.join(directory,'package.json'),JSON.stringify({name:'second-brain-local-audit-tools',private:true,dependencies},null,2));
console.log('Audit-only tool versions',dependencies);
const candidates=[process.env.npm_execpath,path.join(path.dirname(process.execPath),'node_modules/npm/bin/npm-cli.js'),path.resolve(path.dirname(process.execPath),'../node_modules/npm/bin/npm-cli.js'),path.resolve(path.dirname(process.execPath),'../lib/node_modules/npm/bin/npm-cli.js'),path.join(process.env.ProgramFiles||'', 'nodejs/node_modules/npm/bin/npm-cli.js')].filter(Boolean);
let npm;for(const candidate of candidates){try{await fs.access(candidate);npm=candidate;break;}catch{}}
if(!npm)throw Error('npm CLI not found. Run npm install --prefix .test-tmp/mobile-tools lighthouse@13.5.0 @axe-core/playwright@4.14.0');
const child=spawn(process.execPath,[npm,'install','--prefix',directory,'--ignore-scripts','--no-audit','--no-fund'],{stdio:'inherit',windowsHide:true,env:{...process.env,PATH:path.dirname(process.execPath)+path.delimiter+process.env.PATH}});
process.exitCode=await new Promise(resolve=>child.on('exit',resolve));
