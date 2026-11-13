import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Api } from './api';
import type { Identity } from './domain';
interface Session { user: Identity | null; api: Api; login: (tenant: string, username: string, password: string) => Promise<void>; logout: () => Promise<void>; notice: string }
const Context = createContext<Session | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const token = useRef<string | null>(null); const [user, setUser] = useState<Identity | null>(null); const [expires, setExpires] = useState(0); const [notice, setNotice] = useState('');
  const clear = () => { token.current = null; setUser(null); setExpires(0); setNotice('Session ended. Log in again.'); };
  const api = useMemo(() => new Api(() => token.current, clear), []);
  useEffect(() => { if (!expires) return; const timer = setTimeout(clear, Math.max(0, expires - Date.now())); return () => clearTimeout(timer); }, [expires]);
  async function login(tenant_id: string, username: string, password: string) {
    const result = await api.post<{ access_token: string; expires_in: number }>('/v1/auth/login', { tenant_id, username, password });
    token.current = result.access_token;
    try { const identity = await api.get<Identity>('/v1/me'); setUser(identity); setExpires(Date.now() + result.expires_in * 1000); setNotice(''); }
    catch (error) { clear(); throw error; }
  }
  async function logout() { try { await api.post('/v1/auth/logout', {}); } finally { clear(); } }
  return <Context.Provider value={{ user, api, login, logout, notice }}>{children}</Context.Provider>;
}
export function useAuth() { const value = useContext(Context); if (!value) throw new Error('Auth context required'); return value; }
