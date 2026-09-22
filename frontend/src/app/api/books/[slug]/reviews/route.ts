import { NextResponse } from "next/server";
import { proxyWithSession } from "@/lib/route-handlers";

// Publicar una reseña. Quién puede hacerlo (comprador verificado, una por libro) lo decide el backend.
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export async function POST(request: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!SLUG.test(slug)) return NextResponse.json({ detail: "Libro no válido" }, { status: 404 });
  return proxyWithSession(request, `/books/${slug}/reviews`, "POST");
}
