import { NextResponse, type NextRequest } from "next/server";

import { AUTH_COOKIE } from "@/lib/auth-cookie";

// 낙관적 검사: 쿠키 유무만 본다. 실제 인증은 백엔드가 매 요청 검증한다.
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const loggedIn = request.cookies.has(AUTH_COOKIE);
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  if (!loggedIn && !isAuthPage) {
    const url = new URL("/login", request.url);
    url.searchParams.set("next", pathname + search);
    return NextResponse.redirect(url);
  }
  if (loggedIn && isAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/debates/:path*", "/login", "/signup"],
};
