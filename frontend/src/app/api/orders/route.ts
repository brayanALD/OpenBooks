import { proxyWithSession } from "@/lib/route-handlers";

// Crear un pedido (checkout). Los pedidos se LEEN desde el servidor con `lib/orders.ts`, no desde el navegador.
export const POST = (request: Request) => proxyWithSession(request, "/orders", "POST");
