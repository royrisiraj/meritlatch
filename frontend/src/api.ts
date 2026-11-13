export class ApiError extends Error {
  constructor(public status: number, public codes: string[]) { super(codes.join(', ')); }
}
export function errorText(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Connection unavailable. Check the local server, then refresh. No mutation was automatically retried.';
  const context = error.status === 409 ? 'State changed or request conflicts. Current data has been refreshed; review it before submitting again.' : error.status === 401 ? 'Session ended. Log in again.' : error.status === 403 ? 'Your authenticated role cannot perform this action.' : error.status === 404 ? 'Record unavailable in your assigned tenant or job.' : error.status === 429 ? 'Rate limit reached. Wait before trying again.' : 'Request denied. Check the fields and current evidence before retrying.';
  return `${context} ${error.codes.join(', ')}`;
}
export const operationKey = () => crypto.randomUUID().replaceAll('-', '');
export class Api {
  constructor(private token: () => string | null, private expired: () => void, private base = import.meta.env.VITE_API_BASE_PATH || '') {
    if (base && (!/^\/[A-Za-z0-9/_-]*$/.test(base) || base.startsWith('//'))) throw new Error('API base must be a same-origin path');
  }
  async request<T>(path: string, options: RequestInit = {}, binary = false): Promise<T> {
    if (!/^\/v1\//.test(path) || path.includes('..') || path.includes('\\')) throw new Error('Unsupported API path');
    const token = this.token();
    const headers = new Headers(options.headers);
    if (token) headers.set('Authorization', `Bearer ${token}`);
    if (options.body && typeof options.body === 'string') headers.set('Content-Type', 'application/json');
    const response = await fetch(this.base + path, { ...options, headers, credentials: 'omit', cache: 'no-store', redirect: 'error', signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(30000)]) : AbortSignal.timeout(30000) });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const codes = Array.isArray(body.reason_codes) ? body.reason_codes.filter((v: unknown) => typeof v === 'string' && /^[A-Z0-9_]{1,80}$/.test(v)).slice(0, 20) : ['REQUEST_FAILED'];
      if (response.status === 401 && token === this.token()) this.expired();
      throw new ApiError(response.status, codes);
    }
    return (binary ? await response.blob() : await response.json()) as T;
  }
  get<T>(path: string, signal?: AbortSignal) { return this.request<T>(path, { signal }); }
  post<T>(path: string, data: unknown) { return this.request<T>(path, { method: 'POST', body: JSON.stringify(data) }); }
  patch<T>(path: string, data: unknown) { return this.request<T>(path, { method: 'PATCH', body: JSON.stringify(data) }); }
}
