// Solo para el navegador: llamadas a los Route Handlers de /api.

import { useCartStore, type CartItem } from "@/store/cart.store";
import type { User } from "@/types/user";

type Failure = {
  ok: false;
  status: number;
  message: string;
  /** Código de negocio del backend (`total_changed`, `cart_issues`…), si lo trae. */
  code?: string;
  fields: Record<string, string>;
};
type Success<T> = { ok: true; data: T };

/** Los errores 422 de FastAPI traen `loc` por campo; se traducen a `{ "address.line": "…" }`. */
function fieldErrors(detail: unknown): Record<string, string> {
  const fields: Record<string, string> = {};
  if (!Array.isArray(detail)) return fields;
  for (const problem of detail) {
    const path = Array.isArray(problem?.loc) ? problem.loc.slice(1).join(".") : "";
    if (path) fields[path] = "Revisa este dato.";
  }
  return fields;
}

export const postJson = <T>(url: string, body: unknown) => requestJson<T>("POST", url, body);

export async function requestJson<T>(method: "POST" | "PATCH" | "PUT" | "DELETE", url: string, body?: unknown): Promise<Success<T> | Failure> {
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    return { ok: false, status: 0, message: "No pudimos conectar con el servidor. Inténtalo de nuevo.", fields: {} };
  }

  const data = await response.json().catch(() => ({}));
  if (response.ok) return { ok: true, data: data as T };

  const detail = data?.detail;
  // `detail` puede ser un texto, un objeto {code, message} (errores de negocio) o la lista de campos inválidos (422).
  const business = detail && !Array.isArray(detail) && typeof detail === "object" ? detail : null;
  return {
    ok: false,
    status: response.status,
    message:
      typeof detail === "string"
        ? detail
        : typeof business?.message === "string"
          ? business.message
          : "Revisa los datos e inténtalo de nuevo.",
    code: typeof business?.code === "string" ? business.code : undefined,
    fields: fieldErrors(detail),
  };
}

export type SessionResult = { user: User };

/**
 * Justo después de iniciar sesión: suma el carrito de invitado al de la cuenta y deja el resultado en el store.
 * Si falla, el carrito local se conserva y CartSync lo subirá después.
 */
export async function mergeGuestCart(): Promise<void> {
  const local = useCartStore.getState().items;
  const result = await postJson<{ items: { book_id: string; quantity: number }[] }>("/api/cart/merge", {
    items: local.map((i) => ({ book_id: i.bookId, quantity: i.quantity })),
  });
  if (result.ok) {
    const merged: CartItem[] = result.data.items.map((i) => ({ bookId: i.book_id, quantity: i.quantity }));
    useCartStore.getState().replace(merged);
  }
}
