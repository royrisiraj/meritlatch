// Supplementary read-only browser measurement of an already executed rehearsal.
import { chromium, expect } from '@playwright/test';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const summary = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const last = summary.rehearsals.at(-1);
if (last.status !== 'PASSED') throw new Error('PASSED_REHEARSAL_REQUIRED');
const root = last.steps[0].operator_root;
const extracted = path.resolve(root, '../..');
const output = path.resolve(process.argv[3]);
fs.mkdirSync(output, { recursive: false, mode: 0o700 });
const python = path.join(source, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => ['SystemRoot', 'WINDIR', 'PATH', 'Path', 'PATHEXT', 'COMSPEC', 'USERPROFILE', 'LOCALAPPDATA', 'HOME'].includes(k)));
Object.assign(env, { PYTHONUTF8: '1', TEMP: path.join(source, '.venv'), TMP: path.join(source, '.venv'), TMPDIR: path.join(source, '.venv') });
function cli(...args) {
  const p = spawnSync(python, ['-m', 'backend.tools.local_ops', ...args], { cwd: extracted, env, windowsHide: true, encoding: 'utf8', timeout: 60000 });
  if (p.status !== 0) throw new Error('LOCAL_OPERATION_FAILED');
  return JSON.parse(p.stdout.trim());
}
let service, browser;
const result = { classification: 'READ_ONLY_ACTUAL_BROWSER_INSPECTION', source: 'PREVIOUSLY_EXECUTED_SYNTHETIC_REHEARSAL_3', package_sha256: last.package_sha256, samples: 1, started_at: new Date().toISOString() };
try {
  service = cli('start', '--root', root, '--port', '0', '--fixture', 'unsafe-then-valid', '--acknowledge-canned', '--resume');
  browser = await chromium.launch({ env, headless: true });
  result.chromium = browser.version();
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.route('**/*', r => new URL(r.request().url()).origin === service.url ? r.continue() : r.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', () => errors.push('UNEXPECTED_PAGE_ERROR'));
  const began = performance.now();
  await page.goto(service.url + '/login');
  await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
  result.login_screen_ready_ms = performance.now() - began;
  result.navigation = await page.evaluate(() => { const n = performance.getEntriesByType('navigation')[0]; return { response_end_ms: n.responseEnd, dom_content_loaded_ms: n.domContentLoadedEventEnd, load_event_end_ms: n.loadEventEnd, transfer_bytes: n.transferSize }; });
  const credentials = JSON.parse(fs.readFileSync(path.join(root, 'data/credentials.local.json'), 'utf8')).engineer;
  await page.getByLabel('Tenant', { exact: true }).fill(credentials.tenant_id);
  await page.getByLabel('Username', { exact: true }).fill(credentials.username);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Log out', exact: true })).toBeVisible();
  const run = last.steps.find(s => s.name === 'weak_synthetic_run_genuine_finding_and_blocked_gate').run_id;
  await page.evaluate(url => { history.pushState({}, '', url); window.dispatchEvent(new PopStateEvent('popstate')); }, `/engineer/runs/${run}`);
  await expect(page.getByText(/SYNTHETIC SECURITY EVALUATION/)).toBeVisible();
  await expect(page.getByText('1/26 — 3.85%', { exact: true })).toBeVisible();
  await expect(page.getByText('0/6 — 0.00%', { exact: true })).toBeVisible();
  await page.screenshot({ path: path.join(output, '05-synthetic-metrics.png'), fullPage: true });
  expect(errors).toEqual([]);
  result.status = 'PASSED'; result.errors = errors; result.run_id = run;
} finally {
  if (browser) await browser.close();
  if (service) result.shutdown = cli('stop', '--root', root).status;
  result.finished_at = new Date().toISOString();
  fs.writeFileSync(path.join(output, 'inspection.json'), JSON.stringify(result, null, 2));
}
console.log(JSON.stringify(result));
