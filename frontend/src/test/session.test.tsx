import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { it, expect, vi, beforeEach } from 'vitest';
import { Application } from '../App';
beforeEach(() => { history.replaceState({}, '', '/login'); localStorage.clear(); sessionStorage.clear(); });
function session(role = 'CONTRACTOR') {
return vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, init) => {
    const path = String(url);
    if (path === '/v1/auth/login') return new Response(JSON.stringify({ access_token: 'opaque', expires_in: 3600 }));
    if (path === '/v1/me') return new Response(JSON.stringify({ id: 'user', username: 'fictional', tenant_id: 'a', role }));
    if (path === '/v1/auth/logout') return new Response('{}');
    if (path === '/v1/jobs') return new Response('[]');
    if (path.includes('/v1/')) return new Response(JSON.stringify({ items: [], next_cursor: null }));
    throw new Error('Unexpected request');
  });
}
async function login() { const u = userEvent.setup(); await u.type(screen.getByLabelText('Tenant'), 'a'); await u.type(screen.getByLabelText('Username'), 'fictional'); await u.type(screen.getByLabelText('Password'), 'fictional-password'); await u.click(screen.getByRole('button', { name: 'Sign in' })); return u; }
it('authenticates then navigates by backend role, with empty state and logout', async () => { const f = session(); render(<Application />); const u = await login(); expect(await screen.findByRole('heading', { name: 'Assigned work' })).toBeVisible(); expect(await screen.findByText('No assigned jobs returned by the server.')).toBeVisible(); expect(screen.queryByRole('link', { name: 'Review queue' })).toBeNull(); await u.click(screen.getByRole('button', { name: 'Log out' })); expect(await screen.findByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible(); expect(f.mock.calls.some(([url]) => url === '/v1/auth/logout')).toBe(true); expect(localStorage.length + sessionStorage.length).toBe(0); });
it.each([['MANAGER', 'Manager review queue'], ['ENGINEER', 'Security assurance workspace'], ['SERVICE_AGENT', 'Restricted service-agent workspace']])('routes actual %s identity', async (role, title) => { session(role); render(<Application />); await login(); expect(await screen.findByRole('heading', { name: title })).toBeVisible(); });
it('blocks a manager deep link for contractor even after login', async () => { session(); render(<Application />); await login(); await screen.findByRole('heading', { name: 'Assigned work' }); history.pushState({}, '', '/manager/queue'); window.dispatchEvent(new PopStateEvent('popstate')); expect(await screen.findByRole('heading', { name: 'Unauthorized workspace' })).toBeVisible(); });
it('handles login failures without fake session', async () => { vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ reason_codes: ['INVALID_CREDENTIALS'] }), { status: 401 })); render(<Application />); await login(); expect(await screen.findByRole('alert')).toHaveTextContent('INVALID_CREDENTIALS'); expect(screen.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible(); });
it('shows loading while login is pending', async () => { vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => { })); render(<Application />); await login(); expect(await screen.findByRole('button', { name: 'Signing in…' })).toBeDisabled(); });
it('handles expired session on a protected read', async () => { const f = session(); render(<Application />); await login(); await screen.findByRole('heading', { name: 'Assigned work' }); f.mockResolvedValue(new Response(JSON.stringify({ reason_codes: ['AUTHENTICATION_REQUIRED'] }), { status: 401 })); await userEvent.click(screen.getByRole('button', { name: 'Refresh jobs' })); await waitFor(() => expect(screen.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible()); });
