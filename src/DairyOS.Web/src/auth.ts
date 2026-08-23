export type Role = 'OWNER' | 'MANAGER' | 'MILKER' | string;

export type AuthUser = {
  username: string;
  role: Role;
  fullName: string;
  permissions: string[];
};

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem('dairyos_user');
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return localStorage.getItem('dairyos_token');
}

export function hasPermission(permission: string, user: AuthUser | null = getStoredUser()): boolean {
  return Boolean(user?.permissions?.includes(permission));
}

export function saveUser(user: AuthUser): void {
  localStorage.setItem('dairyos_user', JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem('dairyos_token');
  localStorage.removeItem('dairyos_user');
}

export function installAuthenticatedFetch(): void {
  const nativeFetch = window.fetch.bind(window);
  if ((window as Window & { __dairyosFetchInstalled?: boolean }).__dairyosFetchInstalled) return;
  (window as Window & { __dairyosFetchInstalled?: boolean }).__dairyosFetchInstalled = true;

  window.fetch = (input: RequestInfo | URL, init: RequestInit = {}) => {
    const token = getToken();
    if (!token) return nativeFetch(input, init);

    const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
    if (!headers.has('Authorization')) headers.set('Authorization', `Bearer ${token}`);
    return nativeFetch(input, { ...init, headers });
  };
}
