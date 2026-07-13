import { cookies } from "next/headers";

export const ACCESS_COOKIE = "sap_access";
export const REFRESH_COOKIE = "sap_refresh";

export interface JwtClaims {
  role: "member" | "priest" | "diocesan_admin" | "super_admin";
  verification_status?: string | null;
  user_id: number;
  exp: number;
}

/**
 * Decodes the JWT payload without verifying the signature - fine here since
 * this is only used for UI routing/display decisions (which nav links to
 * show, which dashboard to redirect to). The real security boundary is
 * Django's DRF permission classes, which verify every token on every
 * request; a forged/expired token simply gets a 401/403 from the API.
 */
export function decodeJwt(token: string): JwtClaims | null {
  try {
    const payload = token.split(".")[1];
    const json = Buffer.from(payload, "base64url").toString("utf-8");
    return JSON.parse(json) as JwtClaims;
  } catch {
    return null;
  }
}

export async function getSession(): Promise<JwtClaims | null> {
  const store = await cookies();
  const access = store.get(ACCESS_COOKIE)?.value;
  if (!access) return null;
  const claims = decodeJwt(access);
  if (!claims) return null;
  if (claims.exp * 1000 < Date.now()) return null;
  return claims;
}

const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

export async function setSessionCookies(access: string, refresh: string) {
  const store = await cookies();
  store.set(ACCESS_COOKIE, access, { ...cookieOptions, maxAge: 60 * 30 });
  store.set(REFRESH_COOKIE, refresh, { ...cookieOptions, maxAge: 60 * 60 * 24 * 7 });
}

export async function clearSessionCookies() {
  const store = await cookies();
  store.delete(ACCESS_COOKIE);
  store.delete(REFRESH_COOKIE);
}

export async function getAccessToken(): Promise<string | undefined> {
  const store = await cookies();
  return store.get(ACCESS_COOKIE)?.value;
}

export async function getRefreshToken(): Promise<string | undefined> {
  const store = await cookies();
  return store.get(REFRESH_COOKIE)?.value;
}
