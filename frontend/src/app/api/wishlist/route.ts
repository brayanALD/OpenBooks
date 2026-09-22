import { proxyWithSession } from "@/lib/route-handlers";

// Favoritos con sus tarjetas (la página /cuenta/favoritos los lee directamente del servidor; esto es para el navegador).
export const GET = (request: Request) => proxyWithSession(request, "/wishlist", "GET");
