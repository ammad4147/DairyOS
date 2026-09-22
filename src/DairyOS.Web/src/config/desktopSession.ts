/** Scope the desktop capability to this tab and exact backend origin. */
export function desktopWindowUrl(value: string): string {
  const target = new URL(value, window.location.href);
  const token = window.sessionStorage.getItem('dairyos.desktop.session');
  if (token && target.origin === window.location.origin) {
    target.hash = new URLSearchParams({ 'desktop-session': token }).toString();
  }
  return target.toString();
}

/**
 * Attempt to acquire the desktop session token from the native JS API
 * provided by pywebview's `window.pywebview.api`.
 */
async function acquireTokenFromNativeApi(): Promise<string | null> {
  const pywebview = (window as any).pywebview;
  if (!pywebview?.api?.getDesktopSessionToken) return null;
  try {
    const token = await pywebview.api.getDesktopSessionToken();
    if (typeof token === 'string' && token.length > 0) {
      window.sessionStorage.setItem('dairyos.desktop.session', token);
      return token;
    }
  } catch {
    // pywebview API call failed — token unavailable from native bridge.
  }
  return null;
}

/**
 * Return the current desktop session token, trying sessionStorage first
 * and falling back to the native pywebview API.
 */
async function resolveToken(): Promise<string | null> {
  const cached = window.sessionStorage.getItem('dairyos.desktop.session');
  if (cached) return cached;
  return acquireTokenFromNativeApi();
}

export function installDesktopSession(): void {
  const parameters = new URLSearchParams(window.location.hash.slice(1));
  const incoming = parameters.get('desktop-session');
  const key = 'dairyos.desktop.session';
  if (incoming) {
    window.sessionStorage.setItem(key, incoming);
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  }

  // Also try acquiring from pywebview native API asynchronously.
  if (!incoming) {
    void acquireTokenFromNativeApi();
  }

  const originalFetch = window.fetch.bind(window);
  const humanSession = () => window.sessionStorage.getItem('dairyos.human.session');
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const target = new URL(input instanceof Request ? input.url : String(input), window.location.href);
    if (target.origin !== window.location.origin) return originalFetch(input, init);

    const token = await resolveToken();
    const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined));
    if (token) {
      headers.set('X-DairyOS-Desktop-Session', token);
    }
    const identitySession = humanSession();
    if (identitySession) headers.set('X-DairyOS-Human-Session', identitySession);

    const response = await originalFetch(input, { ...init, headers });

    // On 401, attempt one re-acquisition of the desktop session token and retry.
    if (response.status === 401) {
      const freshToken = await acquireTokenFromNativeApi();
      if (freshToken && freshToken !== token) {
        const retryHeaders = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined));
        retryHeaders.set('X-DairyOS-Desktop-Session', freshToken);
        const retryIdentitySession = humanSession();
        if (retryIdentitySession) retryHeaders.set('X-DairyOS-Human-Session', retryIdentitySession);
        return originalFetch(input, { ...init, headers: retryHeaders });
      }
    }

    return response;
  };
}
