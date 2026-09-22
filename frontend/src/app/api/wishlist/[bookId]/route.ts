import { NextResponse } from "next/server";
import { proxyWithSession } from "@/lib/route-handlers";

const SAFE_ID = /^[A-Za-z0-9_-]{1,64}$/;

type Context = { params: Promise<{ bookId: string }> };

async function forward(request: Request, { params }: Context, method: "PUT" | "DELETE") {
  const { bookId } = await params;
  if (!SAFE_ID.test(bookId)) return NextResponse.json({ detail: "Libro no válido" }, { status: 404 });
  return proxyWithSession(request, `/wishlist/${bookId}`, method);
}

export const PUT = (request: Request, context: Context) => forward(request, context, "PUT");
export const DELETE = (request: Request, context: Context) => forward(request, context, "DELETE");
