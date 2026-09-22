import { proxyWithSession } from "@/lib/route-handlers";

// Al iniciar sesión: suma el carrito de invitado al guardado en la cuenta.
export const POST = (request: Request) => proxyWithSession(request, "/cart/merge", "POST");
