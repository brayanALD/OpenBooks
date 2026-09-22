import { NextResponse } from "next/server";
import { proxyWithSession } from "@/lib/route-handlers";

// Editar o borrar MI reseña de un libro. El backend solo deja tocar la propia.
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

type Context = { params: Promise<{ slug: string }> };

async function forward(request: Request, { params }: Context, method: "PUT" | "DELETE") {
  const { slug } = await params;
  if (!SLUG.test(slug)) return NextResponse.json({ detail: "Libro no válido" }, { status: 404 });
  return proxyWithSession(request, `/books/${slug}/reviews/mine`, method);
}

export const PUT = (request: Request, context: Context) => forward(request, context, "PUT");
export const DELETE = (request: Request, context: Context) => forward(request, context, "DELETE");
