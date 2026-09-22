import { proxyWithSession } from "@/lib/route-handlers";

// Solo los ids de los favoritos: lo que WishlistSync necesita para pintar los corazones.
export const GET = (request: Request) => proxyWithSession(request, "/wishlist/ids", "GET");
