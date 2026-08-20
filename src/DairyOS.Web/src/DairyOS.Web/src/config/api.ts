export function apiUrl(path: string): string {
  const base = 'http://localhost:8000';
  return `${base}${path.startsWith('/') ? '' : '/'}${path}`;
}
