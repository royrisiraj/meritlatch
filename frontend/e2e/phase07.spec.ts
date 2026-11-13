import { test, expect, type Page, type APIRequestContext, type TestInfo } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

// Actual local FastAPI/Chromium. Only acknowledged fictional fixtures are used.
type User = { tenant_id: string; username: string; password: string; id: string };
const root = () => process.env.SENTINEL_E2E_ROOT!;
const users = (): Record<string, User> => JSON.parse(readFileSync(path.join(root(), 'canned', 'credentials.local.json'), 'utf8'));
async function login(page: Page, name: string) {
  const u = users()[name]; await page.goto('/login');
  await page.getByLabel('Tenant', { exact: true }).fill(u.tenant_id);
  await page.getByLabel('Username', { exact: true }).fill(u.username);
  await page.getByLabel('Password', { exact: true }).fill(u.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
}
async function actor(request: APIRequestContext, name: string) {
  const u = users()[name]; const origin = 'http://127.0.0.1:8015';
  const response = await request.post(origin + '/v1/auth/login', { data: { tenant_id: u.tenant_id, username: u.username, password: u.password } });
  expect(response.status()).toBe(200);
  return { origin, headers: { Authorization: `Bearer ${(await response.json()).access_token}` } };
}
async function navigate(page: Page, url: string) {
  await page.evaluate(url => { history.pushState({}, '', url); window.dispatchEvent(new PopStateEvent('popstate')); }, url);
}
async function capture(page: Page, info: TestInfo, name: string) {
  await page.screenshot({ path: info.outputPath(name + '.png'), fullPage: true, mask: [page.locator('input[type=password], .callout code, [data-sensitive]')] });
}
async function reflow(page: Page, width: number) {
  await page.setViewportSize({ width, height: 1000 });
  const overflow = await page.evaluate(() => ({ width:innerWidth, scroll:document.documentElement.scrollWidth, elements:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})).slice(0,12) }));
  expect(overflow.scroll, JSON.stringify(overflow)).toBeLessThanOrEqual(width);
}
async function keyboardDisclosure(page: Page) {
  const summary = page.locator('details > summary').first();
  await expect(summary).toBeVisible(); await summary.focus(); await expect(summary).toBeFocused();
  const wasOpen = await summary.evaluate(e => (e.parentElement as HTMLDetailsElement).open);
  await page.keyboard.press('Enter');
  expect(await summary.evaluate(e => (e.parentElement as HTMLDetailsElement).open)).toBe(!wasOpen);
  expect(await summary.evaluate(e => getComputedStyle(e).outlineStyle)).not.toBe('none');
}
async function measuredContrast(page: Page, info: TestInfo, selector: string, name: string) {
  const ratio = await page.locator(selector).first().evaluate(element => {
    const rgb = (value: string) => value.match(/[\d.]+/g)!.slice(0, 3).map(Number);
    const lum = (v: number[]) => v.map(n => { const c = n / 255; return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4; }).reduce((a, c, i) => a + c * [.2126, .7152, .0722][i], 0);
    let node: Element | null = element; let background = 'rgb(255, 255, 255)';
    while (node) { const color = getComputedStyle(node).backgroundColor; if (color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent') { background = color; break; } node = node.parentElement; }
    const a = lum(rgb(getComputedStyle(element).color)), b = lum(rgb(background));
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  });
  writeFileSync(info.outputPath(name + '-contrast.json'), JSON.stringify({ selector, samples: 1, ratio, minimum: 4.5 }, null, 2));
  expect(ratio).toBeGreaterThanOrEqual(4.5);
}

test('Phase 07 real business screens, responsive controls and keyboard disclosure', async ({ browser, request }, info) => {
  const managerContext = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const contractorContext = await browser.newContext({ viewport: { width: 375, height: 1000 }, reducedMotion: 'reduce' });
  const m = await managerContext.newPage(), c = await contractorContext.newPage();
  const errors: string[] = []; for (const p of [m, c]) p.on('pageerror', () => errors.push('UNEXPECTED_PAGE_ERROR'));
  try {
    await m.goto('/login'); await expect(m.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
    await capture(m, info, '01-login-desktop');
    await measuredContrast(m, info, 'button', 'login-button');
    await m.getByLabel('Tenant', { exact: true }).focus(); await m.keyboard.press('Tab');
    await expect(m.getByLabel('Username', { exact: true })).toBeFocused();
    await login(m, 'manager');
    await measuredContrast(m, info, '.workspace-nav a.active', 'active-navigation');
    await measuredContrast(m, info, 'button.secondary', 'secondary-button');
    const auth = await actor(request, 'manager'), agent = await actor(request, 'agent'), u = users();
    const job = await request.post(auth.origin + '/v1/jobs', { headers: auth.headers, data: { asset_id: 'PUMP-PHASE07', contractor_id: u.contractor.id, engineer_id: u.engineer.id, service_agent_id: u.agent.id } });
    expect(job.status()).toBe(201); const jobId = (await job.json()).id;
    const created = await request.post(auth.origin + '/v1/cases', { headers: auth.headers, data: { job_id: jobId } });
    expect(created.status()).toBe(201); const id = (await created.json()).id;
    await m.getByRole('button', { name: 'Refresh queue' }).click();
    await expect(m.getByRole('link', { name: new RegExp('PUMP-PHASE07') })).toBeVisible();
    await capture(m, info, '02-manager-queue-desktop');
    await login(c, 'contractor'); await expect(c.getByRole('link', { name: 'PUMP-PHASE07', exact: true })).toBeVisible();
    await capture(c, info, '03-contractor-dashboard-mobile');
    await navigate(c, `/contractor/cases/${id}`);
    await expect(c.getByLabel('Server permission L0')).toBeVisible();
    await c.getByRole('button', { name: 'Issue fresh challenge' }).click();
    await expect(c.getByText(/Expires /)).toBeVisible();
    // Unique fictional bytes avoid colliding with the original suite's scoped
    // duplicate checks. PNG decoding ignores this harmless trailing test marker.
    await c.getByLabel(/Inspection image/).setInputFiles({ name:'phase07-unsafe.png', mimeType:'image/png', buffer:Buffer.concat([readFileSync(path.join(root(), 'canned', 'evidence-1.png')), Buffer.from(`phase07-${id}`)]) });
    await c.getByRole('button', { name: 'Upload evidence', exact: true }).click();
    await expect(c.getByText('Inspection: SAFETY_ALERT', { exact: true })).toBeVisible();
    await expect(c.getByLabel('Server permission L1')).toBeVisible();
    await measuredContrast(c, info, '.ladder .current', 'current-permission');
    await capture(c, info, '04-contractor-unsafe-mobile');
    await measuredContrast(c, info, '.safety-notice', 'safety-notice');
    await navigate(m, `/manager/cases/${id}`);
    await expect(m.getByText('Inspection: SAFETY_ALERT', { exact: true })).toBeVisible();
    await m.getByRole('checkbox', { name: 'Confirm rejection and request corrected new evidence.' }).check();
    await m.getByRole('button', { name: 'Reject evidence', exact: true }).click();
    await expect(m.getByText('Business: REJECTED', { exact: true })).toBeVisible();
    await c.getByRole('button', { name: 'Refresh current case' }).click();
    await expect(c.getByText('Business: REJECTED', { exact: true })).toBeVisible();
    await c.getByRole('button', { name: 'Issue fresh challenge' }).click();
    await expect(c.getByText(/Expires /)).toBeVisible();
    await c.getByLabel(/Inspection image/).setInputFiles({ name:'phase07-correction.png', mimeType:'image/png', buffer:Buffer.concat([readFileSync(path.join(root(), 'canned', 'evidence-2.png')), Buffer.from(`phase07-${id}`)]) });
    await capture(c, info, '05-contractor-correction-upload-mobile');
    await c.getByRole('button', { name: 'Upload evidence', exact: true }).click();
    await expect(c.getByLabel('Server permission L2')).toBeVisible();
    for (const width of [375, 768, 1440, 320]) {
      await reflow(c, width); await c.getByRole('button', { name: 'Issue fresh challenge' }).scrollIntoViewIfNeeded();
      await expect(c.getByRole('button', { name: 'Issue fresh challenge' })).toBeInViewport();
      expect((await c.getByRole('button', { name: 'Issue fresh challenge' }).boundingBox())!.height).toBeGreaterThanOrEqual(44);
      await capture(c, info, `06-contractor-case-${width}`);
    }
    await keyboardDisclosure(c);
    const read = await request.get(auth.origin + `/v1/cases/${id}`, { headers: auth.headers }); const current = await read.json();
    const prepared = await request.post(agent.origin + `/v1/cases/${id}/actions/execute`, { headers: agent.headers, data: { expected_case_version: current.version, action: 'prepare_invoice' } });
    expect(prepared.status()).toBe(200);
    await m.getByRole('button', { name: 'Refresh current case' }).click();
    await expect(m.getByRole('button', { name: 'Approve current simulation' })).toBeEnabled();
    expect(await m.getByRole('button', { name: 'Approve current simulation' }).count()).toBe(1);
    await capture(m, info, '07-manager-evidence-review-desktop');
    await reflow(m, 768); await m.getByRole('checkbox', { name: 'I reviewed these exact versions for simulated completion.' }).scrollIntoViewIfNeeded();
    await expect(m.getByRole('checkbox', { name: 'I reviewed these exact versions for simulated completion.' })).toBeInViewport();
    await capture(m, info, '08-manager-review-tablet');
    await m.getByRole('checkbox', { name: 'I reviewed these exact versions for simulated completion.' }).check();
    await m.getByRole('button', { name: 'Approve current simulation' }).click();
    await expect(m.getByLabel('Server permission L3')).toBeVisible();
    await reflow(m, 1440); await capture(m, info, '09-manager-approved-desktop');
    expect(await c.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true);
    expect(await c.getByRole('button', { name: 'Issue fresh challenge' }).evaluate(e => getComputedStyle(e).transitionDuration)).toBe('0s');
    expect(await m.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
    expect(errors).toEqual([]);
  } finally { await managerContext.close(); await contractorContext.close(); }
});

test('Phase 07 actual engineering discrepancy, metrics and independent unpublished gate', async ({ browser, request }, info) => {
  const first = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const second = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const a = await first.newPage(), b = await second.newPage(); const auth = await actor(request, 'engineer');
  try {
    await login(a, 'engineer'); await expect(a.getByRole('heading', { name: 'Recent engineering actions', exact: true })).toBeVisible();
    await capture(a, info, '10-engineer-overview-desktop');
    await a.getByLabel('Test profile').selectOption('WEAK_TEST_ONLY');
    await a.getByRole('button', { name: 'Create test candidate' }).click();
    await a.getByRole('link', { name: /WEAK_TEST_ONLY ·/ }).first().click(); const weak = a.url().split('/').at(-1)!;
    await a.getByRole('button', { name: 'Run synthetic regression' }).click();
    await expect(a.getByRole('button', { name: 'Run synthetic regression' })).toBeEnabled();
    const runs = await request.get(auth.origin + `/v1/redteam/runs?candidate_id=${weak}`, { headers: auth.headers });
    const weakRun = (await runs.json()).items[0]; expect(weakRun.summary.false_approvals).toBe(1);
    await navigate(a, `/engineer/runs/${weakRun.id}`);
    await expect(a.getByText('1/26 — 3.85%', { exact: true })).toBeVisible();
    await expect(a.getByText('0/6 — 0.00%', { exact: true })).toBeVisible();
    await capture(a, info, '11-engineer-synthetic-metrics-desktop');
    await keyboardDisclosure(a);
    await a.getByRole('link', { name: 'Findings', exact: true }).click();
    await expect(a.getByRole('link', { name: 'A02 — FALSE_APPROVAL', exact: true }).first()).toBeVisible();
    await capture(a, info, '12-engineer-findings-desktop');
    const findings = await request.get(auth.origin + '/v1/alerts?limit=50', { headers: auth.headers });
    const finding = (await findings.json()).items.find((f: { scenario_id: string; artifact_sha256: string }) => f.scenario_id === 'A02' && f.artifact_sha256 === weakRun.artifact_sha256);
    expect(finding).toBeTruthy(); await navigate(a, `/engineer/findings/${finding.id}`);
    await expect(a.getByRole('heading', { name: 'Independent expected vs actual', exact: true })).toBeVisible();
    await capture(a, info, '13-engineer-finding-comparison-desktop');
    for (const width of [768, 375]) { await reflow(a, width); await capture(a, info, `14-engineer-finding-${width}`); }
    await reflow(a, 1440); await a.getByRole('link', { name: 'Assurance', exact: true }).click();
    await a.getByLabel('Test profile').selectOption('SAFE_BASELINE'); await a.getByRole('button', { name: 'Create test candidate' }).click();
    await a.getByRole('link', { name: /SAFE_BASELINE ·/ }).first().click(); const safe = a.url().split('/').at(-1)!;
    await a.getByRole('button', { name: 'Run synthetic regression' }).click(); await expect(a.getByRole('button', { name: 'Run synthetic regression' })).toBeEnabled();
    const safeRuns = await request.get(auth.origin + `/v1/redteam/runs?candidate_id=${safe}`, { headers: auth.headers }); const safeRun = (await safeRuns.json()).items[0];
    expect(safeRun.summary.passed).toBe(38);
    await navigate(a, `/engineer/findings/${finding.id}`); await a.getByRole('combobox', { name: 'Proposed candidate', exact: true }).selectOption(safe);
    await a.getByRole('button', { name: 'Record remediation proposal' }).click(); await expect(a.getByRole('link', { name: /Review proposed candidate/ }).first()).toBeVisible();
    const details = await request.get(auth.origin + `/v1/alerts/${finding.id}`, { headers: auth.headers }); const proposal = (await details.json()).proposals.find((p: { candidate_id: string }) => p.candidate_id === safe);
    await login(b, 'reviewer'); await navigate(b, `/engineer/candidates/${safe}?proposal=${proposal.id}`);
    await b.getByRole('combobox', { name: 'Exact completed run', exact: true }).selectOption(safeRun.id);
    await b.getByRole('checkbox', { name: 'I reviewed this exact candidate artifact, corpus and run binding.' }).check();
    await b.getByRole('button', { name: 'Record independent review' }).click(); await expect(b.getByText('review id', { exact: true })).toBeVisible();
    await b.getByRole('combobox', { name: 'Gate run', exact: true }).selectOption(safeRun.id);
    await b.getByRole('button', { name: 'Evaluate release readiness' }).click();
    await expect(b.getByRole('heading', { name: 'READY_FOR_MANUAL_RELEASE', exact: true })).toBeVisible();
    await capture(b, info, '15-engineer-unpublished-gate-desktop');
    await reflow(b, 768); await capture(b, info, '16-engineer-gate-tablet');
    const history = await request.get(auth.origin + `/v1/redteam/candidates/${safe}/history`, { headers: auth.headers });
    expect((await history.json()).gates[0].published).toBe(false);
  } finally { await first.close(); await second.close(); }
});

