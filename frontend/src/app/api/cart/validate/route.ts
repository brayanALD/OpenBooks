import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

// Proxy hacia FastAPI: el navegador habla con su propio origen, sin CORS ni la URL del backend.
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "JSON inválido" }, { status: 400 });
  }

  try {
    const response = await backendFetch("/cart/validate", { method: "POST", json: body });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "No se pudo contactar con la API" }, { status: 502 });
  }
}
