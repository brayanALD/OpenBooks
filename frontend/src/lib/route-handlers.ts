// Solo para Route Handlers (proxies hacia FastAPI).

import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";
import { getSessionToken, sessionCookieOptions } from "@/lib/session";
import { SESSION_COOKIE } from "@/lib/session-cookie";

/**
 * Defensa extra contra CSRF, además de SameSite=Lax: si la petición declara un origen distinto al del
 * sitio, se rechaza. Las peticiones sin cabecera Origin (curl, pruebas de servidor) no pasan por el navegador.
 */
export function crossSiteRequest(request: Request): boolean {
  const origin = request.headers.get("origin");
  return origin !== null && new URL(origin).host !== request.headers.get("host");
}

const forbidden = () => NextResponse.json({ detail: "Origen no permitido" }, { status: 403 });
const badJson = () => NextResponse.json({ detail: "JSON inválido" }, { status: 400 });
const apiDown = () => NextResponse.json({ detail: "No se pudo contactar con la API" }, { status: 502 });

async function readJson(request: Request): Promise<{ ok: true; body: unknown } | { ok: false }> {
  try {
    // Un PUT sin datos (p. ej. añadir a favoritos) llega con el cuerpo vacío: no es un JSON inválido.
    const text = await request.text();
    return { ok: true, body: text.trim() === "" ? undefined : JSON.parse(text) };
  } catch {
    return { ok: false };
  }
}

/** Registro e inicio de sesión: el token del backend no llega al navegador, se convierte en cookie httpOnly. */
export async function startSession(request: Request, backendPath: string, successStatus: number) {
  if (crossSiteRequest(request)) return forbidden();
  const parsed = await readJson(request);
  if (!parsed.ok) return badJson();

  let response: Response;
  try {
    response = await backendFetch(backendPath, { method: "POST", json: parsed.body });
  } catch {
    return apiDown();
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const headers = new Headers();
    const retryAfter = response.headers.get("retry-after");
    if (retryAfter) headers.set("retry-after", retryAfter);
    return NextResponse.json(data, { status: response.status, headers });
  }

  const result = NextResponse.json({ user: data.user }, { status: successStatus });
  result.cookies.set(SESSION_COOKIE, data.access_token, sessionCookieOptions());
  return result;
}

export function endSession(request: Request) {
  if (crossSiteRequest(request)) return forbidden();
  const result = NextResponse.json({ ok: true });
  result.cookies.set(SESSION_COOKIE, "", { ...sessionCookieOptions(), maxAge: 0 });
  return result;
}

type Method = "GET" | "PUT" | "POST" | "PATCH" | "DELETE";

/**
 * Reenvía una petición autenticada al backend con el token de la cookie.
 * Admite JSON y formularios con archivos (subida de portadas).
 */
export async function proxyWithSession(request: Request, backendPath: string, method: Method) {
  if (method !== "GET" && crossSiteRequest(request)) return forbidden();

  const token = await getSessionToken();
  if (!token) return NextResponse.json({ detail: "Sesión no válida o caducada" }, { status: 401 });

  let json: unknown;
  let formData: FormData | undefined;
  // Un DELETE no lleva cuerpo: no hay nada que leer (ni que validar).
  if (method !== "GET" && method !== "DELETE") {
    if ((request.headers.get("content-type") ?? "").startsWith("multipart/form-data")) {
      try {
        formData = await request.formData();
      } catch {
        return badJson();
      }
    } else {
      const parsed = await readJson(request);
      if (!parsed.ok) return badJson();
      json = parsed.body;
    }
  }

  try {
    const response = await backendFetch(backendPath, { method, token, json, formData });
    // 204 no admite cuerpo: `NextResponse.json` lanzaría un error.
    if (response.status === 204) return new NextResponse(null, { status: 204 });
    return NextResponse.json(await response.json().catch(() => ({})), { status: response.status });
  } catch {
    return apiDown();
  }
}
