import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

// Ficha pública de un libro para la vista rápida de las tarjetas (descripción, editorial, páginas…).
const SAFE_SLUG = /^[a-z0-9-]{1,80}$/;

type Context = { params: Promise<{ slug: string }> };

export async function GET(_request: Request, { params }: Context) {
  const { slug } = await params;
  if (!SAFE_SLUG.test(slug)) return NextResponse.json({ detail: "Libro no encontrado" }, { status: 404 });
  try {
    const response = await backendFetch(`/books/${slug}`);
    return NextResponse.json(await response.json().catch(() => ({})), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "No se pudo contactar con la API" }, { status: 502 });
  }
}
