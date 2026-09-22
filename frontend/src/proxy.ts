import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE } from "@/lib/session-cookie";

/**
 * Comprobación optimista: si ni siquiera hay cookie de sesión, se manda al login sin renderizar la página.
 * NO valida el token (eso lo hace cada página privada con `requireUser`, que consulta al backend);
 * sirve para ahorrar trabajo y para que la URL de destino se conserve en `?next=`.
 */
export function proxy(request: NextRequest) {
  if (request.cookies.has(SESSION_COOKIE)) return NextResponse.next();

  const login = new URL("/login", request.url);
  login.searchParams.set("next", request.nextUrl.pathname + request.nextUrl.search);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/cuenta/:path*", "/checkout/:path*", "/admin/:path*"],
};
