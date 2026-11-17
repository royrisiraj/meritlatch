import { test, expect, type Page, type TestInfo } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const users = () => JSON.parse(readFileSync(path.join(process.env.SENTINEL_E2E_ROOT!, 'canned/credentials.local.json'), 'utf8'));
async function capture(page: Page, info: TestInfo, name: string) {
  await page.screenshot({path:info.outputPath(name+'.png'),fullPage:true,mask:[page.locator('input[type=password], .callout code, [data-sensitive]')],maskColor:'#26364d'});
}
async function login(page: Page, name: string) {
  const u=users()[name]; await page.goto('/login');
  await page.getByLabel('Tenant',{exact:true}).fill(u.tenant_id);
  await page.getByLabel('Username',{exact:true}).fill(u.username);
  await page.getByLabel('Password',{exact:true}).fill(u.password);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('button',{name:'Log out',exact:true})).toBeVisible();
}
async function viewport(page: Page, width: number) {
  await page.setViewportSize({width,height:1000});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
}

test('Strata split authentication and actual role shells share Obsidian Cobalt', async ({page},info)=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/login');
  await expect(page).toHaveTitle('MeritLatch — Autonomy must be earned.');
  await expect(page.getByRole('heading',{name:'Welcome back'})).toBeVisible();
  await expect(page.getByText('EVIDENCE-BOUND AUTHORIZATION',{exact:true})).toBeVisible();
  await expect(page.locator('.geometric-mesh')).toHaveAttribute('aria-hidden','true');
  expect(await page.locator('body').evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgb(7, 8, 11)');
  const inputContrast=await page.getByLabel('Tenant',{exact:true}).evaluate(e=>{
    const c=getComputedStyle(e); const lum=(s:string)=>s.match(/[\d.]+/g)!.slice(0,3).map(Number).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const a=lum(c.borderTopColor),b=lum(c.backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  });
  expect(inputContrast).toBeGreaterThanOrEqual(3);
  writeFileSync(info.outputPath('input-boundary-contrast.json'),JSON.stringify({ratio:inputContrast,minimum:3,samples:1},null,2));
  for(const width of [1440,375,768,320]) { await viewport(page,width); await capture(page,info,`strata-login-${width}`); }
  expect(await page.getByRole('button',{name:'Sign in',exact:true}).evaluate(e=>getComputedStyle(e).transitionDuration)).toBe('0s');
  for(const unsupported of [/Google/i,/GitHub/i,/Magic link/i,/SSO/,/Register/i,/Remember/i,/Reset password/i]) expect(await page.getByRole('button',{name:unsupported}).count()).toBe(0);
  await viewport(page,1440); await login(page,'manager');
  await expect(page.getByRole('heading',{name:'Manager review queue',exact:true})).toBeVisible();
  await capture(page,info,'strata-manager-shell-1440');
  await viewport(page,375); await capture(page,info,'strata-manager-shell-375');
  await page.getByRole('button',{name:'Log out',exact:true}).click();
  await login(page,'contractor');
  await expect(page.getByRole('heading',{name:'Assigned work',exact:true})).toBeVisible();
  await capture(page,info,'strata-contractor-shell-375');
  await viewport(page,1440); await capture(page,info,'strata-contractor-shell-1440');
  expect(await page.evaluate(()=>[localStorage.length,sessionStorage.length])).toEqual([0,0]);
});

test('Strata service-agent and job forms retain real restrictions and controls', async ({page},info)=>{
  await login(page,'agent');
  await expect(page.getByRole('heading',{name:'Restricted service-agent workspace'})).toBeVisible();
  await expect(page.getByRole('navigation',{name:'Workspace'})).toHaveCount(0);
  for(const width of [1440,375]) { await viewport(page,width); await capture(page,info,`strata-agent-${width}`); }
  expect(await page.locator('.form-sheet').evaluate(e=>getComputedStyle(e).borderRadius)).toBe('16px');
  await page.getByRole('button',{name:'Log out',exact:true}).click();
  await login(page,'manager'); await page.getByRole('link',{name:'Create job',exact:true}).first().click();
  await expect(page.getByRole('button',{name:'Create assigned job'})).toBeEnabled();
  for(const width of [1440,768,375,320]) { await viewport(page,width); await capture(page,info,`strata-job-form-${width}`); }
  await page.getByLabel('Asset ID',{exact:true}).focus();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('combobox',{name:'Assigned contractor',exact:true})).toBeFocused();
});
