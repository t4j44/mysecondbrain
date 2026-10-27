/** Synthetic fixtures prove UI behavior, not hosted authentication/providers/devices. */
import {test,expect,type Page} from '@playwright/test';
import {createRequire} from 'node:module';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(path.resolve('package.json'));
const {default:AxeBuilder}=require(path.resolve('../../.test-tmp/mobile-tools/node_modules/@axe-core/playwright'));
const home={followups:[],projects:[],meetings:[],recent_activity:[],opportunities:[],limits:'Synthetic data only.',activation:{counts:{people:0},targets:{people:5},first_activated_at:null}};
async function noOverflow(page:Page){expect(await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:document.documentElement.clientWidth}))).toEqual(expect.objectContaining({width:expect.any(Number)}));expect(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth+1)).toBe(true);}
async function capture(page:Page,name:string,project:string){
 if(![320,390,430,768].includes(page.viewportSize()!.width))return;
 const out=path.resolve(process.env.MOBILE_AUDIT_OUTPUT||'../../.test-tmp/mobile-overhaul','after');await fs.mkdir(out,{recursive:true});
 await page.screenshot({path:path.join(out,`${name}-${project}.png`),fullPage:false,animations:'disabled'});
}

for(const route of ['dashboard','people','assistant','work','capture','meetings'])test(`${route}: readable layout, navigation and accessibility`,async({page},info)=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/'+route);await expect(page.locator('main h1')).toBeVisible();
 await expect(page.locator('main [role="status"]').filter({hasText:/Loading your/})).toHaveCount(0);
 await noOverflow(page);
 if(page.viewportSize()!.width<768){
  const nav=page.getByRole('navigation',{name:'Mobile Primary Navigation'});await expect(nav).toBeVisible();
  await expect(nav.getByRole('link')).toHaveCount(4);
  await expect(nav.getByRole('button',{name:'More',exact:true})).toBeVisible();
  for(const link of await nav.locator('a, button').all()){const box=await link.boundingBox();expect(box!.height).toBeGreaterThanOrEqual(44);expect(box!.width).toBeGreaterThanOrEqual(44);}
 }
 for(const button of await page.locator('main button:visible, header button:visible').all()){
  const box=await button.boundingBox();expect(box!.height).toBeGreaterThanOrEqual(43.9);expect(box!.width).toBeGreaterThanOrEqual(43.9);
 }
 await capture(page,route,info.project.name);
 if(info.project.name.endsWith('-390')){
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  await info.attach('axe',{body:JSON.stringify(result.violations,null,2),contentType:'application/json'});
  expect(result.violations.map((v:{id:string;impact:string})=>({id:v.id,impact:v.impact}))).toEqual([]);
 }
 expect(errors).toEqual([]);
});

test('capture choices preserve a draft and open the real recorder consent step',async({page},info)=>{
 await page.goto('/capture');
 const note=page.getByRole('textbox',{name:'Capture text'});
 await note.fill('A fictional note to keep.');
 await page.getByRole('button',{name:'Quick note / voice',exact:true}).click();await expect(note).toBeFocused();
 await page.getByRole('button',{name:'Document / photo',exact:true}).click();
 await expect(page.getByRole('link',{name:'Upload a document',exact:true})).toHaveAttribute('href','/documents');
 await page.getByText('Photo / business card',{exact:true}).click();
 await expect(page.getByLabel('Read a business card')).toBeVisible();await noOverflow(page);
 await capture(page,'capture-uploads',info.project.name);
 await page.getByRole('button',{name:'Document / photo',exact:true}).click();await expect(note).toHaveValue('A fictional note to keep.');
 await page.getByRole('link',{name:'Record meeting',exact:true}).click();
 await expect(page.getByRole('button',{name:'Hide recorder',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Record meeting',exact:true})).toBeDisabled();
 await expect(page.getByText('● Recording',{exact:true})).toHaveCount(0);
 await capture(page,'meeting-consent',info.project.name);await noOverflow(page);
});

test('existing dark theme and collapsed desktop sidebar remain usable',async({page},info)=>{
 test.skip(![390,1440].includes(page.viewportSize()!.width),'Representative theme and sidebar widths');
 for(const route of ['dashboard','capture','meetings']){
  await page.goto('/'+route+'?theme=dark');await expect(page.locator('main h1')).toBeVisible();await noOverflow(page);
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(result.violations).toEqual([]);
  await capture(page,`${route}-dark`,info.project.name);
 }
 if(page.viewportSize()!.width>=1024){
  await page.getByRole('button',{name:'Collapse sidebar'}).click();
  await expect(page.getByRole('navigation',{name:'Primary Navigation',exact:true}).getByRole('link',{name:'Meetings',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Expand sidebar'}).click();await noOverflow(page);
 }
});

test('authentication forms stay readable in both themes without calling a provider',async({page},info)=>{
 test.skip(page.viewportSize()!.width!==390,'Representative auth theme width');
 for(const theme of ['light','dark']) for(const route of ['login','signup','forgot-password','reset-password','verify']){
  await page.goto(`/${route}?theme=${theme}`);await expect(page.locator('main h2')).toBeVisible();await noOverflow(page);
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  expect(result.violations.map((v:{id:string;nodes:unknown[]})=>({id:v.id,nodes:v.nodes}))).toEqual([]);
  await capture(page,`${route}-${theme}`,info.project.name);
 }
});

test('home: conflict is distinct from empty and retry recovers',async({page},info)=>{
 let failed=true;await page.route('**/api/v1/relationships/home',route=>route.fulfill({status:failed?409:200,contentType:'application/json',body:JSON.stringify(failed?{error:{code:'CONFLICT',message:'Resource state conflict or duplicate detected in database',request_id:'synthetic-request-409'}}:home)}));
 await page.goto('/dashboard');await expect(page.getByRole('alert')).toContainText('service error');
 await expect(page.getByText('No follow-ups due',{exact:false})).toHaveCount(0);
 await page.getByText('Support details',{exact:true}).click();await expect(page.getByText(/synthetic-request-409/)).toBeVisible();
 await expect(page.getByText('Resource state conflict or duplicate detected in database',{exact:true})).toHaveCount(0);
 await capture(page,'dashboard-error',info.project.name);failed=false;await page.getByRole('button',{name:'Try again',exact:true}).click();
 await expect(page.getByText(/No follow-ups due/)).toBeVisible();await noOverflow(page);
});

test('people: paginates without duplicates and searches the complete fixture dataset',async({page})=>{
 const searches:string[]=[];page.on('request',request=>{if(request.url().includes('/api/v1/people?'))searches.push(request.url());});
 await page.goto('/people');await expect(page.getByTestId('person-card')).toHaveCount(30);
 await page.getByRole('button',{name:'Load more contacts',exact:true}).click();await expect(page.getByTestId('person-card')).toHaveCount(60);
 const names=await page.getByTestId('person-card').allTextContents();expect(new Set(names).size).toBe(60);
 await page.getByTestId('people-search').fill('Farzana');await expect(page.getByTestId('person-card')).toHaveCount(1);
 await expect(page.getByTestId('person-card')).toContainText('বাংলা');expect(searches.filter(url=>url.includes('q=Farzana')).length).toBe(1);await noOverflow(page);
});

test('people: failed quick add preserves typed text and does not claim success',async({page})=>{
 await page.route('**/api/v1/people',async route=>{if(route.request().method()==='POST')return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'UNAVAILABLE',message:'Synthetic failure'}})});await route.continue();});
 await page.goto('/people');await page.getByText('Quick add from a short note',{exact:true}).click();
 const input=page.getByRole('textbox',{name:'Quick add person'});await input.fill('Farzana বাংলা, Designer @ Fictional Studio');await page.getByRole('button',{name:'Save person',exact:true}).click();
 await expect(input).toHaveValue('Farzana বাংলা, Designer @ Fictional Studio');await expect(page.getByText('Could not save this person.',{exact:false})).toBeVisible();await noOverflow(page);
});

test('person form: labelled create/edit, persisted refresh and archive confirmation',async({page},info)=>{
 const name=`Synthetic নাবিলা ${info.project.name} ${Date.now()}`;
 await page.goto('/people/new');await page.getByRole('textbox',{name:'Full name'}).fill(name);
 await page.getByRole('textbox',{name:'Company',exact:true}).fill('Fictional company বাংলা '+ 'long-company'.repeat(15));
 await page.getByRole('textbox',{name:'Notes',exact:true}).fill('Met at a fictional event. Keep this note after refresh.');
 await page.getByRole('button',{name:'Save person',exact:true}).click();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
 await page.reload();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();await noOverflow(page);await capture(page,'person-detail',info.project.name);
 const url=page.url();await page.goto(url+'/edit');await page.getByRole('textbox',{name:'Full name'}).fill(name+' updated');await page.getByRole('button',{name:'Save changes',exact:true}).click();
 await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();await page.reload();await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Archive contact',exact:true}).click();
 const dialog=page.getByRole('alertdialog');await expect(dialog).toBeVisible();await dialog.getByRole('button',{name:'Cancel',exact:true}).click();
 await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Archive contact',exact:true}).click();await page.getByRole('alertdialog').getByRole('button',{name:'Archive Contact',exact:true}).click();
 await expect(page).toHaveURL(/\/people$/);expect((await page.request.get(url.replace('/people/','/api/v1/people/'))).status()).toBe(404);
});

test('assistant: sends once, wraps long sources and keeps composer above navigation',async({page},info)=>{
 let count=0;await page.route('**/api/v1/ai/content-generate',async route=>{count++;await new Promise(resolve=>setTimeout(resolve,150));await route.fulfill({contentType:'application/json',body:JSON.stringify({generated_text:'বাংলা saved excerpt. '+ 'https://example.invalid/'+ 'long-path'.repeat(100),citations:[{id:'synthetic-source',entity_type:'interaction',title:'Fictional conversation বাংলা '+ 'long-source-'.repeat(10)}]})});});
 await page.goto('/assistant');await page.getByRole('textbox',{name:'Your question'}).fill('What did I promise?');
 await page.locator('main form').evaluate(form=>{form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));});
 await expect(page.getByRole('navigation',{name:'Supporting sources'})).toBeVisible();expect(count).toBe(1);await noOverflow(page);
 const composer=await page.getByRole('textbox',{name:'Your question'}).boundingBox();
 if(page.viewportSize()!.width<768){const nav=await page.getByRole('navigation',{name:'Mobile Primary Navigation'}).boundingBox();expect(composer!.y+composer!.height).toBeLessThanOrEqual(nav!.y);}
 await capture(page,'assistant-answer',info.project.name);
});

test('assistant: visual viewport keyboard simulation keeps focused composer visible',async({page},info)=>{
 test.skip(page.viewportSize()!.width>=768,'Phone keyboard simulation only; physical keyboard behavior is a separate gate.');
 await page.goto('/assistant');await page.getByRole('textbox',{name:'Your question'}).focus();
 const visible=await page.evaluate(()=>{
  const height=innerHeight-Math.min(300,Math.round(innerHeight*.4));
  Object.defineProperty(visualViewport,'height',{configurable:true,value:height});visualViewport!.dispatchEvent(new Event('resize'));return height;
 });
 await expect(page.getByRole('navigation',{name:'Mobile Primary Navigation'})).toBeHidden();
 const box=await page.getByRole('textbox',{name:'Your question'}).boundingBox();expect(box!.y+box!.height).toBeLessThanOrEqual(visible+1);expect(box!.y).toBeGreaterThanOrEqual(0);
 await capture(page,'assistant-keyboard-simulation',info.project.name);await noOverflow(page);
});

test('capture: restores only the same-session draft and does not prefetch contact data',async({page})=>{
 let peopleRequests=0;page.on('request',request=>{if(request.url().includes('/api/v1/people'))peopleRequests++;});
 await page.goto('/capture');await page.getByRole('textbox',{name:'Capture text'}).fill('Fictional note বাংলা kept until confirmed.');await page.reload();
 await expect(page.getByRole('textbox',{name:'Capture text'})).toHaveValue('Fictional note বাংলা kept until confirmed.');expect(peopleRequests).toBe(0);await noOverflow(page);
});

test('drawer and page search trap focus, close on Escape and restore trigger focus',async({page})=>{
 await page.goto('/dashboard');
 if(page.viewportSize()!.width<768){
  await page.getByRole('button',{name:'More',exact:true}).click();const drawer=page.getByRole('dialog',{name:'Navigation',exact:true});await expect(drawer).toBeVisible();
  await expect(drawer.getByRole('link',{name:'Documents',exact:true})).toBeVisible();
  await page.keyboard.press('Tab');expect(await drawer.evaluate(element=>element.contains(document.activeElement))).toBe(true);await page.keyboard.press('Escape');await expect(drawer).toBeHidden();await expect(page.getByRole('button',{name:'More',exact:true})).toBeFocused();
 }
 await page.getByRole('button',{name:'Find a page',exact:true}).click();const search=page.getByRole('dialog',{name:'Find a page',exact:true});await expect(search).toBeVisible();
 await page.getByRole('searchbox',{name:'Search pages'}).fill('privacy');await expect(search.getByRole('link',{name:'Privacy',exact:true})).toBeVisible();await page.keyboard.press('Escape');await expect(search).toBeHidden();await expect(page.getByRole('button',{name:'Find a page',exact:true})).toBeFocused();
});

test('200 percent text remains usable without horizontal overflow',async({page},info)=>{
 for(const route of ['dashboard','people','assistant','capture','work']){
  await page.goto('/'+route);await page.locator('html').evaluate(element=>{element.style.fontSize='200%';});await noOverflow(page);
  if(route==='assistant'){
   await page.getByRole('textbox',{name:'Your question'}).fill('Readable at 200%');
   const send=page.getByRole('button',{name:'Send question'});
   expect((await page.getByRole('textbox',{name:'Your question'}).boundingBox())!.width).toBeGreaterThanOrEqual(150);
   // Enlarged text intentionally uses document scrolling. The send control must
   // remain reachable and uncovered, rather than being clipped by a fixed shell.
   await send.scrollIntoViewIfNeeded();await expect(send).toBeInViewport();
   expect(await send.evaluate(button=>{const box=button.getBoundingClientRect();return button.contains(document.elementFromPoint(box.x+box.width/2,box.y+box.height/2));})).toBe(true);
   await capture(page,'assistant-text-200',info.project.name);
  }
 }
});

test('slow home request keeps a loading state until real data arrives',async({page})=>{
 await page.goto('/dashboard');
 let release!:()=>void;
 const pending=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/v1/relationships/home',async route=>{await pending;await route.fulfill({contentType:'application/json',body:JSON.stringify(home)});});
 await page.reload({waitUntil:'domcontentloaded'});
 await expect(page.getByRole('status').filter({hasText:/Loading your/})).toBeVisible();
 await expect(page.getByText(/No follow-ups due/)).toHaveCount(0);
 release();await expect(page.getByText(/No follow-ups due/)).toBeVisible();await noOverflow(page);
});

test('offline assistant preserves the question and recovers after reconnecting',async({page,context})=>{
 await page.goto('/assistant');await context.setOffline(true);
 await page.getByRole('textbox',{name:'Your question'}).fill('Fictional question kept while offline');
 await page.getByRole('button',{name:'Send question'}).click();
 await expect(page.getByRole('alert')).toBeVisible();
 await expect(page.getByRole('article',{name:'Your question'})).toContainText('Fictional question kept while offline');
 await context.setOffline(false);await page.getByRole('button',{name:'Try again',exact:true}).click();
 await expect(page.getByRole('navigation',{name:'Supporting sources'})).toBeVisible();
 await expect(page.getByRole('article',{name:'Your question'})).toHaveCount(1);await noOverflow(page);
});

test('saved tools load actual records, paginate, and distinguish service errors',async({page},info)=>{
 test.skip(![320,390,768,1440].includes(page.viewportSize()!.width),'Secondary route sweep at four representative widths.');
 for(const route of ['organizations','memories','ideas','achievements','kpis','content']){
  await page.goto('/'+route);await expect(page.locator('main article')).toHaveCount(20);await noOverflow(page);
  await page.getByRole('button',{name:'Load more saved records'}).click();await expect.poll(()=>page.locator('main article').count()).toBeGreaterThan(20);
  await capture(page,route,info.project.name);
  if(info.project.name.endsWith('-390')){
   const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(scan.violations.map((item:{id:string})=>item.id)).toEqual([]);
  }
 }
 await page.route('**/api/v1/memories?**',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'UNAVAILABLE',message:'Synthetic failure'}})}));
 await page.goto('/memories');await expect(page.getByRole('alert')).toContainText('service error');await expect(page.getByText(/No records saved here/)).toHaveCount(0);
});

test('note form saves canonical fields, opens the source and survives refresh',async({page},info)=>{
 const title=`Fictional note ${info.project.name} ${Date.now()}`;
 let payload:Record<string,unknown>={};
 page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith('/api/v1/memories'))payload=request.postDataJSON();});
 await page.goto('/memories/new');await page.getByRole('textbox',{name:'Title',exact:true}).fill(title);await page.getByRole('textbox',{name:'Note',exact:true}).fill('Fictional evidence বাংলা kept after refresh.');
 await page.getByRole('button',{name:'Save note',exact:true}).click();await expect(page).toHaveURL(/\/sources\/memory\//);
 await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();await page.reload();await expect(page.getByText('Fictional evidence বাংলা kept after refresh.',{exact:true})).toBeVisible();
 expect(payload).toMatchObject({title,body:'Fictional evidence বাংলা kept after refresh.',type:'note',visibility:'private'});expect(payload).not.toHaveProperty('content');await noOverflow(page);
});
