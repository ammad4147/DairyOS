/** Read a DairyOS response without turning a plain-text server failure into a JSON parse error. */
export async function readApiPayload(
  response: Response,
  fallback: string,
): Promise<Record<string, unknown>>;
export async function readApiPayload<T extends Record<string, unknown>>(
  response: Response,
  fallback: string,
): Promise<T>;
export async function readApiPayload<T extends Record<string, unknown>>(
  response: Response,
  fallback: string,
): Promise<T> {
  const body = await response.text();
  let payload: unknown = null;

  try {
    payload = body ? JSON.parse(body) : null;
  } catch {
    throw new Error(`${fallback} (HTTP ${response.status}).`);
  }

  if (!response.ok) {
    const detail = (
      payload &&
      typeof payload === 'object' &&
      'detail' in payload
    )
      ? String((payload as { detail?: unknown }).detail || '')
      : '';
    throw new Error(detail || `${fallback} (HTTP ${response.status}).`);
  }

  return payload && typeof payload === 'object'
    ? payload as T
    : {} as T;
}
