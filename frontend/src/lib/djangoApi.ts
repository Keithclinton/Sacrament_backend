import "server-only";

import { getAccessToken, getRefreshToken, setSessionCookies } from "./session";

const BASE_URL = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000";

export class DjangoApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`Django API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * Server-side-only fetch wrapper around the Django API. Attaches the JWT
 * access token from the httpOnly cookie (never exposed to browser JS) and
 * transparently refreshes it once on a 401 before giving up - callers never
 * need to think about token expiry.
 */
export async function djangoFetch(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<{ status: number; data: unknown }> {
  const { auth = true, headers, ...rest } = options;
  const doFetch = async () => {
    const finalHeaders = new Headers(headers);
    finalHeaders.set("Content-Type", "application/json");
    if (auth) {
      const token = await getAccessToken();
      if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
    }
    return fetch(`${BASE_URL}${path}`, { ...rest, headers: finalHeaders, cache: "no-store" });
  };

  let response = await doFetch();

  if (response.status === 401 && auth) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      response = await doFetch();
    }
  }

  const data = await parseBody(response);
  return { status: response.status, data };
}

async function tryRefresh(): Promise<boolean> {
  const refresh = await getRefreshToken();
  if (!refresh) return false;

  const response = await fetch(`${BASE_URL}/api/accounts/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!response.ok) return false;

  const data = (await response.json()) as { access: string; refresh?: string };
  await setSessionCookies(data.access, data.refresh ?? refresh);
  return true;
}
