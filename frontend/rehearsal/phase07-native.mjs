// Verify the new compiled frontend in a fresh, extracted native package.
import { chromium, expect, request } from '@playwright/test';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const archive = path.resolve(process.argv[2]);
const output = path.join(source, '.venv', `phase07-native-${crypto.randomUUID()}`);
fs.mkdirSync(output, { mode: 0o700 });
const python = path.join(source, '.venv/Scripts/python.exe');
const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => ['SystemRoot','WINDIR','PATH','Path','PATHEXT','COMSPEC','USERPROFILE','LOCALAPPDATA'].includes(k)));
Object.assign(env, { PYTHONUTF8:'1', TEMP:path.join(source,'.venv'), TMP:path.join(source,'.venv'), TMPDIR:path.join(source,'.venv') });
function cli(cwd, module, ...args) {
  const r = spawnSync(python, ['-m',module,...args], { cwd,env,windowsHide:true,encoding:'utf8',timeout:60000 });
  if (r.status !== 0) throw new Error('NATIVE_OPERATOR_FAILED');
  return JSON.parse(r.stdout.trim());
}
const result = { classification:'ACTUAL_NATIVE_PHASE07_COMPILED_FRONTEND', started_at:new Date().toISOString(), provider:'ACKNOWLEDGED_CANNED_MOCK_AI', remote_deployment:'NOT_ATTEMPTED' };
let service, browser, client;
const extracted = path.join(output,'package');
try {
  result.archive = cli(source,'backend.tools.release_package','verify','--package',archive);
  cli(source,'backend.tools.release_package','extract','--package',archive,'--destination',extracted);
  service = cli(extracted,'backend.tools.local_ops','start','--port','0','--fixture','unsafe-then-valid','--acknowledge-canned');
  result.startup_seconds = service.startup_seconds;
  client = await request.newContext({baseURL:service.url});
  result.http = [];
  for (const [route,status] of [['/healthz',200],['/readyz',200],['/login',200],['/v1/me',401],['/.env',404]]) {
    const r = await client.get(route); expect(r.status()).toBe(status); result.http.push({route,status});
  }
  const u = JSON.parse(fs.readFileSync(path.join(service.run_root,'data/credentials.local.json'),'utf8')).manager;
  const login = await client.post('/v1/auth/login',{data:{tenant_id:u.tenant_id,username:u.username,password:u.password}});
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  const me = await client.get('/v1/me',{headers:{Authorization:`Bearer ${token}`}});
  expect(me.status()).toBe(200); expect((await me.json()).role).toBe('MANAGER');
  result.authenticated_api = 'MANAGER_ME_200';
  browser = await chromium.launch({headless:true,env});
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const errors = []; const page = await context.newPage(); page.on('pageerror',()=>errors.push('PAGE_ERROR'));
  await context.route('**/*', r => new URL(r.request().url()).origin === service.url ? r.continue() : r.abort());
  await page.goto(service.url+'/login');
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
  expect(await page.locator('.app-header').evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgb(17, 28, 43)');
  await page.getByLabel('Tenant',{exact:true}).fill(u.tenant_id);
  await page.getByLabel('Username',{exact:true}).fill(u.username);
  await page.getByLabel('Password',{exact:true}).fill(u.password);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Manager review queue',exact:true})).toBeVisible();
  await page.screenshot({path:path.join(output,'native-manager.png'),fullPage:true});
  expect(errors).toEqual([]); result.browser_errors = errors; result.status='PASSED';
} finally {
  if(browser) await browser.close(); if(client) await client.dispose();
  if(service) result.shutdown = cli(extracted,'backend.tools.local_ops','stop','--root',service.run_root).status;
  result.finished_at=new Date().toISOString();
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2));
}
console.log(JSON.stringify({...result,evidence_root:output}));
