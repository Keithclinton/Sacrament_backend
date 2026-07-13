import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, decodeJwt } from "@/lib/session";

/**
 * Route guarding only - a UX convenience, not the security boundary. Every
 * real mutation still goes through djangoFetch -> Django's DRF permission
 * classes, which are what actually enforce authorization. A refactor that
 * moves a page/action outside this matcher must not be relied upon as the
 * only protection (see Next.js proxy.js docs, "Execution order").
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(ACCESS_COOKIE)?.value;
  const claims = token ? decodeJwt(token) : null;
  const isValid = claims && claims.exp * 1000 > Date.now();

  if (pathname.startsWith("/priest")) {
    if (!isValid || claims.role !== "priest") {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  if (pathname.startsWith("/admin")) {
    if (!isValid || !["diocesan_admin", "super_admin"].includes(claims.role)) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/priest/:path*", "/admin/:path*"],
};
