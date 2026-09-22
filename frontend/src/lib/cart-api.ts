import type { CartItem } from "@/store/cart.store";
import type { CartValidation } from "@/types/cart";

/** Pide al servidor los precios, el stock y los totales actuales de estos artículos. */
export async function validateCart(items: CartItem[], signal?: AbortSignal): Promise<CartValidation> {
  const response = await fetch("/api/cart/validate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ items: items.map((i) => ({ book_id: i.bookId, quantity: i.quantity })) }),
    signal,
  });
  if (!response.ok) throw new Error(`Error ${response.status} al validar el carrito`);
  return (await response.json()) as CartValidation;
}
