import { proxyWithSession } from "@/lib/route-handlers";

// Carrito guardado del usuario con sesión (lo sincroniza CartSync).
export const GET = (request: Request) => proxyWithSession(request, "/cart", "GET");
export const PUT = (request: Request) => proxyWithSession(request, "/cart", "PUT");
