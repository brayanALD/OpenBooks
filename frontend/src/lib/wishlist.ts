// Solo para el servidor: favoritos del usuario con sesión.

import { backendFetch } from "@/lib/backend";
import { getSessionToken } from "@/lib/session";
import type { BookSummary } from "@/types/catalog";

export async function getMyFavorites(): Promise<BookSummary[]> {
  const token = await getSessionToken();
  if (!token) return [];
  const response = await backendFetch("/wishlist", { token });
  if (!response.ok) throw new Error(`No se pudieron cargar los favoritos (${response.status})`);
  return ((await response.json()) as { items: BookSummary[] }).items;
}
