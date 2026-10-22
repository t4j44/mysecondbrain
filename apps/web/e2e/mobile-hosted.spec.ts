import fs from 'node:fs/promises';
import {test,expect} from '@playwright/test';

// Real Next.js, Supabase auth and staging API. No mocked data or API responses.
test('real primary routes load, stay within viewport and preserve a capture draft',async({page},info)=>{
 const failures:string[]=[];page.on('response',response=>{if(response.url().includes('second-brain-api-staging')&&response.status()>=500)failures.push(`${response.status()} ${new URL(response.url()).pathname}`);});
 for(const route of ['dashboard','people','assistant','capture','work']){
  await page.goto('/'+route);await expect(page.getByRole('button',{name:'Account options'})).toBeVisible();
  if(route==='dashboard')await expect(page.getByText('No follow-ups due',{exact:false})).toBeVisible();
  if(route==='assistant')await expect(page.getByRole('textbox',{name:'Your question'})).toBeVisible();
  if(route==='capture'){
   await page.getByRole('textbox',{name:'Capture text'}).fill('Synthetic local draft বাংলা, not submitted to AI.');await page.reload();
   await expect(page.getByRole('textbox',{name:'Capture text'})).toHaveValue('Synthetic local draft বাংলা, not submitted to AI.');
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  const output=`../../.test-tmp/mobile-overhaul/staging-screenshots/${route}-${info.project.name}.png`;await fs.mkdir('../../.test-tmp/mobile-overhaul/staging-screenshots',{recursive:true});await page.screenshot({path:output,fullPage:true});
 }
 expect(failures).toEqual([]);
});

test('real contact create, edit, refresh and confirmed archive persist',async({page},info)=>{
 const name=`Synthetic বাংলা ${info.project.name} ${Date.now()}`;
 await page.goto('/people/new');await page.getByRole('textbox',{name:'Full name'}).fill(name);
 await page.getByRole('textbox',{name:'Company',exact:true}).fill('Fictional staging studio');
 await page.getByRole('button',{name:'Save person',exact:true}).click();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
 await page.reload();await expect(page.getByRole('heading',{name,exact:true})).toBeVisible();
 await page.goto(page.url()+'/edit');await page.getByRole('textbox',{name:'Full name'}).fill(name+' updated');await page.getByRole('button',{name:'Save changes',exact:true}).click();
 await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();
 await page.reload();await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Archive contact',exact:true}).click();await page.getByRole('alertdialog').getByRole('button',{name:'Cancel',exact:true}).click();
 await expect(page.getByRole('heading',{name:name+' updated',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Archive contact',exact:true}).click();await page.getByRole('alertdialog').getByRole('button',{name:'Archive Contact',exact:true}).click();await expect(page).toHaveURL(/\/people$/);
 await page.getByTestId('people-search').fill(name);await expect(page.getByTestId('person-card')).toHaveCount(0);
});
