import { NextResponse } from "next/server";
import { proxyWithSession } from "@/lib/route-handlers";

// Proxy hacia /admin/* del backend. No decide permisos: el backend exige el rol de administrador en cada endpoint
// (401 sin sesión, 403 a los clientes). Aquí solo se valida la forma de la ruta.
const SAFE_PATH = /^[A-Za-z0-9_-]+(\/[A-Za-z0-9_-]+)*$/;

type Context = { params: Promise<{ path: string[] }> };

async function forward(request: Request, { params }: Context, method: "GET" | "POST" | "PATCH" | "DELETE") {
  const path = (await params).path.join("/");
  if (!SAFE_PATH.test(path)) return NextResponse.json({ detail: "Ruta no válida" }, { status: 404 });
  const query = new URL(request.url).search;
  return proxyWithSession(request, `/admin/${path}${query}`, method);
}

export const GET = (request: Request, context: Context) => forward(request, context, "GET");
export const POST = (request: Request, context: Context) => forward(request, context, "POST");
export const PATCH = (request: Request, context: Context) => forward(request, context, "PATCH");
export const DELETE = (request: Request, context: Context) => forward(request, context, "DELETE");
