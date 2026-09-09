/** Scope the desktop capability to this tab and exact backend origin. */
export function desktopWindowUrl(value: string): string {
  const target = new URL(value, window.location.href);
  const token = window.sessionStorage.getItem('dairyos.desktop.session');
  if (token && target.origin === window.location.origin) {
    target.hash = new URLSearchParams({ 'desktop-session': token }).toString();
  }
  return target.toString();
}

export function installDesktopSession(): void {
  const parameters = new URLSearchParams(window.location.hash.slice(1));
  const incoming = parameters.get('desktop-session');
  const key = 'dairyos.desktop.session';
  if (incoming) {
    window.sessionStorage.setItem(key, incoming);
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  }
  const token = incoming || window.sessionStorage.getItem(key);
  if (!token) return;
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    const target = new URL(input instanceof Request ? input.url : String(input), window.location.href);
    if (target.origin !== window.location.origin) return originalFetch(input, init);
    const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : undefined));
    headers.set('X-DairyOS-Desktop-Session', token);
    return originalFetch(input, { ...init, headers });
  };
}
