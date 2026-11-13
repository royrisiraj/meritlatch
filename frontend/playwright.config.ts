import { defineConfig } from '@playwright/test';
import path from 'node:path';
const taskRoot = process.env.SENTINEL_E2E_ROOT || path.resolve('..', '.venv', `phase05-browser-${Date.now()}`);
process.env.SENTINEL_E2E_ROOT = taskRoot;
const python = '.\\.venv\\Scripts\\python.exe';
const tempRoot = path.resolve('..', '.venv');
export default defineConfig({
testDir: './e2e', workers: 1, retries: 0, timeout: 120000, expect: { timeout: 15000 },
  reporter: [['list']], outputDir: path.join(taskRoot, 'screenshots'),
  use: { actionTimeout: 15000, baseURL: 'http://127.0.0.1:5175', browserName: 'chromium', viewport: { width: 1440, height: 1000 }, trace: 'off', screenshot: 'only-on-failure' },
  webServer: [
    { command: `${python} -m backend.tools.portal_demo --root "${taskRoot}/canned" --port 8015 --fixture unsafe-then-valid --acknowledge-canned`, cwd: '..', url: 'http://127.0.0.1:8015/healthz', timeout: 60000, env: { PYTHONUTF8: '1', TEMP: tempRoot, TMP: tempRoot, TMPDIR: tempRoot } },
    { command: `${python} -m backend.tools.portal_demo --root "${taskRoot}/normal" --port 8016`, cwd: '..', url: 'http://127.0.0.1:8016/healthz', timeout: 60000, env: { PYTHONUTF8: '1', TEMP: tempRoot, TMP: tempRoot, TMPDIR: tempRoot } },
    { command: 'npm.cmd run dev -- --port 5175', url: 'http://127.0.0.1:5175', env: { SENTINEL_PROXY_TARGET: 'http://127.0.0.1:8015' } },
    { command: 'npm.cmd run dev -- --port 5176', url: 'http://127.0.0.1:5176', env: { SENTINEL_PROXY_TARGET: 'http://127.0.0.1:8016' } }
  ]
});
